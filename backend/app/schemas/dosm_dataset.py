"""
Pydantic schemas for DOSM Dataset API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.dosm_dataset import ScrapeTier


class DOSMDatasetCreate(BaseModel):
    """Schema for creating a new DOSM dataset entry"""
    dataset_id: str = Field(..., max_length=255, description="Unique dataset identifier")
    name: str = Field(..., max_length=500, description="Dataset name")
    description: Optional[str] = Field(None, max_length=2000, description="Dataset description")
    source_url: str = Field(..., max_length=1000, description="Source URL for the dataset")
    tier: ScrapeTier = Field(..., description="Scraping tier assigned to this dataset")
    scrape_method: str = Field(..., max_length=100, description="Method used to scrape this dataset")
    update_frequency: Optional[str] = Field(None, max_length=50, description="Expected update frequency")
    confidence: str = Field(default="high", pattern="^(high|medium|low)$", description="Data confidence level")
    is_statistical: bool = Field(default=True, description="Whether this is statistical reference data")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "health_statistics_2024",
                "name": "Health Statistics 2024",
                "description": "Annual health statistics from DOSM",
                "source_url": "https://open.dosm.gov.my/api/data/health_statistics_2024",
                "tier": "tier1_opendosm",
                "scrape_method": "opendosm_api",
                "update_frequency": "annually",
                "confidence": "high",
                "is_statistical": True
            }
        }


class DOSMDatasetUpdate(BaseModel):
    """Schema for updating a DOSM dataset"""
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    source_url: Optional[str] = Field(None, max_length=1000)
    tier: Optional[ScrapeTier] = None
    scrape_method: Optional[str] = Field(None, max_length=100)
    update_frequency: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    confidence: Optional[str] = Field(None, pattern="^(high|medium|low)$")


class DOSMDatasetResponse(BaseModel):
    """Schema for DOSM dataset response"""
    id: int
    dataset_id: str
    name: str
    description: Optional[str]
    source_url: str
    tier: ScrapeTier
    scrape_method: str
    update_frequency: Optional[str]
    last_checked: Optional[str]
    last_successful_scrape: Optional[str]
    is_statistical: bool
    is_active: bool
    confidence: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "dataset_id": "health_statistics_2024",
                "name": "Health Statistics 2024",
                "description": "Annual health statistics from DOSM",
                "source_url": "https://open.dosm.gov.my/api/data/health_statistics_2024",
                "tier": "tier1_opendosm",
                "scrape_method": "opendosm_api",
                "update_frequency": "annually",
                "last_checked": "2024-01-15T10:30:00Z",
                "last_successful_scrape": "2024-01-15T10:35:00Z",
                "is_statistical": True,
                "is_active": True,
                "confidence": "high",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        }

