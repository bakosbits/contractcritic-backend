import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import uuid

class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
    
    # Contract operations
    def get_user_contracts(self, user_id: str) -> List[Dict[Any, Any]]:
        """Get all contracts for a specific user"""
        response = self.client.table("contracts").select("*").eq("user_id", user_id).execute()
        return response.data
    
    def get_contract_by_id(self, contract_id: str, user_id: str) -> Optional[Dict[Any, Any]]:
        """Get a specific contract by ID for a user"""
        response = self.client.table("contracts").select("*").eq("id", contract_id).eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    
    def create_contract(self, contract_data: Dict[str, Any]) -> Optional[Dict[Any, Any]]:
        """Create a new contract"""
        response = self.client.table("contracts").insert(contract_data).execute()
        return response.data[0] if response.data else None
    
    def update_contract(self, contract_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[Any, Any]]:
        """Update a contract"""
        response = self.client.table("contracts").update(updates).eq("id", contract_id).eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    
    def delete_contract(self, contract_id: str, user_id: str) -> bool:
        """Delete a contract"""
        response = self.client.table("contracts").delete().eq("id", contract_id).eq("user_id", user_id).execute()
        return len(response.data) > 0
    
    # Contract Analysis operations
    def get_contract_analyses(self, contract_id: str) -> List[Dict[Any, Any]]:
        """Get all analyses for a contract with risk factors"""
        response = self.client.table("contract_analysis").select("*, risk_factors(*)").eq("contract_id", contract_id).execute()
        return response.data
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[Any, Any]]:
        """Get a specific analysis by ID with risk factors"""
        response = self.client.table("contract_analysis").select("*, risk_factors(*)").eq("id", analysis_id).execute()
        return response.data[0] if response.data else None
    
    def create_analysis(self, analysis_data: Dict[str, Any]) -> Optional[Dict[Any, Any]]:
        """Create a new contract analysis"""
        response = self.client.table("contract_analysis").insert(analysis_data).execute()
        return response.data[0] if response.data else None
    
    def update_analysis(self, analysis_id: str, updates: Dict[str, Any]) -> Optional[Dict[Any, Any]]:
        """Update a contract analysis"""
        response = self.client.table("contract_analysis").update(updates).eq("id", analysis_id).execute()
        return response.data[0] if response.data else None
    
    # Risk Factor operations
    def create_risk_factors(self, risk_factors: List[Dict[str, Any]]) -> List[Dict[Any, Any]]:
        """Create multiple risk factors for an analysis"""
        response = self.client.table("risk_factors").insert(risk_factors).execute()
        return response.data
    
    def get_risk_factors_by_analysis(self, analysis_id: str) -> List[Dict[Any, Any]]:
        """Get all risk factors for an analysis"""
        response = self.client.table("risk_factors").select("*").eq("analysis_id", analysis_id).execute()
        return response.data
    
    # Utility methods
    def generate_uuid(self) -> str:
        """Generate a new UUID string"""
        return str(uuid.uuid4())
    
    def verify_user_owns_contract(self, contract_id: str, user_id: str) -> bool:
        """Verify that a user owns a specific contract"""
        response = self.client.table("contracts").select("id").eq("id", contract_id).eq("user_id", user_id).execute()
        return len(response.data) > 0

# Global instance
supabase_service = SupabaseService()
