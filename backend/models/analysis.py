"""
Analysis data models
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId

from .user import PyObjectId


class AnalysisStatus(str, Enum):
    """Analysis status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MarketType(str, Enum):
    """Market type enumeration"""
    CN = "cn"  # Chinese market
    US = "us"  # US market
    HK = "hk"  # Hong Kong market


class AnalysisRequest(BaseModel):
    """Analysis request model"""
    stock_code: str = Field(..., min_length=1, max_length=20)
    market_type: MarketType = MarketType.CN
    analysis_date: Optional[str] = None
    analysts: List[str] = Field(default_factory=list)
    llm_config: Optional[Dict[str, Any]] = None
    custom_params: Optional[Dict[str, Any]] = None


class AnalysisProgress(BaseModel):
    """Analysis progress model"""
    status: AnalysisStatus
    progress: float = Field(ge=0.0, le=100.0)
    current_step: Optional[str] = None
    message: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # seconds


class AnalysisResult(BaseModel):
    """Analysis result model"""
    summary: Optional[Dict[str, Any]] = None
    technical_analysis: Optional[Dict[str, Any]] = None
    fundamental_analysis: Optional[Dict[str, Any]] = None
    news_analysis: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    charts: Optional[List[Dict[str, Any]]] = None
    raw_data: Optional[Dict[str, Any]] = None


class AnalysisInDB(BaseModel):
    """Analysis model as stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    stock_code: str
    market_type: MarketType
    status: AnalysisStatus = AnalysisStatus.PENDING
    progress: float = 0.0
    config: Dict[str, Any] = Field(default_factory=dict)
    result_data: Optional[AnalysisResult] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Analysis(BaseModel):
    """Analysis model for API responses"""
    id: str
    user_id: str
    stock_code: str
    market_type: MarketType
    status: AnalysisStatus
    progress: float
    config: Dict[str, Any]
    result_data: Optional[AnalysisResult] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    """Analysis list response model"""
    analyses: List[Analysis]
    total: int
    page: int
    page_size: int


class AnalysisHistoryQuery(BaseModel):
    """Analysis history query parameters"""
    stock_code: Optional[str] = None
    market_type: Optional[MarketType] = None
    status: Optional[AnalysisStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)