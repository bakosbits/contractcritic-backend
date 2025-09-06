"""
Contract models for Supabase integration.

Note: These are data classes for type hints and validation only.
Actual database operations are handled by the Supabase client in services/supabase_client.py
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json


@dataclass
class Contract:
    """Contract data model for Supabase integration"""
    id: Optional[str] = None  # UUID in Supabase
    user_id: Optional[str] = None  # UUID reference to auth.users
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    contract_type: Optional[str] = None
    status: str = 'uploaded'
    blob_url: Optional[str] = None  # Vercel Blob Storage URL
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    analyses_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'contract_type': self.contract_type,
            'status': self.status,
            'blob_url': self.blob_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'analyses_count': self.analyses_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contract':
        """Create Contract instance from dictionary"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            original_filename=data.get('original_filename'),
            file_size=data.get('file_size'),
            contract_type=data.get('contract_type'),
            status=data.get('status', 'uploaded'),
            blob_url=data.get('blob_url'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
            analyses_count=data.get('analyses_count', 0)
        )


@dataclass
class ContractAnalysis:
    """Contract analysis data model for Supabase integration"""
    id: Optional[str] = None  # UUID in Supabase
    contract_id: Optional[str] = None  # UUID reference
    user_id: Optional[str] = None  # UUID reference to auth.users
    analysis_type: Optional[str] = None
    status: str = 'pending'
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    analysis_results: Optional[Dict[str, Any]] = None  # JSONB in Supabase
    processing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    risk_factors: List['RiskFactor'] = None

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'user_id': self.user_id,
            'analysis_type': self.analysis_type,
            'status': self.status,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'analysis_results': self.analysis_results or {},
            'processing_time_ms': self.processing_time_ms,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'risk_factors': [rf.to_dict() for rf in self.risk_factors] if self.risk_factors else []
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContractAnalysis':
        """Create ContractAnalysis instance from dictionary"""
        return cls(
            id=data.get('id'),
            contract_id=data.get('contract_id'),
            user_id=data.get('user_id'),
            analysis_type=data.get('analysis_type'),
            status=data.get('status', 'pending'),
            risk_score=data.get('risk_score'),
            risk_level=data.get('risk_level'),
            analysis_results=data.get('analysis_results'),
            processing_time_ms=data.get('processing_time_ms'),
            tokens_used=data.get('tokens_used'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None,
            risk_factors=[RiskFactor.from_dict(rf) for rf in data.get('risk_factors', [])]
        )


@dataclass
class RiskFactor:
    """Risk factor data model for Supabase integration"""
    id: Optional[str] = None  # UUID in Supabase
    analysis_id: Optional[str] = None  # UUID reference
    user_id: Optional[str] = None  # UUID reference to auth.users
    category: Optional[str] = None
    severity: Optional[str] = None  # low, medium, high
    title: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'user_id': self.user_id,
            'category': self.category,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'recommendation': self.recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskFactor':
        """Create RiskFactor instance from dictionary"""
        return cls(
            id=data.get('id'),
            analysis_id=data.get('analysis_id'),
            user_id=data.get('user_id'),
            category=data.get('category'),
            severity=data.get('severity'),
            title=data.get('title'),
            description=data.get('description'),
            recommendation=data.get('recommendation'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None
        )
