from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Request Models
class ContractAnalysisRequest(BaseModel):
    analysis_type: str = Field(..., description="Type of analysis: 'small_business' or 'individual'")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "small_business"
            }
        }


class ContractUpdateRequest(BaseModel):
    status: Optional[str] = None
    contract_type: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "analyzed",
                "contract_type": "Service Agreement"
            }
        }


# Response Models
class ContractUploadResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "contract_id": "123e4567-e89b-12d3-a456-426614174000",
                    "filename": "contract.pdf",
                    "file_size": 1024000,
                    "status": "uploaded"
                },
                "message": "Contract uploaded successfully"
            }
        }


class ContractResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    original_filename: str
    file_url: str
    file_size: int
    mime_type: str
    status: str
    contract_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    analyses_count: Optional[int] = 0
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "filename": "contract_abc123.pdf",
                "original_filename": "contract.pdf",
                "file_url": "https://blob.vercel-storage.com/contract_abc123.pdf",
                "file_size": 1024000,
                "mime_type": "application/pdf",
                "status": "analyzed",
                "contract_type": "Service Agreement",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "analyses_count": 1
            }
        }


class ContractListResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "contracts": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "filename": "contract.pdf",
                            "status": "analyzed",
                            "created_at": "2023-01-01T00:00:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "per_page": 100,
                        "total": 1,
                        "pages": 1,
                        "has_next": False,
                        "has_prev": False
                    }
                }
            }
        }


class RiskFactor(BaseModel):
    id: Optional[str] = None
    analysis_id: str
    category: str
    severity: str
    description: str
    recommendation: str
    created_at: Optional[datetime] = None


class ContractAnalysis(BaseModel):
    id: str
    contract_id: str
    ai_model_used: str
    analysis_type: str
    risk_score: float
    risk_level: str
    analysis_results: Dict[str, Any]
    processing_time_ms: int
    tokens_used: int
    status: str
    created_at: datetime
    updated_at: datetime
    risk_factors: Optional[List[RiskFactor]] = []


class ContractAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                    "contract_id": "456e7890-e89b-12d3-a456-426614174000",
                    "risk_score": 45.5,
                    "risk_level": "Medium",
                    "status": "completed",
                    "processing_time_ms": 5000
                },
                "message": "Contract analysis completed successfully"
            }
        }


class DashboardStats(BaseModel):
    total_contracts: int
    status_breakdown: Dict[str, int]
    risk_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class DashboardStatsResponse(BaseModel):
    success: bool
    data: DashboardStats
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "total_contracts": 10,
                    "status_breakdown": {
                        "uploaded": 2,
                        "processing": 1,
                        "analyzed": 6,
                        "error": 1
                    },
                    "risk_distribution": {
                        "high_risk": 1,
                        "medium_risk": 4,
                        "low_risk": 5
                    },
                    "recent_activity": [
                        {
                            "id": "123",
                            "filename": "contract.pdf",
                            "status": "analyzed",
                            "created_at": "2023-01-01T00:00:00Z"
                        }
                    ]
                }
            }
        }


# Generic Response Models
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    status_code: Optional[int] = None
    details: Optional[List[str]] = None
