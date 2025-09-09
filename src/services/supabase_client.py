import os
from supabase import create_client, Client
from typing import Dict, Any, List
import uuid

class SupabaseService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url:
            raise ValueError("SUPABASE_URL must be set in environment variables")
        if not self.anon_key:
            raise ValueError("SUPABASE_ANON_KEY must be set in environment variables")
    
    def get_client(self, user_jwt_token: str) -> Client:
        """Create a client using the user's JWT token for all operations"""
        return create_client(self.url, self.anon_key, {
            'global': {
                'headers': {
                    'Authorization': f'Bearer {user_jwt_token}'
                }
            }
        })
    
    # Contract operations
    def get_user_contracts(self, user_jwt: str) -> List[Dict[Any, Any]]:
        """Get all contracts for the authenticated user with analyses count"""
        client = self.get_client(user_jwt)
        
        # Get all contracts for the user (RLS will filter automatically)
        response = client.table("contracts").select("*").execute()
        contracts = response.data
        
        # For each contract, count the analyses
        for contract in contracts:
            analyses_response = client.table("contract_analysis").select("id").eq("contract_id", contract['id']).execute()
            contract['analyses_count'] = len(analyses_response.data)
        
        return contracts
    
    def get_contract_by_id(self, contract_id: str, user_jwt: str) -> Dict[Any, Any] | None:
        """Get a specific contract by ID for the authenticated user"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").select("*").eq("id", contract_id).execute()
        return response.data[0] if response.data else None
    
    def create_contract(self, contract_data: Dict[str, Any], user_jwt: str) -> Dict[Any, Any] | None:
        """Create a new contract"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").insert(contract_data).execute()
        return response.data[0] if response.data else None
    
    def update_contract(self, contract_id: str, updates: Dict[str, Any], user_jwt: str) -> Dict[Any, Any] | None:
        """Update a contract"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").update(updates).eq("id", contract_id).execute()
        return response.data[0] if response.data else None
    
    def delete_contract(self, contract_id: str, user_jwt: str) -> bool:
        """Delete a contract"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").delete().eq("id", contract_id).execute()
        return len(response.data) > 0
    
    # Contract Analysis operations
    def get_contract_analyses(self, contract_id: str, user_jwt: str) -> List[Dict[Any, Any]]:
        """Get all analyses for a contract with risk factors"""
        client = self.get_client(user_jwt)
        response = client.table("contract_analysis").select("*, risk_factors(*)").eq("contract_id", contract_id).execute()
        return response.data
    
    def get_analysis_by_id(self, analysis_id: str, user_jwt: str) -> Dict[Any, Any] | None:
        """Get a specific analysis by ID with risk factors"""
        client = self.get_client(user_jwt)
        response = client.table("contract_analysis").select("*, risk_factors(*)").eq("id", analysis_id).execute()
        return response.data[0] if response.data else None
    
    def create_analysis(self, analysis_data: Dict[str, Any], user_jwt: str) -> Dict[Any, Any] | None:
        """Create a new contract analysis"""
        client = self.get_client(user_jwt)
        response = client.table("contract_analysis").insert(analysis_data).execute()
        return response.data[0] if response.data else None
    
    def update_analysis(self, analysis_id: str, updates: Dict[str, Any], user_jwt: str) -> Dict[Any, Any] | None:
        """Update a contract analysis"""
        client = self.get_client(user_jwt)
        response = client.table("contract_analysis").update(updates).eq("id", analysis_id).execute()
        return response.data[0] if response.data else None
    
    # Risk Factor operations
    def create_risk_factors(self, risk_factors: List[Dict[str, Any]], user_jwt: str) -> List[Dict[Any, Any]]:
        """Create multiple risk factors for an analysis"""
        client = self.get_client(user_jwt)
        response = client.table("risk_factors").insert(risk_factors).execute()
        return response.data
    
    def get_risk_factors_by_analysis(self, analysis_id: str, user_jwt: str) -> List[Dict[Any, Any]]:
        """Get all risk factors for an analysis"""
        client = self.get_client(user_jwt)
        response = client.table("risk_factors").select("*").eq("analysis_id", analysis_id).execute()
        return response.data
    
    # Utility methods
    def generate_uuid(self) -> str:
        """Generate a new UUID string"""
        return str(uuid.uuid4())
    
    def verify_user_owns_contract(self, contract_id: str, user_jwt: str) -> bool:
        """Verify that a user owns a specific contract"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").select("id").eq("id", contract_id).execute()
        return len(response.data) > 0

# Global instance
supabase_service = SupabaseService()
