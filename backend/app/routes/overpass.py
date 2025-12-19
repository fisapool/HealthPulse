"""
Overpass API proxy routes
"""
import logging
from typing import Optional
import httpx
from fastapi import APIRouter, HTTPException, Request, Depends, Body, Query
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


def build_healthcare_facilities_query(
    bounds: Optional[list] = None,
    state_name: Optional[str] = None,
    city_name: Optional[str] = None
) -> str:
    """Build Overpass QL query for healthcare facilities"""
    
    # Base facility tags for area queries - each statement includes (area) filter
    def build_facility_queries_for_area():
        """Build individual facility query statements for area queries"""
        queries = [
            'node["amenity"="hospital"](area);',
            'way["amenity"="hospital"](area);',
            'relation["amenity"="hospital"](area);',
            'node["amenity"="clinic"](area);',
            'way["amenity"="clinic"](area);',
            'relation["amenity"="clinic"](area);',
            'node["healthcare"="hospital"](area);',
            'way["healthcare"="hospital"](area);',
            'relation["healthcare"="hospital"](area);',
            'node["healthcare"="clinic"](area);',
            'way["healthcare"="clinic"](area);',
            'relation["healthcare"="clinic"](area);',
            'node["healthcare"="health_centre"](area);',
            'way["healthcare"="health_centre"](area);',
            'relation["healthcare"="health_centre"](area);'
        ]
        return '\n'.join(queries)
    
    # For bbox queries, use individual statements
    facility_tags_bbox = """node["amenity"="hospital"];
way["amenity"="hospital"];
relation["amenity"="hospital"];
node["amenity"="clinic"];
way["amenity"="clinic"];
relation["amenity"="clinic"];
node["healthcare"="hospital"];
way["healthcare"="hospital"];
relation["healthcare"="hospital"];
node["healthcare"="clinic"];
way["healthcare"="clinic"];
relation["healthcare"="clinic"];
node["healthcare"="health_centre"];
way["healthcare"="health_centre"];
relation["healthcare"="health_centre"];"""
    
    if state_name:
        # State-level query using admin_level=4 for Malaysian states
        # Use map_to_area pattern for area queries
        # Each facility query statement includes (area) filter individually
        facility_queries = build_facility_queries_for_area()
        query = f"""[out:json][timeout:300];
rel["name"="{state_name}"]["admin_level"="4"]["boundary"="administrative"];
map_to_area;
{facility_queries}
out center;"""
        
        return query
    
    elif city_name:
        # City-level query: Use boundary relation (admin_level=8 for cities)
        # Use map_to_area pattern for city area queries (admin_level=8 in Malaysia)
        # Note: Some cities may not have boundary relations in OSM - those will return empty results
        # Each facility query statement includes (area) filter individually
        facility_queries = build_facility_queries_for_area()
        query = f"""[out:json][timeout:300];
rel["name"="{city_name}"]["admin_level"="8"]["boundary"="administrative"];
map_to_area;
{facility_queries}
out center;"""
        
        return query
    
    else:
        # Default to bbox query
        # Use provided bounds or default to Malaysia
        if not bounds:
            bounds = MALAYSIA_BOUNDS
        
        # Ensure bounds are floats for proper numeric formatting (no quotes)
        south, west, north, east = [float(b) for b in bounds]
        
        # Pre-format the bbox to avoid any interpolation issues
        bbox = f"{south},{west},{north},{east}"
        
        # Use individual statements for bbox queries (grouped syntax doesn't work)
        # Each statement needs its own bbox filter
        bbox_str = f"{bbox}"
        query_lines = [
            "[out:json][timeout:300];"
        ]
        for line in facility_tags_bbox.strip().split('\n'):
            if line.strip() and line.strip().endswith(';'):
                # Add bbox filter to each statement
                query_lines.append(line.rstrip(';') + f"({bbox_str});")
        query_lines.append("out center;")
        query = '\n'.join(query_lines)
        
        return query


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
    bbox: Optional[list] = Body(None),
    state_name: Optional[str] = Body(None, description="Filter by state name (e.g., Selangor)"),
    city_name: Optional[str] = Body(None, description="Filter by city name (e.g., Kuala Lumpur)")
):
    """
    Get healthcare facilities (hospitals and clinics) for Malaysia
    
    Optionally accepts:
    - A bounding box [south, west, north, east] to filter results
    - state_name: Filter by state name (e.g., "Selangor", "Johor")
    - city_name: Filter by city name (e.g., "Kuala Lumpur", "Penang")
    
    If not provided, uses Malaysia's full bounding box.
    Note: state_name and city_name cannot be used together.
    """
    try:
        # Validate parameters
        if state_name and city_name:
            raise HTTPException(
                status_code=400,
                detail="Specify either state_name or city_name, not both."
            )
        
        service = get_overpass_service()
        client_id = get_client_id(request) if request else "default"
        
        # Build query based on parameters
        if state_name or city_name:
            # Use area-based query
            query = build_healthcare_facilities_query(
                bounds=None,
                state_name=state_name,
                city_name=city_name
            )
        else:
            # Use bbox query
            bounds = bbox if bbox and len(bbox) == 4 else MALAYSIA_BOUNDS
            query = build_healthcare_facilities_query(bounds=bounds)
        
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
        
        # Determine bounds for response
        bounds = bbox if bbox and len(bbox) == 4 else (None if state_name or city_name else MALAYSIA_BOUNDS)
        
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
    try:
        bbox = [south, west, north, east]
        service = get_overpass_service()
        client_id = get_client_id(request) if request else "default"
        
        # Build and execute query directly (don't call POST endpoint)
        query = build_healthcare_facilities_query(bounds=bbox)
        
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
                if facility.type in ["hospital", "clinic"]:
                    facilities.append(facility)
        
        return FacilitiesResponse(
            facilities=facilities,
            count=len(facilities),
            bbox=bbox,
            cached=False
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


@router.get("/facilities", response_model=FacilitiesResponse)
async def get_facilities_by_location(
    request: Request,
    state_name: Optional[str] = Query(None, description="Filter by state name (e.g., Selangor, Johor)"),
    city_name: Optional[str] = Query(None, description="Filter by city name (e.g., Kuala Lumpur, Penang)"),
    bbox: Optional[str] = Query(None, description="Bounding box as comma-separated string: south,west,north,east")
):
    """
    Get healthcare facilities filtered by state or city name
    
    Query parameters:
    - state_name: Filter by state name (e.g., "Selangor", "Johor")
    - city_name: Filter by city name (e.g., "Kuala Lumpur", "Penang")
    - bbox: Optional bounding box as "south,west,north,east"
    
    Note: state_name and city_name cannot be used together.
    """
    # Parse bbox if provided
    parsed_bbox = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) == 4:
                parsed_bbox = parts
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox format. Expected: south,west,north,east"
            )
    
    # Use POST endpoint logic
    return await get_healthcare_facilities(
        request=request,
        bbox=parsed_bbox,
        state_name=state_name,
        city_name=city_name
    )

