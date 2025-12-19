"""
Pydantic schemas for DOSM Record with mandatory metadata block
"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, Literal
from datetime import datetime


class RecordMetadata(BaseModel):
    """Mandatory metadata block for every DOSM record"""
    source: Literal["DOSM"] = "DOSM"
    dataset_id: str = Field(..., description="Dataset identifier")
    source_url: str = Field(..., description="Source URL where data was retrieved")
    file_type: Literal["api", "csv", "xlsx", "pdf", "html"] = Field(..., description="Type of source file")
    published_date: Optional[datetime] = Field(None, description="Date when data was published")
    retrieved_at: datetime = Field(..., description="Timestamp when data was retrieved")
    scrape_method: Literal[
        "opendosm_api",
        "direct_download",
        "pdf_extraction",
        "html_parsing",
        "browser_automation"
    ] = Field(..., description="Method used to scrape the data")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence level of the data")

    @field_validator("retrieved_at", mode="before")
    @classmethod
    def parse_retrieved_at(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    @field_validator("published_date", mode="before")
    @classmethod
    def parse_published_date(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "source": "DOSM",
                "dataset_id": "health_statistics_2024",
                "source_url": "https://open.dosm.gov.my/api/data/health_statistics_2024",
                "file_type": "api",
                "published_date": "2024-01-01T00:00:00Z",
                "retrieved_at": "2024-01-15T10:30:00Z",
                "scrape_method": "opendosm_api",
                "confidence": "high"
            }
        }


class DOSMRecordCreate(BaseModel):
    """Schema for creating a DOSM record"""
    dataset_id: str = Field(..., description="Dataset identifier")
    data: Dict[str, Any] = Field(..., description="Actual data fields (flexible schema)")
    metadata: RecordMetadata = Field(..., description="Mandatory metadata block")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "health_statistics_2024",
                "data": {
                    "facility_name": "Hospital ABC",
                    "location": "Kuala Lumpur",
                    "beds": 500
                },
                "metadata": {
                    "source": "DOSM",
                    "dataset_id": "health_statistics_2024",
                    "source_url": "https://open.dosm.gov.my/api/data/health_statistics_2024",
                    "file_type": "api",
                    "published_date": "2024-01-01T00:00:00Z",
                    "retrieved_at": "2024-01-15T10:30:00Z",
                    "scrape_method": "opendosm_api",
                    "confidence": "high"
                }
            }
        }


class DOSMRecordResponse(BaseModel):
    """Schema for DOSM record response"""
    id: int
    dataset_id: str
    data: Dict[str, Any]
    record_metadata: Dict[str, Any] = Field(..., serialization_alias="metadata")
    created_at: str

    class Config:
        from_attributes = True


class DatasetVersionResponse(BaseModel):
    """Schema for dataset version response"""
    id: int
    dataset_id: str
    file_hash: str
    schema_fingerprint: Optional[str]
    version_number: int
    record_count: int
    file_size: Optional[int]
    retrieved_at: str
    created_at: str

    class Config:
        from_attributes = True

