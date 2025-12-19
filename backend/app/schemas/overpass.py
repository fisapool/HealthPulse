"""
Pydantic schemas for Overpass API proxy endpoints
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class OverpassQueryRequest(BaseModel):
    """Request schema for Overpass QL query"""
    query: str = Field(..., description="Overpass QL query string")
    timeout: Optional[int] = Field(25, ge=1, le=300, description="Query timeout in seconds")
    bbox: Optional[List[float]] = Field(
        None,
        description="Bounding box [south, west, north, east]",
        min_length=4,
        max_length=4
    )


class OverpassElement(BaseModel):
    """OSM element from Overpass API response"""
    type: str
    id: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    center: Optional[Dict[str, float]] = None
    tags: Optional[Dict[str, str]] = None
    timestamp: Optional[str] = None
    version: Optional[int] = None
    changeset: Optional[int] = None
    user: Optional[str] = None
    uid: Optional[int] = None


class OverpassQueryResponse(BaseModel):
    """Response schema for Overpass API query"""
    version: Optional[float] = None
    generator: Optional[str] = None
    osm3s: Optional[Dict[str, Any]] = None
    elements: List[OverpassElement] = Field(default_factory=list)
    remark: Optional[str] = None


class FacilityOSM(BaseModel):
    """OSM element mapped to facility format"""
    id: str
    name: str
    type: str  # "hospital" or "clinic"
    location: Dict[str, float]  # {"lat": float, "lng": float}
    address: str
    contact: Optional[str] = None
    lastUpdated: str
    score: int = Field(ge=0, le=100, description="Data quality score")
    osm_tags: Optional[Dict[str, str]] = None


class FacilitiesResponse(BaseModel):
    """Response schema for facilities endpoint"""
    facilities: List[FacilityOSM]
    count: int
    bbox: Optional[List[float]] = None
    cached: bool = False


class OverpassHealthResponse(BaseModel):
    """Health check response for Overpass API"""
    status: str
    available: bool
    version: Optional[str] = None
    message: Optional[str] = None

