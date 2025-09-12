#!/usr/bin/env python3
"""
Development server startup script for FastAPI backend
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def main():
    """Start the FastAPI development server"""
    try:
        import uvicorn
        from app.main import app
        
        print("🚀 Starting FastAPI development server...")
        print("📖 API Documentation will be available at: http://localhost:8000/docs")
        print("🔍 Interactive API explorer at: http://localhost:8000/redoc")
        print("❤️  Health check at: http://localhost:8000/health")
        print()
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not found. Please install it:")
        print("   pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
