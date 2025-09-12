from fastapi import APIRouter

from app.api.v1.endpoints import contracts, users

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(users.router, prefix="/auth", tags=["authentication"])
