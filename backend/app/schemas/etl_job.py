"""
Pydantic schemas for ETL Job API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ETLJobStatus(str, Enum):
    """Enum for ETL job status values"""
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ETLJobCreate(BaseModel):
    """Schema for creating a new ETL job"""
    source: str = Field(..., max_length=100, description="Data source name (e.g., 'DHIS2', 'Legacy SQL')")
    status: Optional[ETLJobStatus] = Field(default=ETLJobStatus.PENDING, description="Job status")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "DHIS2",
                "status": "Pending"
            }
        }


class ETLJobResponse(BaseModel):
    """Schema for ETL job response"""
    id: str
    source: str
    status: ETLJobStatus
    records_processed: int = Field(..., ge=0, description="Number of records processed")
    start_time: str
    errors: int = Field(..., ge=0, description="Number of errors encountered")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "1",
                "source": "DHIS2",
                "status": "Completed",
                "records_processed": 1250,
                "start_time": "2024-01-15T10:30:00Z",
                "errors": 0
            }
        }

