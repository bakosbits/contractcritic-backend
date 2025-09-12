#!/usr/bin/env python3
"""
Test script to validate the FastAPI migration
This script tests basic functionality to ensure the migration was successful
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

try:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.config import settings
    print("✅ Successfully imported FastAPI application")
except ImportError as e:
    print(f"❌ Failed to import FastAPI application: {e}")
    sys.exit(1)

def test_app_startup():
    """Test that the FastAPI app can be created and started"""
    try:
        client = TestClient(app)
        print("✅ FastAPI application created successfully")
        return client
    except Exception as e:
        print(f"❌ Failed to create FastAPI application: {e}")
        return None

def test_health_endpoint(client):
    """Test the health check endpoint"""
    try:
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")

def test_docs_endpoint(client):
    """Test that OpenAPI docs are accessible"""
    try:
        response = client.get("/docs")
        if response.status_code == 200:
            print("✅ OpenAPI docs accessible at /docs")
        else:
            print(f"❌ OpenAPI docs failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAPI docs test failed: {e}")

def test_contract_endpoints(client):
    """Test contract endpoints (without authentication)"""
    try:
        # Test GET /api/v1/contracts (should require auth)
        response = client.get("/api/v1/contracts")
        if response.status_code == 401:
            print("✅ Contract list endpoint properly requires authentication")
        else:
            print(f"⚠️  Contract list endpoint returned unexpected status {response.status_code}")
    except Exception as e:
        print(f"❌ Contract endpoints test failed: {e}")

def test_user_endpoints(client):
    """Test user endpoints (without authentication)"""
    try:
        # Test GET /api/v1/users/profile (should require auth)
        response = client.get("/api/v1/users/profile")
        if response.status_code == 401:
            print("✅ User profile endpoint properly requires authentication")
        else:
            print(f"⚠️  User profile endpoint returned unexpected status {response.status_code}")
    except Exception as e:
        print(f"❌ User endpoints test failed: {e}")

def test_configuration():
    """Test that configuration is loaded correctly"""
    try:
        print(f"✅ Configuration loaded:")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug mode: {settings.DEBUG}")
        print(f"   CORS origins configured: {len(settings.ALLOWED_HOSTS)} hosts")
        print(f"   Supabase URL configured: {'Yes' if settings.SUPABASE_URL else 'No'}")
        print(f"   OpenAI API configured: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting FastAPI Migration Validation Tests")
    print("=" * 50)
    
    # Test configuration
    test_configuration()
    print()
    
    # Test app startup
    client = test_app_startup()
    if not client:
        print("❌ Cannot proceed with endpoint tests - app startup failed")
        return
    
    print()
    
    # Test endpoints
    test_health_endpoint(client)
    test_docs_endpoint(client)
    test_contract_endpoints(client)
    test_user_endpoints(client)
    
    print()
    print("=" * 50)
    print("🎉 FastAPI Migration Validation Complete!")
    print()
    print("Next steps:")
    print("1. Start the development server: uvicorn app.main:app --reload")
    print("2. Visit http://localhost:8000/docs to see the API documentation")
    print("3. Test with your frontend application")

if __name__ == "__main__":
    main()
