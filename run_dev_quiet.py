#!/usr/bin/env python3
"""
Quiet development server startup script for FastAPI backend
This version reduces the verbose watchfiles logging
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def main():
    """Start the FastAPI development server with reduced logging"""
    try:
        import uvicorn
        from app.main import app
        
        # Reduce watchfiles logging to WARNING level to stop the spam
        logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
        
        print("🚀 Starting FastAPI development server (quiet mode)...")
        print("📖 API Documentation will be available at: http://localhost:8000/docs")
        print("🔍 Interactive API explorer at: http://localhost:8000/redoc")
        print("❤️  Health check at: http://localhost:8000/health")
        print("🔇 Watchfiles logging reduced to minimize terminal spam")
        print()
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app"],
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
