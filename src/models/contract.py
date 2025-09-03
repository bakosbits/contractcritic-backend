from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    contract_type = db.Column(db.String(100))
    status = db.Column(db.String(50), default='uploaded')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to analyses
    analyses = db.relationship('ContractAnalysis', backref='contract', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Contract {self.filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'contract_type': self.contract_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'analyses_count': len(self.analyses)
        }

class ContractAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    ai_model_used = db.Column(db.String(50))
    analysis_type = db.Column(db.String(50))
    risk_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    analysis_results = db.Column(db.Text)  # JSON string
    processing_time_ms = db.Column(db.Integer)
    tokens_used = db.Column(db.Integer)
    status = db.Column(db.String(50), default='pending')
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to risk factors
    risk_factors = db.relationship('RiskFactor', backref='analysis', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ContractAnalysis {self.id}>'

    def to_dict(self):
        analysis_data = {}
        if self.analysis_results:
            try:
                analysis_data = json.loads(self.analysis_results)
            except json.JSONDecodeError:
                analysis_data = {}
        
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'ai_model_used': self.ai_model_used,
            'analysis_type': self.analysis_type,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'analysis_results': analysis_data,
            'processing_time_ms': self.processing_time_ms,
            'tokens_used': self.tokens_used,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'risk_factors': [rf.to_dict() for rf in self.risk_factors]
        }

    def set_analysis_results(self, results_dict):
        """Helper method to set analysis results as JSON string"""
        self.analysis_results = json.dumps(results_dict)

    def get_analysis_results(self):
        """Helper method to get analysis results as dictionary"""
        if self.analysis_results:
            try:
                return json.loads(self.analysis_results)
            except json.JSONDecodeError:
                return {}
        return {}

class RiskFactor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('contract_analysis.id'), nullable=False)
    category = db.Column(db.String(100))
    severity = db.Column(db.String(20))  # low, medium, high
    description = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RiskFactor {self.category}>'

    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'category': self.category,
            'severity': self.severity,
            'description': self.description,
            'recommendation': self.recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

