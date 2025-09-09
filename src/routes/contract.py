import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from src.middleware.auth import require_auth, get_current_user
from src.services.supabase_client import supabase_service
from src.services.blob_storage import blob_service
from src.services.contract_analyzer import ContractAnalyzer
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

contract_bp = Blueprint('contract', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Get file size in bytes"""
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    return size

@contract_bp.route('/contracts/upload', methods=['POST'])
@require_auth
def upload_contract():
    """
    Upload a contract file for analysis.
    Expects multipart/form-data with 'file' field.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Check file size
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Read file content
        file_content = file.read()
        file.seek(0)  # Reset for potential re-use
        
        # Upload to Vercel Blob Storage
        blob_result = blob_service.upload_file(
            file_content,
            file.filename,
            file.mimetype
        )
        
        if not blob_result:
            return jsonify({
                'success': False,
                'error': 'Failed to upload file to storage'
            }), 500
        
        # Create contract record in Supabase with audit logging
        contract_data = {
            'user_id': g.user_id,
            'filename': os.path.basename(blob_result['pathname']) if blob_result.get('pathname') else file.filename,
            'original_filename': file.filename,
            'file_url': blob_result['url'],
            'file_size': file_size,
            'mime_type': file.mimetype,
            'status': 'uploaded'
        }
        
        # Extract JWT token for audit logging
        token = request.headers.get('Authorization').split(' ')[1]
        contract = supabase_service.create_contract(contract_data, user_jwt=token)
        
        if not contract:
            # If contract creation failed, try to clean up the uploaded file
            try:
                blob_service.delete_file(blob_result['url'])
            except:
                pass
            return jsonify({
                'success': False,
                'error': 'Failed to create contract record'
            }), 500
        
        logger.info(f"Contract uploaded successfully: {contract['id']}")
        
        return jsonify({
            'success': True,
            'data': {
                'contract_id': contract['id'],
                'filename': file.filename,
                'file_size': file_size,
                'status': 'uploaded'
            },
            'message': 'Contract uploaded successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading contract: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during file upload'
        }), 500

@contract_bp.route('/contracts', methods=['GET'])
@require_auth
def get_contracts():
    """
    Get list of contracts for the authenticated user.
    Query parameters: page, per_page, status
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 100, type=int), 100)  # Cap at 100
        status = request.args.get('status')
        
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Get contracts for the authenticated user
        contracts = supabase_service.get_user_contracts(user_jwt=token)
        
        # Filter by status if provided
        if status:
            contracts = [c for c in contracts if c.get('status') == status]
        
        # Sort by created_at descending
        contracts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Simple pagination
        total = len(contracts)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_contracts = contracts[start:end]
        
        return jsonify({
            'success': True,
            'data': {
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
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contracts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/<contract_id>', methods=['GET'])
@require_auth
def get_contract(contract_id):
    """
    Get details of a specific contract.
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        contract = supabase_service.get_contract_by_id(contract_id, user_jwt=token)
        
        if not contract:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': contract
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contract {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/<contract_id>/analyze', methods=['POST'])
@require_auth
def analyze_contract(contract_id):
    """
    Analyze a contract using AI.
    Request body: {"analysis_type": "small_business" | "individual"}
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Verify user owns the contract
        contract = supabase_service.get_contract_by_id(contract_id, user_jwt=token)
        if not contract:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        # Get analysis type from request
        data = request.get_json() or {}
        analysis_type = data.get('analysis_type', 'small_business')
        
        if analysis_type not in ['small_business', 'individual']:
            return jsonify({
                'success': False,
                'error': 'Invalid analysis type. Must be "small_business" or "individual"'
            }), 400
        
        # Extract JWT token for audit logging
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Update contract status to processing
        supabase_service.update_contract(contract_id, {'status': 'processing'}, user_jwt=token)
        
        # Download file from Vercel Blob Storage for analysis
        import requests
        file_response = requests.get(contract['file_url'])
        if file_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': 'Failed to download contract file for analysis'
            }), 500
        
        # Create temporary file for analysis
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(contract['original_filename'])[1]) as temp_file:
            temp_file.write(file_response.content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize analyzer
            analyzer = ContractAnalyzer()
            
            # Extract text from file
            logger.info(f"Extracting text from contract {contract_id}")
            text_data = analyzer.extract_text_from_file(temp_file_path)
            
            # Perform analysis
            logger.info(f"Analyzing contract {contract_id} with {analysis_type} analysis")
            analysis_result = analyzer.analyze_contract(
                text_data['cleaned_text'], 
                analysis_type
            )
            
            # Create analysis record
            analysis_data = {
                'contract_id': contract_id,
                'ai_model_used': analysis_result['ai_model_used'],
                'analysis_type': analysis_type,
                'risk_score': analysis_result['risk_score'],
                'risk_level': analysis_result['risk_level'] if isinstance(analysis_result['risk_level'], str) else str(analysis_result['risk_level']),
                'analysis_results': analysis_result['analysis_results'],  # Supabase handles JSON automatically
                'processing_time_ms': analysis_result['processing_time_ms'],
                'tokens_used': analysis_result['tokens_used'],
                'status': 'completed'
            }

            analysis = supabase_service.create_analysis(analysis_data, user_jwt=token)
            
            if not analysis:
                raise Exception("Failed to create analysis record")
            
            # Extract and save risk factors
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
                supabase_service.create_risk_factors(risk_factor_records, user_jwt=token)
            
            # Extract contract type from analysis results and update contract
            contract_type = analysis_result['analysis_results'].get('contract_type', 'Unknown')
            
            # Update contract status and type
            supabase_service.update_contract(contract_id, {
                'status': 'analyzed',
                'contract_type': contract_type
            }, user_jwt=token)

            logger.info(f"Contract analysis completed for contract {contract_id}, type: {contract_type}")
            
            return jsonify({
                'success': True,
                'data': {
                    'analysis_id': analysis['id'],
                    'contract_id': contract_id,
                    'risk_score': analysis['risk_score'],
                    'risk_level': analysis['risk_level'],
                    'status': 'completed',
                    'processing_time_ms': analysis['processing_time_ms']
                },
                'message': 'Contract analysis completed successfully'
            }), 200
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error analyzing contract {contract_id}: {str(e)}")
        
        # Update contract status to error
        try:
            token = request.headers.get('Authorization').split(' ')[1]
            supabase_service.update_contract(contract_id, {'status': 'error'}, user_jwt=token)
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Internal server error during analysis'
        }), 500

@contract_bp.route('/contracts/<contract_id>/analysis', methods=['GET'])
@require_auth
def get_contract_analysis(contract_id):
    """
    Get the latest analysis results for a contract.
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Verify user owns the contract
        if not supabase_service.verify_user_owns_contract(contract_id, user_jwt=token):
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        # Get analyses for this contract
        analyses = supabase_service.get_contract_analyses(contract_id, user_jwt=token)
        
        if not analyses:
            return jsonify({
                'success': False,
                'error': 'No analysis found for this contract'
            }), 404
        
        # Return the most recent analysis (first in the list due to ordering)
        latest_analysis = analyses[0]
        
        return jsonify({
            'success': True,
            'data': latest_analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching analysis for contract {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/<contract_id>/analysis/<analysis_id>', methods=['GET'])
@require_auth
def get_specific_analysis(contract_id, analysis_id):
    """
    Get a specific analysis by ID.
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Verify user owns the contract
        if not supabase_service.verify_user_owns_contract(contract_id, user_jwt=token):
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        analysis = supabase_service.get_analysis_by_id(analysis_id, user_jwt=token)
        
        if not analysis or analysis['contract_id'] != contract_id:
            return jsonify({
                'success': False,
                'error': 'Analysis not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/<contract_id>', methods=['DELETE'])
@require_auth
def delete_contract(contract_id):
    """
    Delete a contract and its associated files and analyses.
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Get contract to verify ownership and get file URL
        contract = supabase_service.get_contract_by_id(contract_id, user_jwt=token)
        if not contract:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        # Delete the file from Vercel Blob Storage
        try:
            blob_service.delete_file(contract['file_url'])
        except Exception as e:
            logger.warning(f"Could not delete file {contract['file_url']}: {str(e)}")
        
        # Delete from Supabase (cascades to analyses and risk factors due to foreign key constraints)
        success = supabase_service.delete_contract(contract_id, user_jwt=token)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to delete contract'
            }), 500
        
        logger.info(f"Contract {contract_id} deleted successfully")
        
        return jsonify({
            'success': True,
            'message': 'Contract deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting contract {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/batch-update-types', methods=['POST'])
@require_auth
def batch_update_contract_types():
    """
    Batch update contract types for existing analyzed contracts that are missing contract_type.
    This is useful for retroactively updating contracts analyzed before the contract_type fix.
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Get all analyzed contracts for the user that don't have a contract_type
        contracts = supabase_service.get_user_contracts(user_jwt=token)
        
        # Filter for analyzed contracts without contract_type
        contracts_to_update = [
            c for c in contracts 
            if c.get('status') == 'analyzed' and not c.get('contract_type')
        ]
        
        if not contracts_to_update:
            return jsonify({
                'success': True,
                'data': {
                    'updated_count': 0,
                    'message': 'No contracts need contract type updates'
                }
            }), 200
        
        updated_count = 0
        errors = []
        
        for contract in contracts_to_update:
            try:
                # Get the latest analysis for this contract
                analyses = supabase_service.get_contract_analyses(contract['id'], user_jwt=token)
                
                if not analyses:
                    errors.append(f"No analysis found for contract {contract['id']}")
                    continue
                
                # Get contract type from the latest analysis
                latest_analysis = analyses[0]
                analysis_results = latest_analysis.get('analysis_results', {})
                contract_type = analysis_results.get('contract_type', 'Unknown')
                
                # Update the contract with the extracted type
                success = supabase_service.update_contract(contract['id'], {
                    'contract_type': contract_type
                }, user_jwt=token)
                
                if success:
                    updated_count += 1
                    logger.info(f"Updated contract {contract['id']} with type: {contract_type}")
                else:
                    errors.append(f"Failed to update contract {contract['id']}")
                    
            except Exception as e:
                error_msg = f"Error updating contract {contract['id']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        response_data = {
            'updated_count': updated_count,
            'total_candidates': len(contracts_to_update),
            'message': f'Successfully updated {updated_count} out of {len(contracts_to_update)} contracts'
        }
        
        if errors:
            response_data['errors'] = errors
            response_data['message'] += f' ({len(errors)} errors occurred)'
        
        logger.info(f"Batch contract type update completed: {updated_count}/{len(contracts_to_update)} updated")
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch contract type update: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during batch update'
        }), 500

@contract_bp.route('/dashboard/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """
    Get dashboard statistics for the authenticated user.
    """
    try:
        # Extract JWT token
        token = request.headers.get('Authorization').split(' ')[1]
        
        # Get all contracts for the user
        contracts = supabase_service.get_user_contracts(user_jwt=token)
        
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
            analyses = supabase_service.get_contract_analyses(contract['id'], user_jwt=token)
            all_analyses.extend(analyses)
        
        # Calculate risk distribution
        risk_counts = {'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
        for analysis in all_analyses:
            risk_level = analysis.get('risk_level', '').lower()
            if risk_level == 'high':
                risk_counts['high_risk'] += 1
            elif 'medium' in risk_level:  # Covers Medium, Medium-High, Medium-Low
                risk_counts['medium_risk'] += 1
            elif risk_level == 'low':
                risk_counts['low_risk'] += 1
        
        # Get recent activity (last 5 contracts)
        recent_contracts = sorted(contracts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        return jsonify({
            'success': True,
            'data': {
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
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
