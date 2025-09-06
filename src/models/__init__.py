"""
Data models for Supabase integration.

This module contains dataclasses that represent the structure of data
stored in Supabase. These are used for type hints and data validation.

Actual database operations are handled by the Supabase client in 
services/supabase_client.py
"""

# Import all models for easy access
from .contract import Contract, ContractAnalysis, RiskFactor
from .user import User

__all__ = [
    'Contract',
    'ContractAnalysis', 
    'RiskFactor',
    'User'
]
