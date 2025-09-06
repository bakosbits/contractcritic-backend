"""
User models for Supabase integration.

Note: These are data classes for type hints and validation only.
Actual user operations are handled by Supabase Auth and the Supabase client 
in services/supabase_client.py
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """User data model for Supabase integration"""
    id: Optional[str] = None  # UUID from auth.users
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from dictionary"""
        return cls(
            id=data.get('id'),
            email=data.get('email'),
            name=data.get('name'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None
        )
