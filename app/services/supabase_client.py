import os
import logging
from supabase import create_client, Client
from typing import Dict, Any, List
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    def __init__(self):
        self.url = settings.supabase_url
        self.anon_key = settings.supabase_anon_key
        
        logger.info(f"Initializing SupabaseService with URL: {self.url[:50]}..." if self.url else "No URL")
        logger.info(f"Anon key present: {bool(self.anon_key)}")
        
        if not self.url:
            logger.error("SUPABASE_URL is not set in environment variables")
            raise ValueError("SUPABASE_URL must be set in environment variables")
        if not self.anon_key:
            logger.error("SUPABASE_ANON_KEY is not set in environment variables")
            raise ValueError("SUPABASE_ANON_KEY must be set in environment variables")
        
        logger.info("SupabaseService initialized successfully")
    
    def get_client(self, user_jwt_token: str) -> Client:
        """Create a client using the user's JWT token for all operations"""
        logger.debug(f"Creating Supabase client with JWT token (length: {len(user_jwt_token) if user_jwt_token else 0})")
        try:
            # Create client with the user's JWT token as the access token
            # This ensures all requests are authenticated with the user's token
            client = create_client(self.url, self.anon_key)
            
            if user_jwt_token:
                # Set the JWT token directly in the auth module and headers
                # This ensures RLS policies can properly evaluate the user context
                try:
                    # Set the access token directly on the auth module
                    client.auth._access_token = user_jwt_token
                    # Also set the Authorization header for REST API calls
                    client.options.headers['Authorization'] = f'Bearer {user_jwt_token}'
                    # Set the user context for RLS evaluation
                    client.auth._user = None  # Will be populated on first API call
                    logger.debug("JWT token set successfully for RLS evaluation")
                except Exception as auth_error:
                    logger.error(f"Failed to set JWT authentication: {auth_error}")
                    raise
            
            logger.debug("Supabase client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {str(e)}")
            raise
    
    # Contract operations
    def get_user_contracts(self, user_jwt: str) -> List[Dict[Any, Any]]:
        """Get all contracts for the authenticated user with analyses count"""
        logger.info("Getting user contracts from Supabase")
        try:
            client = self.get_client(user_jwt)
            
            # Get all contracts for the user (RLS will filter automatically)
            logger.debug("Executing contracts table query")
            response = client.table("contracts").select("*").execute()
            logger.info(f"Contracts query returned {len(response.data)} contracts")
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase error in get_user_contracts: {response.error}")
            
            contracts = response.data
            
            # For each contract, count the analyses
            for contract in contracts:
                try:
                    analyses_response = client.table("contract_analysis").select("id").eq("contract_id", contract['id']).execute()
                    contract['analyses_count'] = len(analyses_response.data)
                except Exception as e:
                    logger.warning(f"Failed to get analyses count for contract {contract['id']}: {str(e)}")
                    contract['analyses_count'] = 0
            
            logger.info(f"Successfully retrieved {len(contracts)} contracts")
            return contracts
            
        except Exception as e:
            logger.error(f"Error in get_user_contracts: {str(e)}")
            raise
    
    def get_contract_by_id(self, contract_id: str, user_jwt: str) -> Dict[Any, Any] | None:
        """Get a specific contract by ID for the authenticated user"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").select("*").eq("id", contract_id).execute()
        return response.data[0] if response.data else None
    
    def create_contract(self, contract_data: Dict[str, Any], user_jwt: str) -> Dict[Any, Any] | None:
        """Create a new contract"""
        logger.info(f"Creating new contract with data keys: {list(contract_data.keys())}")
        try:
            client = self.get_client(user_jwt)
            logger.debug("Executing contract insert query")
            response = client.table("contracts").insert(contract_data).execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase error in create_contract: {response.error}")
                return None
            
            result = response.data[0] if response.data else None
            if result:
                logger.info(f"Successfully created contract with ID: {result.get('id')}")
            else:
                logger.warning("Contract creation returned no data")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in create_contract: {str(e)}")
            raise
    
    def update_contract(self, contract_id: str, updates: Dict[str, Any], user_jwt: str) -> bool:
        """Update a contract"""
        try:
            client = self.get_client(user_jwt)
            response = client.table("contracts").update(updates).eq("id", contract_id).execute()
            
            # Check if the update was successful
            # Supabase update operations might not return data, but they should not have errors
            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase error in update_contract: {response.error}")
                return False
            
            # If no error and we have data, or if no error and no data (successful update with no return)
            return True
            
        except Exception as e:
            logger.error(f"Error in update_contract: {str(e)}")
            return False
    
    def delete_contract(self, contract_id: str, user_jwt: str) -> bool:
        """Delete a contract"""
        client = self.get_client(user_jwt)
        response = client.table("contracts").delete().eq("id", contract_id).execute()
        return len(response.data) > 0
    
    # Contract Analysis operations
    def get_contract_analyses(self, contract_id: str, user_jwt: str) -> List[Dict[Any, Any]]:
        """Get all analyses for a contract with risk factors, ordered by creation date (newest first)"""
        client = self.get_client(user_jwt)
        response = client.table("contract_analysis").select("*, risk_factors(*)").eq("contract_id", contract_id).order("created_at", desc=True).execute()
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

    def update_profile(self, user_id: str, updates: Dict[str, Any], user_jwt: str) -> bool:
        """Update a user's profile using public.profiles table with UPSERT functionality"""
        logger.info(f"Attempting to upsert profiles table for user_id: {user_id} with updates: {updates}")
        try:
            client = self.get_client(user_jwt)
            
            # Prepare the profile data for upsert (includes the user_id as primary key)
            profile_data = {"id": user_id}
            
            if 'first_name' in updates:
                profile_data['first_name'] = updates['first_name']
            if 'last_name' in updates:
                profile_data['last_name'] = updates['last_name']
            if 'phone' in updates:
                profile_data['phone'] = updates['phone']
            if 'email' in updates:
                profile_data['email'] = updates['email']
            
            # Only include the id if we have other fields to update
            if len(profile_data) == 1:  # Only has 'id'
                logger.warning(f"No valid profile fields to update for user_id: {user_id}")
                return True
            
            logger.debug(f"Profile upsert data: {profile_data}")
            
            # Use upsert to INSERT if record doesn't exist, UPDATE if it does
            # This handles both new users (no profile record) and existing users
            response = client.table("profiles").upsert(profile_data).execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase error in update_profile upsert: {response.error}")
                return False
            
            logger.info(f"Profiles table upsert successful for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in update_profile: {str(e)}")
            return False

    # Optimized methods for new endpoints
    def get_dashboard_stats(self, user_jwt: str) -> Dict[str, Any]:
        """Get optimized dashboard statistics with minimal database queries"""
        logger.info("Getting optimized dashboard stats from Supabase")
        try:
            client = self.get_client(user_jwt)
            
            # Get contract counts by status in one query (RLS ensures user-only data)
            contracts_response = client.table("contracts").select("id, status, created_at").execute()
            contracts = contracts_response.data
            
            total_contracts = len(contracts)
            
            # Calculate status breakdown (already user-scoped via RLS)
            status_counts = {'uploaded': 0, 'processing': 0, 'analyzed': 0, 'error': 0}
            for contract in contracts:
                status = contract.get('status', 'unknown')
                if status in status_counts:
                    status_counts[status] += 1
            
            # Get risk distribution - ONLY for user's contracts
            analyzed_contract_ids = [c['id'] for c in contracts if c.get('status') == 'analyzed']
            
            risk_response = client.table("contract_analysis").select("risk_level, contract_id, created_at").in_("contract_id", analyzed_contract_ids).execute()
            seen_contracts = set()
            latest_analyses = []
            for analysis in risk_response.data:
                if analysis['contract_id'] not in seen_contracts:
                    latest_analyses.append(analysis)
                    seen_contracts.add(analysis['contract_id'])
            
            # Count risk levels
            risk_counts = {'low': 0, 'medium_low': 0, 'medium': 0, 'medium_high': 0, 'high': 0}
            for analysis in latest_analyses:
                risk_level = analysis.get('risk_level', '').lower().replace('-', '_')  # Convert hyphens to underscores
                if risk_level in risk_counts:
                    risk_counts[risk_level] += 1
            
            # Get most recent 5 contracts directly from database (RLS ensures user-only)
            recent_response = client.table("contracts").select("id, original_filename, status, created_at").order("created_at", desc=True).limit(5).execute()
            recent_activity = recent_response.data
            
            dashboard_data = {
                'total_contracts': total_contracts,
                'status_breakdown': status_counts,
                'risk_distribution': risk_counts,
                'recent_activity': recent_activity
            }
            
            logger.info(f"Successfully retrieved dashboard stats: {total_contracts} contracts")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error in get_dashboard_stats: {str(e)}")
            raise

    def get_contracts_list(self, user_jwt: str, status_filter: str = None) -> List[Dict[str, Any]]:
        """Get optimized contracts list with only required fields"""
        logger.info("Getting optimized contracts list from Supabase")
        try:
            client = self.get_client(user_jwt)
            
            # Select only the fields needed for the contract list
            select_fields = "id, original_filename, contract_type, status, file_size, file_url, execution_date, effective_date, expiration_date, termination_date, created_at, updated_at"
            
            query = client.table("contracts").select(select_fields)
            
            # Apply status filter if provided
            if status_filter:
                query = query.eq("status", status_filter)
            
            # Execute query and sort by created_at descending
            response = query.order("created_at", desc=True).execute()
            contracts = response.data
            
            # Get analyses count for each contract with optimized query
            for contract in contracts:
                try:
                    analyses_response = client.table("contract_analysis").select("id").eq("contract_id", contract['id']).execute()
                    contract['analyses_count'] = len(analyses_response.data)
                except Exception as e:
                    logger.warning(f"Failed to get analyses count for contract {contract['id']}: {str(e)}")
                    contract['analyses_count'] = 0
            
            logger.info(f"Successfully retrieved {len(contracts)} contracts for list view")
            return contracts
            
        except Exception as e:
            logger.error(f"Error in get_contracts_list: {str(e)}")
            raise

    def get_user_stats(self, user_id: str, user_jwt: str) -> Dict[str, Any]:
        """Get user account statistics using optimized queries"""
        logger.info(f"Getting user stats for user_id: {user_id}")
        try:
            client = self.get_client(user_jwt)
            
            # Use count query for contracts (more efficient than selecting all records)
            contracts_response = client.table("contracts").select("*", count="exact").execute()
            contracts_analyzed = contracts_response.count if hasattr(contracts_response, 'count') else 0
            
            # Get member since date from profiles table created_at
            member_since = "Unknown"
            try:
                profile_response = client.table("profiles").select("created_at").eq("id", user_id).single().execute()
                if profile_response.data:
                    created_at = profile_response.data.get('created_at')
                    if created_at:
                        from datetime import datetime
                        try:
                            # Parse the ISO date string and format it
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            member_since = date_obj.strftime("%b %Y")
                        except Exception as e:
                            logger.warning(f"Failed to parse profile created_at date: {e}")
                            member_since = "Unknown"
            except Exception as profile_error:
                logger.warning(f"Failed to get profile created_at: {profile_error}")
                member_since = "Unknown"
            
            # Get last login from auth (this would typically come from Supabase auth metadata)
            # For now, we'll use a placeholder
            last_login = "Today"
            
            stats = {
                'contracts_analyzed': contracts_analyzed,
                'member_since': member_since,
                'last_login': last_login,
                'subscription_plan': 'Free Plan',
                'analyses_remaining': max(0, 10 - contracts_analyzed)  # Assuming 10 free analyses
            }
            
            logger.info(f"Successfully retrieved user stats: {contracts_analyzed} contracts analyzed")
            return stats
            
        except Exception as e:
            logger.error(f"Error in get_user_stats: {str(e)}")
            return None


# Global instance
supabase_service = SupabaseService()
