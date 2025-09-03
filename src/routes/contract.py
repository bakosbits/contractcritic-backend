import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from src.models.user import db
from src.models.contract import Contract, ContractAnalysis, RiskFactor
from src.services.contract_analyzer import ContractAnalyzer
import logging

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
        
        # Generate secure filename
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        secure_name = str(uuid.uuid4()) + file_extension
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, secure_name)
        file.save(file_path)
        
        # Get user_id from request (in a real app, this would come from authentication)
        user_id = request.form.get('user_id', 1)  # Default to user 1 for demo
        
        # Create contract record
        contract = Contract(
            user_id=user_id,
            filename=secure_name,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.mimetype,
            status='uploaded'
        )
        
        db.session.add(contract)
        db.session.commit()
        
        logger.info(f"Contract uploaded successfully: {contract.id}")
        
        return jsonify({
            'success': True,
            'data': {
                'contract_id': contract.id,
                'filename': original_filename,
                'file_size': file_size,
                'status': 'uploaded'
            },
            'message': 'Contract uploaded successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading contract: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error during file upload'
        }), 500

@contract_bp.route('/contracts', methods=['GET'])
def get_contracts():
    """
    Get list of contracts for a user.
    Query parameters: user_id, page, per_page, status
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id', 1, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # Build query
        query = Contract.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        contracts = query.order_by(Contract.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'contracts': [contract.to_dict() for contract in contracts.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': contracts.total,
                    'pages': contracts.pages,
                    'has_next': contracts.has_next,
                    'has_prev': contracts.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contracts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/<int:contract_id>', methods=['GET'])
def get_contract(contract_id):
    """
    Get details of a specific contract.
    """
    try:
        contract = Contract.query.get_or_404(contract_id)
        
        return jsonify({
            'success': True,
            'data': contract.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contract {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Contract not found'
        }), 404

@contract_bp.route('/contracts/<int:contract_id>/analyze', methods=['POST'])
def analyze_contract(contract_id):
    """
    Analyze a contract using AI.
    Request body: {"analysis_type": "comprehensive" | "quick_summary"}
    """
    try:
        # Get contract
        contract = Contract.query.get_or_404(contract_id)
        
        # Get analysis type from request
        data = request.get_json() or {}
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        if analysis_type not in ['comprehensive', 'quick_summary']:
            return jsonify({
                'success': False,
                'error': 'Invalid analysis type. Must be "comprehensive" or "quick_summary"'
            }), 400
        
        # Initialize analyzer
        analyzer = ContractAnalyzer()
        
        # Extract text from file
        logger.info(f"Extracting text from contract {contract_id}")
        text_data = analyzer.extract_text_from_file(contract.file_path)
        
        # Update contract with extracted metadata
        contract.status = 'processing'
        db.session.commit()
        
        # Perform analysis
        logger.info(f"Analyzing contract {contract_id} with {analysis_type} analysis")
        analysis_result = analyzer.analyze_contract(
            text_data['cleaned_text'], 
            analysis_type
        )
        
        # Create analysis record
        analysis = ContractAnalysis(
            contract_id=contract_id,
            ai_model_used=analysis_result['ai_model_used'],
            analysis_type=analysis_type,
            risk_score=analysis_result['risk_score'],
            risk_level=analysis_result['risk_level'],
            processing_time_ms=analysis_result['processing_time_ms'],
            tokens_used=analysis_result['tokens_used'],
            status='completed'
        )
        
        # Set analysis results
        analysis.set_analysis_results(analysis_result['analysis_results'])
        
        db.session.add(analysis)
        db.session.flush()  # Get the analysis ID
        
        # Extract and save risk factors
        risk_factors = analyzer.extract_risk_factors(analysis_result['analysis_results'])
        
        for factor_data in risk_factors:
            risk_factor = RiskFactor(
                analysis_id=analysis.id,
                category=factor_data['category'],
                severity=factor_data['severity'],
                description=factor_data['description'],
                recommendation=factor_data['recommendation']
            )
            db.session.add(risk_factor)
        
        # Update contract status
        contract.status = 'analyzed'
        contract.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Contract analysis completed for contract {contract_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'analysis_id': analysis.id,
                'contract_id': contract_id,
                'risk_score': analysis.risk_score,
                'risk_level': analysis.risk_level,
                'status': 'completed',
                'processing_time_ms': analysis.processing_time_ms
            },
            'message': 'Contract analysis completed successfully'
        }), 200
        
    except FileNotFoundError:
        logger.error(f"Contract file not found for contract {contract_id}")
        return jsonify({
            'success': False,
            'error': 'Contract file not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Error analyzing contract {contract_id}: {str(e)}")
        
        # Update contract status to error
        try:
            contract = Contract.query.get(contract_id)
            if contract:
                contract.status = 'error'
                db.session.commit()
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Internal server error during analysis'
        }), 500

@contract_bp.route('/contracts/<int:contract_id>/analysis', methods=['GET'])
def get_contract_analysis(contract_id):
    """
    Get the latest analysis results for a contract.
    """
    try:
        # Get the latest analysis for this contract
        analysis = ContractAnalysis.query.filter_by(
            contract_id=contract_id
        ).order_by(ContractAnalysis.created_at.desc()).first()
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'No analysis found for this contract'
            }), 404
        
        return jsonify({
            'success': True,
            'data': analysis.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching analysis for contract {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/contracts/<int:contract_id>/analysis/<int:analysis_id>', methods=['GET'])
def get_specific_analysis(contract_id, analysis_id):
    """
    Get a specific analysis by ID.
    """
    try:
        analysis = ContractAnalysis.query.filter_by(
            id=analysis_id,
            contract_id=contract_id
        ).first_or_404()
        
        return jsonify({
            'success': True,
            'data': analysis.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Analysis not found'
        }), 404

@contract_bp.route('/contracts/<int:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    """
    Delete a contract and its associated files and analyses.
    """
    try:
        contract = Contract.query.get_or_404(contract_id)
        
        # Delete the physical file
        try:
            if os.path.exists(contract.file_path):
                os.remove(contract.file_path)
        except Exception as e:
            logger.warning(f"Could not delete file {contract.file_path}: {str(e)}")
        
        # Delete from database (cascades to analyses and risk factors)
        db.session.delete(contract)
        db.session.commit()
        
        logger.info(f"Contract {contract_id} deleted successfully")
        
        return jsonify({
            'success': True,
            'message': 'Contract deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting contract {contract_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@contract_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get dashboard statistics for a user.
    """
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        # Get contract counts
        total_contracts = Contract.query.filter_by(user_id=user_id).count()
        
        # Get contracts by status
        uploaded = Contract.query.filter_by(user_id=user_id, status='uploaded').count()
        processing = Contract.query.filter_by(user_id=user_id, status='processing').count()
        analyzed = Contract.query.filter_by(user_id=user_id, status='analyzed').count()
        error = Contract.query.filter_by(user_id=user_id, status='error').count()
        
        # Get risk level distribution
        high_risk = db.session.query(ContractAnalysis).join(Contract).filter(
            Contract.user_id == user_id,
            ContractAnalysis.risk_level == 'High'
        ).count()
        
        medium_risk = db.session.query(ContractAnalysis).join(Contract).filter(
            Contract.user_id == user_id,
            ContractAnalysis.risk_level == 'Medium'
        ).count()
        
        low_risk = db.session.query(ContractAnalysis).join(Contract).filter(
            Contract.user_id == user_id,
            ContractAnalysis.risk_level == 'Low'
        ).count()
        
        # Get recent activity (last 5 contracts)
        recent_contracts = Contract.query.filter_by(
            user_id=user_id
        ).order_by(Contract.created_at.desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_contracts': total_contracts,
                'status_breakdown': {
                    'uploaded': uploaded,
                    'processing': processing,
                    'analyzed': analyzed,
                    'error': error
                },
                'risk_distribution': {
                    'high_risk': high_risk,
                    'medium_risk': medium_risk,
                    'low_risk': low_risk
                },
                'recent_activity': [contract.to_dict() for contract in recent_contracts]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

