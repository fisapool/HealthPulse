"""
Overpass API proxy routes
"""
import logging
from typing import Optional
import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.schemas.overpass import (
    OverpassQueryRequest,
    OverpassQueryResponse,
    FacilitiesResponse,
    FacilityOSM,
    OverpassHealthResponse
)
from app.services.overpass_proxy import get_overpass_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Malaysia bounding box: [south, west, north, east]
MALAYSIA_BOUNDS = [0.855, 98.942, 7.363, 119.267]


def build_healthcare_facilities_query(bounds: list = MALAYSIA_BOUNDS) -> str:
    """Build Overpass QL query for healthcare facilities"""
    south, west, north, east = bounds
    return f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"]({south},{west},{north},{east});
      way["amenity"="hospital"]({south},{west},{north},{east});
      relation["amenity"="hospital"]({south},{west},{north},{east});
      node["amenity"="clinic"]({south},{west},{north},{east});
      way["amenity"="clinic"]({south},{west},{north},{east});
      relation["amenity"="clinic"]({south},{west},{north},{east});
      node["healthcare"="hospital"]({south},{west},{north},{east});
      way["healthcare"="hospital"]({south},{west},{north},{east});
      relation["healthcare"="hospital"]({south},{west},{north},{east});
      node["healthcare"="clinic"]({south},{west},{north},{east});
      way["healthcare"="clinic"]({south},{west},{north},{east});
      relation["healthcare"="clinic"]({south},{west},{north},{east});
      node["healthcare"="health_centre"]({south},{west},{north},{east});
      way["healthcare"="health_centre"]({south},{west},{north},{east});
      relation["healthcare"="health_centre"]({south},{west},{north},{east});
    );
    out center;
    """.strip()


def map_osm_to_facility(element: dict) -> Optional[FacilityOSM]:
    """Map OSM element to FacilityOSM schema"""
    try:
        # Extract coordinates
        location = {"lat": 0.0, "lng": 0.0}
        if element.get("type") == "node":
            if "lat" in element and "lon" in element:
                location = {"lat": float(element["lat"]), "lng": float(element["lon"])}
        elif element.get("type") in ["way", "relation"]:
            if "center" in element:
                center = element["center"]
                location = {"lat": float(center.get("lat", 0)), "lng": float(center.get("lon", 0))}
        
        # Skip if no valid coordinates
        if location["lat"] == 0.0 and location["lng"] == 0.0:
            return None
        
        # Determine facility type
        tags = element.get("tags", {})
        amenity = tags.get("amenity", "").lower()
        healthcare = tags.get("healthcare", "").lower()
        
        facility_type = "clinic"  # Default
        if amenity == "hospital" or healthcare == "hospital":
            facility_type = "hospital"
        elif amenity == "clinic" or healthcare in ["clinic", "health_centre"]:
            facility_type = "clinic"
        
        # Calculate quality score
        score = 0
        if tags.get("name"):
            score += 25
        if tags.get("amenity") or tags.get("healthcare"):
            score += 20
        if tags.get("operator"):
            score += 15
        if tags.get("phone") or tags.get("contact:phone"):
            score += 10
        if tags.get("addr:full") or tags.get("addr:street"):
            score += 15
        if location["lat"] != 0 and location["lng"] != 0:
            score += 15
        
        # Build address
        address = tags.get("addr:full", "")
        if not address:
            parts = []
            if tags.get("addr:street"):
                parts.append(tags["addr:street"])
            if tags.get("addr:city"):
                parts.append(tags["addr:city"])
            if tags.get("addr:postcode"):
                parts.append(tags["addr:postcode"])
            if tags.get("addr:state"):
                parts.append(tags["addr:state"])
            address = ", ".join(parts) if parts else f"{location['lat']:.4f}, {location['lng']:.4f}"
        
        # Get last updated
        last_updated = element.get("timestamp", "")
        if not last_updated:
            last_updated = ""
        
        return FacilityOSM(
            id=f"{element.get('type', 'unknown')}-{element.get('id', 'unknown')}",
            name=tags.get("name", "Unnamed Facility"),
            type=facility_type,
            location=location,
            address=address,
            contact=tags.get("phone") or tags.get("contact:phone"),
            lastUpdated=last_updated,
            score=min(score, 100),
            osm_tags=tags
        )
    except Exception as e:
        logger.warning(f"Error mapping OSM element to facility: {e}")
        return None


def get_client_id(request: Request) -> str:
    """Get client identifier from request (IP address)"""
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/query", response_model=OverpassQueryResponse)
async def execute_overpass_query(
    request_data: OverpassQueryRequest,
    request: Request
):
    """
    Execute a raw Overpass QL query through the proxy
    
    This endpoint forwards Overpass QL queries to the Overpass API instance
    with caching and rate limiting applied.
    """
    try:
        service = get_overpass_service()
        client_id = get_client_id(request)
        
        # Execute query
        response_data = await service.execute_query(
            query=request_data.query,
            client_id=client_id,
            use_cache=True
        )
        
        return OverpassQueryResponse(**response_data)
    
    except ValueError as e:
        # Rate limit error
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing Overpass query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.get("/health", response_model=OverpassHealthResponse)
async def check_overpass_health():
    """
    Check the health status of the Overpass API instance
    """
    try:
        service = get_overpass_service()
        health = await service.check_health()
        return OverpassHealthResponse(**health)
    except Exception as e:
        logger.error(f"Error checking Overpass health: {e}")
        return OverpassHealthResponse(
            status="error",
            available=False,
            message=str(e)
        )


@router.post("/facilities", response_model=FacilitiesResponse)
async def get_healthcare_facilities(
    request: Request,
    bbox: Optional[list] = None
):
    """
    Get healthcare facilities (hospitals and clinics) for Malaysia
    
    Optionally accepts a bounding box [south, west, north, east] to filter results.
    If not provided, uses Malaysia's full bounding box.
    """
    try:
        service = get_overpass_service()
        client_id = get_client_id(request) if request else "default"
        
        # Use provided bbox or default to Malaysia
        bounds = bbox if bbox and len(bbox) == 4 else MALAYSIA_BOUNDS
        
        # Build and execute query
        query = build_healthcare_facilities_query(bounds)
        response_data = await service.execute_query(
            query=query,
            client_id=client_id,
            use_cache=True
        )
        
        # Map OSM elements to facilities
        elements = response_data.get("elements", [])
        facilities = []
        for element in elements:
            facility = map_osm_to_facility(element)
            if facility:
                # Filter to only hospitals and clinics
                if facility.type in ["hospital", "clinic"]:
                    facilities.append(facility)
        
        return FacilitiesResponse(
            facilities=facilities,
            count=len(facilities),
            bbox=bounds,
            cached=False  # TODO: Track cache hits in service
        )
    
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code if e.response else None
        logger.error(f"Overpass API HTTP error: {status_code} - {str(e)}")
        if status_code == 504:
            raise HTTPException(
                status_code=503,
                detail="Overpass API is temporarily unavailable (timeout). Please try again in a few moments."
            )
        elif status_code and status_code >= 500:
            raise HTTPException(
                status_code=503,
                detail=f"Overpass API service error ({status_code}). Please try again later."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Overpass API error: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Overpass API request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Overpass API. Please try again later."
        )
    except Exception as e:
        logger.error(f"Error fetching healthcare facilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch facilities: {str(e)}")


@router.get("/facilities/bbox", response_model=FacilitiesResponse)
async def get_facilities_by_bbox(
    south: float,
    west: float,
    north: float,
    east: float,
    request: Request
):
    """
    Get healthcare facilities within a bounding box
    
    Query parameters:
    - south: Southern latitude
    - west: Western longitude
    - north: Northern latitude
    - east: Eastern longitude
    """
    bbox = [south, west, north, east]
    return await get_healthcare_facilities(bbox=bbox, request=request)

