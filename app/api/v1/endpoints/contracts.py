import os
import tempfile
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user, get_jwt_token
from app.core.config import settings
from app.core.exceptions import FileUploadError, NotFoundError, ValidationError
from app.models.contract import (
    ContractAnalysisRequest, 
    ContractUploadResponse, 
    ContractListResponse,
    ContractAnalysisResponse,
    DashboardStatsResponse,
    SuccessResponse
)
from app.services.supabase_client import supabase_service
from app.services.blob_storage import blob_service
from app.services.contract_analyzer import ContractAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()

# File validation
def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if not file.filename:
        raise FileUploadError("No file selected")
    
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension.lstrip('.') not in settings.allowed_extensions:
        raise FileUploadError(
            f"File type not allowed. Supported formats: {', '.join(settings.allowed_extensions)}"
        )
    
    # Check file size (FastAPI handles this automatically, but we can add custom logic)
    if file.size and file.size > settings.max_file_size:
        raise FileUploadError(
            f"File too large. Maximum size: {settings.max_file_size // (1024*1024)}MB"
        )


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    jwt_token: str = Depends(get_jwt_token)
):
    """Upload a contract file for analysis."""
    try:
        # Validate file
        validate_file(file)
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Vercel Blob Storage
        blob_result = blob_service.upload_file_sync(
            file_content,
            file.filename,
            file.content_type,
            user_id=current_user['user_id']
        )
        
        if not blob_result:
            raise FileUploadError("Failed to upload file to storage")
        
        # Create contract record in Supabase
        contract_data = {
            'user_id': current_user['user_id'],
            'filename': os.path.basename(blob_result['pathname']) if blob_result.get('pathname') else file.filename,
            'original_filename': file.filename,
            'file_url': blob_result['url'],
            'file_size': len(file_content),
            'mime_type': file.content_type,
            'status': 'uploaded'
        }
        
        contract = supabase_service.create_contract(contract_data, jwt_token)
        
        if not contract:
            # Clean up uploaded file if contract creation failed
            try:
                blob_service.delete_file_sync(blob_result['url'])
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create contract record"
            )
        
        logger.info(f"Contract uploaded successfully: {contract['id']}")
        
        return ContractUploadResponse(
            success=True,
            data={
                'contract_id': contract['id'],
                'filename': file.filename,
                'file_size': len(file_content),
                'status': 'uploaded'
            },
            message="Contract uploaded successfully"
        )
        
    except FileUploadError:
        raise
    except Exception as e:
        logger.error(f"Error uploading contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file upload"
        )


@router.get("", response_model=ContractListResponse)
async def get_contracts(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    jwt_token: str = Depends(get_jwt_token)
):
    """Get list of contracts for the authenticated user."""
    try:
        # Get contracts for the authenticated user
        contracts = supabase_service.get_user_contracts(jwt_token)
        
        # Filter by status if provided
        if status_filter:
            contracts = [c for c in contracts if c.get('status') == status_filter]
        
        # Sort by created_at descending
        contracts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Simple pagination
        total = len(contracts)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_contracts = contracts[start:end]
        
        return ContractListResponse(
            success=True,
            data={
                'contracts': paginated_contracts,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': end < total,
                    'has_prev': page > 1
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching contracts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard(
    jwt_token: str = Depends(get_jwt_token)
):
    """Get optimized dashboard statistics for the authenticated user."""
    try:
        # Get dashboard statistics with optimized queries
        dashboard_data = supabase_service.get_dashboard_stats(jwt_token)
        
        return DashboardStatsResponse(
            success=True,
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/list", response_model=ContractListResponse)
async def get_contracts_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    jwt_token: str = Depends(get_jwt_token)
):
    """Get optimized list of contracts for the authenticated user with minimal fields."""
    try:
        # Get contracts list with only required fields
        contracts = supabase_service.get_contracts_list(jwt_token, status_filter)
        
        # Simple pagination
        total = len(contracts)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_contracts = contracts[start:end]
        
        return ContractListResponse(
            success=True,
            data={
                'contracts': paginated_contracts,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': end < total,
                    'has_prev': page > 1
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching contracts list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string into ISO 8601 format, handling 'Not specified'."""
    if not date_str or date_str.lower() == 'not specified':
        return None
    try:
        # Attempt to parse the date string
        return datetime.strptime(date_str, '%B %d, %Y').isoformat()
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return None


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    jwt_token: str = Depends(get_jwt_token)
):
    """Get details of a specific contract."""
    try:
        contract = supabase_service.get_contract_by_id(contract_id, jwt_token)
        
        if not contract:
            raise NotFoundError("Contract not found")
        
        return {
            "success": True,
            "data": contract
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    except Exception as e:
        logger.error(f"Error fetching contract {contract_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def analyze_contract_background(
    contract_id: str,
    analysis_type: str,
    jwt_token: str
):
    """Background task for contract analysis."""
    logger.info(f"=== STARTING BACKGROUND TASK for contract {contract_id} ===")
    
    try:
        # Step 1: Get contract
        logger.info(f"Step 1: Getting contract {contract_id}")
        contract = supabase_service.get_contract_by_id(contract_id, jwt_token)
        if not contract:
            logger.error(f"Contract {contract_id} not found for analysis")
            return
        logger.info(f"Step 1: Contract found - {contract.get('filename', 'unknown')}")
        
        # Step 2: Update contract status to processing
        logger.info(f"Step 2: Updating contract status to processing")
        supabase_service.update_contract(contract_id, {'status': 'processing'}, jwt_token)
        logger.info(f"Step 2: Contract status updated to processing")
        
        # Step 3: Download file from Vercel Blob Storage for analysis
        logger.info(f"Step 3: Downloading file from {contract['file_url']}")
        import httpx
        async with httpx.AsyncClient() as client:
            file_response = await client.get(contract['file_url'])
            if file_response.status_code != 200:
                logger.error(f"Failed to download contract file for analysis: {contract_id}, status: {file_response.status_code}")
                supabase_service.update_contract(contract_id, {'status': 'error'}, jwt_token)
                return
        logger.info(f"Step 3: File downloaded successfully, size: {len(file_response.content)} bytes")
        
        # Step 4: Create temporary file for analysis
        logger.info(f"Step 4: Creating temporary file for analysis")
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(contract['original_filename'])[1]) as temp_file:
            temp_file.write(file_response.content)
            temp_file_path = temp_file.name
        logger.info(f"Step 4: Temporary file created at {temp_file_path}")
        
        try:
            # Step 5: Initialize analyzer
            logger.info(f"Step 5: Initializing ContractAnalyzer")
            analyzer = ContractAnalyzer()
            logger.info(f"Step 5: ContractAnalyzer initialized successfully")
            
            # Step 6: Extract text from file
            logger.info(f"Step 6: Extracting text from contract {contract_id}")
            text_data = analyzer.extract_text_from_file(temp_file_path)
            logger.info(f"Step 6: Text extracted - {text_data.get('word_count', 0)} words, {text_data.get('char_count', 0)} characters")
            
            # Step 7: Perform analysis
            logger.info(f"Step 7: Starting AI analysis for contract {contract_id} with {analysis_type} analysis")
            analysis_result = analyzer.analyze_contract(
                text_data['cleaned_text'], 
                analysis_type
            )
            logger.info(f"Step 7: AI analysis completed successfully")
            
            # Step 8: Create analysis record
            logger.info(f"Step 8: Creating analysis record in database")
            analysis_data = {
                'contract_id': contract_id,
                'ai_model_used': analysis_result['ai_model_used'],
                'analysis_type': analysis_type,
                'risk_score': analysis_result['risk_score'],
                'risk_level': analysis_result['risk_level'] if isinstance(analysis_result['risk_level'], str) else str(analysis_result['risk_level']),
                'analysis_results': analysis_result['analysis_results'],
                'processing_time_ms': analysis_result['processing_time_ms'],
                'tokens_used': analysis_result['tokens_used'],
                'status': 'completed'
            }

            analysis = supabase_service.create_analysis(analysis_data, jwt_token)
            
            if not analysis:
                raise Exception("Failed to create analysis record")
            logger.info(f"Step 8: Analysis record created with ID: {analysis['id']}")
            
            # Step 9: Extract and save risk factors
            logger.info(f"Step 9: Extracting and saving risk factors")
            risk_factors = analyzer.extract_risk_factors(analysis_result['analysis_results'])
            
            risk_factor_records = []
            for factor_data in risk_factors:
                risk_factor_records.append({
                    'analysis_id': analysis['id'],
                    'category': factor_data['category'],
                    'severity': factor_data['severity'],
                    'description': factor_data['description'],
                    'recommendation': factor_data['recommendation']
                })
            
            if risk_factor_records:
                supabase_service.create_risk_factors(risk_factor_records, jwt_token)
                logger.info(f"Step 9: {len(risk_factor_records)} risk factors saved")
            else:
                logger.info(f"Step 9: No risk factors to save")
            
            # Step 10: Extract contract type and update contract
            contract_type = analysis_result['analysis_results'].get('contract_type', 'Unknown')
            logger.info(f"Step 10: Updating contract status to 'analyzed', type: {contract_type}")
            
            # Update contract status and type with detailed error handling
            try:
                logger.info(f"Step 10a: Preparing contract update data")
                update_data = {
                    'status': 'analyzed',
                    'contract_type': contract_type,
                }

                # Extract and parse dates
                dates = analysis_result['analysis_results'].get('dates', {})
                if dates:
                    update_data['execution_date'] = parse_date(dates.get('execution_date'))
                    update_data['effective_date'] = parse_date(dates.get('effective_date'))
                    update_data['expiration_date'] = parse_date(dates.get('expiration_date'))
                    update_data['termination_date'] = parse_date(dates.get('termination_date'))

                # Filter out None values from update_data
                update_data = {k: v for k, v in update_data.items() if v is not None}

                logger.info(f"Step 10b: Update data prepared: {update_data}")
                
                logger.info(f"Step 10c: Calling supabase_service.update_contract")
                update_result = supabase_service.update_contract(contract_id, update_data, jwt_token)
                logger.info(f"Step 10d: Update result: {update_result}")
                
                if update_result:
                    logger.info(f"Step 10e: Contract status successfully updated to 'analyzed'")
                else:
                    logger.error(f"Step 10e: Contract update returned False/None")
                    raise Exception("Contract update returned False/None")
                    
            except Exception as update_error:
                logger.error(f"Step 10 ERROR: Failed to update contract status")
                logger.error(f"Step 10 ERROR type: {type(update_error).__name__}")
                logger.error(f"Step 10 ERROR message: {str(update_error)}")
                import traceback
                logger.error(f"Step 10 ERROR traceback: {traceback.format_exc()}")
                raise update_error

            logger.info(f"=== CONTRACT ANALYSIS COMPLETED SUCCESSFULLY for {contract_id} ===")
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"=== ERROR in contract analysis for {contract_id} ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Update contract status to error
        try:
            supabase_service.update_contract(contract_id, {'status': 'error'}, jwt_token)
            logger.info(f"Contract {contract_id} status updated to 'error'")
        except Exception as update_error:
            logger.error(f"Failed to update contract status to error: {str(update_error)}")


@router.post("/{contract_id}/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    contract_id: str,
    request: ContractAnalysisRequest,
    jwt_token: str = Depends(get_jwt_token)
):
    """Analyze a contract using AI - synchronous analysis."""
    try:
        # Verify user owns the contract
        contract = supabase_service.get_contract_by_id(contract_id, jwt_token)
        if not contract:
            raise NotFoundError("Contract not found")
        
        # Validate analysis type
        if request.analysis_type not in ['small_business', 'individual']:
            raise ValidationError('Invalid analysis type. Must be "small_business" or "individual"')
        
        # Run analysis synchronously
        await analyze_contract_background(
            contract_id,
            request.analysis_type,
            jwt_token
        )
        
        # Get the completed analysis
        analyses = supabase_service.get_contract_analyses(contract_id, jwt_token)
        latest_analysis = analyses[0] if analyses else None
        
        if not latest_analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Analysis completed but could not retrieve results"
            )
        
        return ContractAnalysisResponse(
            success=True,
            data={
                'contract_id': contract_id,
                'analysis_id': latest_analysis['id'],
                'status': 'completed',
                'risk_score': latest_analysis['risk_score'],
                'risk_level': latest_analysis['risk_level'],
                'processing_time_ms': latest_analysis['processing_time_ms']
            },
            message="Contract analysis completed successfully"
        )
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error analyzing contract {contract_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during analysis"
        )


@router.get("/{contract_id}/analysis")
async def get_contract_analysis(
    contract_id: str,
    jwt_token: str = Depends(get_jwt_token)
):
    """Get the latest analysis results for a contract."""
    try:
        # Verify user owns the contract
        if not supabase_service.verify_user_owns_contract(contract_id, jwt_token):
            raise NotFoundError("Contract not found")
        
        # Get analyses for this contract
        analyses = supabase_service.get_contract_analyses(contract_id, jwt_token)
        
        if not analyses:
            raise NotFoundError("No analysis found for this contract")
        
        # Return the most recent analysis
        latest_analysis = analyses[0]
        
        return {
            "success": True,
            "data": latest_analysis
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    except Exception as e:
        logger.error(f"Error fetching analysis for contract {contract_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{contract_id}/analyses/history")
async def get_contract_analyses_history(
    contract_id: str,
    jwt_token: str = Depends(get_jwt_token)
):
    """Get older analyses for a contract (excluding the latest one)."""
    try:
        # Verify user owns the contract
        if not supabase_service.verify_user_owns_contract(contract_id, jwt_token):
            raise NotFoundError("Contract not found")
        
        # Get all analyses for this contract
        all_analyses = supabase_service.get_contract_analyses(contract_id, jwt_token)
        
        if len(all_analyses) <= 1:
            # Return empty list if there's only one or no analyses
            return {
                "success": True,
                "data": []
            }
        
        # Return all analyses except the first one (latest), with only essential fields
        older_analyses = []
        for analysis in all_analyses[1:]:  # Skip the first (latest) analysis
            older_analyses.append({
                "id": analysis["id"],
                "created_at": analysis["created_at"],
                "risk_level": analysis["risk_level"],
                "risk_score": analysis["risk_score"],
                "analysis_type": analysis["analysis_type"]
            })
        
        return {
            "success": True,
            "data": older_analyses
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    except Exception as e:
        logger.error(f"Error fetching analyses history for contract {contract_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{contract_id}/analyses/{analysis_id}")
async def get_specific_analysis(
    contract_id: str,
    analysis_id: str,
    jwt_token: str = Depends(get_jwt_token)
):
    """Get a specific analysis by ID for a contract."""
    try:
        # Verify user owns the contract
        if not supabase_service.verify_user_owns_contract(contract_id, jwt_token):
            raise NotFoundError("Contract not found")
        
        # Get the specific analysis
        analysis = supabase_service.get_analysis_by_id(analysis_id, jwt_token)
        
        if not analysis:
            raise NotFoundError("Analysis not found")
        
        # Verify the analysis belongs to the specified contract
        if analysis.get("contract_id") != contract_id:
            raise NotFoundError("Analysis not found for this contract")
        
        return {
            "success": True,
            "data": analysis
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id} for contract {contract_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{contract_id}", response_model=SuccessResponse)
async def delete_contract(
    contract_id: str,
    jwt_token: str = Depends(get_jwt_token)
):
    """Delete a contract and its associated files and analyses."""
    try:
        # Get contract to verify ownership and get file URL
        contract = supabase_service.get_contract_by_id(contract_id, jwt_token)
        if not contract:
            raise NotFoundError("Contract not found")
        
        # Delete the file from Vercel Blob Storage
        if contract.get('file_url'):
            try:
                blob_service.delete_file_sync(contract['file_url'])
            except Exception:
                pass  # Continue with database deletion even if file deletion fails
        
        # Delete from Supabase (cascades to analyses and risk factors)
        success = supabase_service.delete_contract(contract_id, jwt_token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete contract"
            )
        
        logger.info(f"Contract {contract_id} deleted successfully")
        
        return SuccessResponse(
            success=True,
            message="Contract deleted successfully"
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    except Exception as e:
        logger.error(f"Error deleting contract {contract_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    jwt_token: str = Depends(get_jwt_token)
):
    """Get dashboard statistics for the authenticated user. (DEPRECATED - use /dashboard)"""
    try:
        # Get all contracts for the user
        contracts = supabase_service.get_user_contracts(jwt_token)
        
        # Calculate statistics
        total_contracts = len(contracts)
        
        # Get contracts by status
        status_counts = {}
        for contract in contracts:
            status = contract.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Get all analyses for user's contracts
        all_analyses = []
        for contract in contracts:
            analyses = supabase_service.get_contract_analyses(contract['id'], jwt_token)
            all_analyses.extend(analyses)
        
        # Calculate risk distribution
        risk_counts = {'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
        for analysis in all_analyses:
            risk_level = analysis.get('risk_level', '').lower()
            if risk_level == 'high':
                risk_counts['high_risk'] += 1
            elif 'medium' in risk_level:
                risk_counts['medium_risk'] += 1
            elif risk_level == 'low':
                risk_counts['low_risk'] += 1
        
        # Get recent activity (last 5 contracts)
        recent_contracts = sorted(contracts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        return DashboardStatsResponse(
            success=True,
            data={
                'total_contracts': total_contracts,
                'status_breakdown': {
                    'uploaded': status_counts.get('uploaded', 0),
                    'processing': status_counts.get('processing', 0),
                    'analyzed': status_counts.get('analyzed', 0),
                    'error': status_counts.get('error', 0)
                },
                'risk_distribution': risk_counts,
                'recent_activity': recent_contracts
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
