"""
Facilities API routes
Query facilities from database (fast) instead of Overpass API (slow)
"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text
from app.database import get_db
from app.models.facility import Facility
from app.models.etl_job import ETLJob
from app.services.state_mapping import get_comprehensive_city_state_mapping, normalize_state_name

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/facilities")
async def get_facilities(
    bbox: Optional[str] = Query(None, description="Bounding box: south,west,north,east"),
    facility_type: Optional[str] = Query(None, description="Filter by type: 'hospital' or 'clinic'"),
    limit: int = Query(1000, le=10000, description="Maximum number of facilities to return"),
    skip: int = Query(0, ge=0, description="Number of facilities to skip"),
    db: Session = Depends(get_db)
):
    """
    Get healthcare facilities from database (fast!)
    
    This endpoint queries the local database instead of Overpass API,
    providing much faster response times (milliseconds vs seconds).
    
    Facilities are populated via ETL jobs that fetch from Overpass API.
    Use the /etl-jobs/overpass-facilities endpoint to refresh data.
    """
    try:
        query = db.query(Facility)
        
        # Filter by facility type
        if facility_type:
            facility_type_lower = facility_type.lower()
            if facility_type_lower not in ["hospital", "clinic"]:
                raise HTTPException(
                    status_code=400,
                    detail="facility_type must be 'hospital' or 'clinic'"
                )
            query = query.filter(Facility.facility_type == facility_type_lower)
        
        # Filter by bounding box
        if bbox:
            try:
                coords = [float(x.strip()) for x in bbox.split(",")]
                if len(coords) != 4:
                    raise ValueError("Bounding box must have 4 coordinates")
                south, west, north, east = coords
                
                # Validate coordinates
                if not (-90 <= south <= 90) or not (-90 <= north <= 90):
                    raise ValueError("Latitude must be between -90 and 90")
                if not (-180 <= west <= 180) or not (-180 <= east <= 180):
                    raise ValueError("Longitude must be between -180 and 180")
                if south >= north:
                    raise ValueError("South must be less than north")
                if west >= east:
                    raise ValueError("West must be less than east")
                
                query = query.filter(
                    and_(
                        Facility.latitude >= south,
                        Facility.latitude <= north,
                        Facility.longitude >= west,
                        Facility.longitude <= east
                    )
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid bounding box format: {str(e)}. Expected: south,west,north,east"
                )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        facilities = query.order_by(Facility.name).offset(skip).limit(limit).all()
        
        # Map to response format
        facilities_data = [{
            "id": f.id,
            "osm_id": f.osm_id,
            "name": f.name,
            "type": f.facility_type,
            "location": {"lat": f.latitude, "lng": f.longitude},
            "address": f.address or "",
            "contact": f.contact or "",
            "lastUpdated": f.last_updated_osm.isoformat() if f.last_updated_osm else "",
            "score": f.quality_score,
            "osm_tags": f.osm_tags
        } for f in facilities]
        
        return {
            "facilities": facilities_data,
            "count": len(facilities_data),
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching facilities from database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch facilities: {str(e)}"
        )


@router.get("/facilities/stats")
async def get_facility_stats(db: Session = Depends(get_db)):
    """
    Get statistics about facilities in the database
    """
    try:
        total = db.query(Facility).count()
        hospitals = db.query(Facility).filter(Facility.facility_type == "hospital").count()
        clinics = db.query(Facility).filter(Facility.facility_type == "clinic").count()
        
        # Get average quality score
        avg_score_result = db.query(
            func.avg(Facility.quality_score)
        ).scalar()
        avg_score = round(float(avg_score_result or 0), 2)
        
        return {
            "total": total,
            "hospitals": hospitals,
            "clinics": clinics,
            "average_quality_score": avg_score
        }
    except Exception as e:
        logger.error(f"Error fetching facility stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.get("/facilities/by-state")
async def get_facilities_by_state(db: Session = Depends(get_db)):
    """
    Get facility counts grouped by state from OSM tags (addr:state)
    """
    try:
        # Get all facilities with their OSM tags
        facilities = db.query(Facility).all()
        
        # Load comprehensive city-to-state mapping (includes DOSM data if available)
        city_to_state_mapping = get_comprehensive_city_state_mapping(db)
        
        state_counts = {}
        extraction_stats = {"addr_state": 0, "addr_province": 0, "is_in_state": 0, "city_mapping": 0, "address_parsing": 0, "unknown": 0}
        
        for facility in facilities:
            state = "Unknown"
            extraction_method = "unknown"
            if facility.osm_tags:
                # Prioritize state from OSM tags (check multiple possible fields)
                if facility.osm_tags.get("addr:state"):
                    state = normalize_state_name(facility.osm_tags.get("addr:state"))
                    extraction_method = "addr_state"
                    extraction_stats["addr_state"] += 1
                elif facility.osm_tags.get("addr:province"):
                    state = normalize_state_name(facility.osm_tags.get("addr:province"))
                    extraction_method = "addr_province"
                    extraction_stats["addr_province"] += 1
                elif facility.osm_tags.get("is_in:state"):
                    state = normalize_state_name(facility.osm_tags.get("is_in:state"))
                    extraction_method = "is_in_state"
                    extraction_stats["is_in_state"] += 1
            
            # Fallback 1: Map city name to state using comprehensive mapping (includes DOSM data)
            if state == "Unknown" and facility.address:
                address_lower = facility.address.lower()
                for city, mapped_state in city_to_state_mapping.items():
                    if city in address_lower:
                        state = mapped_state
                        extraction_method = "city_mapping"
                        extraction_stats["city_mapping"] += 1
                        break
            
            # Fallback 2: Try to extract from address parts (last resort)
            if state == "Unknown" and facility.address:
                address_parts = [p.strip() for p in facility.address.split(",")]
                # Only use address parsing if we have 3+ parts (likely has state info)
                if len(address_parts) >= 3:
                    # Check if any part matches a known state name
                    known_states = ["selangor", "johor", "sabah", "sarawak", "perak", "penang",
                                   "kedah", "kelantan", "terengganu", "pahang", "melaka", "malacca",
                                   "negeri sembilan", "perlis", "kuala lumpur", "putrajaya",
                                   "labuan", "singapore"]
                    for part in reversed(address_parts):
                        part_lower = part.lower().strip()
                        if part_lower in known_states:
                            state = normalize_state_name(part)
                            extraction_method = "address_parsing"
                            extraction_stats["address_parsing"] += 1
                            break
            
            if state == "Unknown":
                extraction_stats["unknown"] += 1
            
            
            # Count by state
            if state not in state_counts:
                state_counts[state] = 0
            state_counts[state] += 1
        
        # Convert to list format for frontend, sorted by count descending
        state_data = [
            {"name": state, "facilities": count}
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        
        return state_data
    except Exception as e:
        logger.error(f"Error fetching facilities by state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch facilities by state: {str(e)}")


@router.get("/facilities/{facility_id}")
async def get_facility(
    facility_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single facility by ID
    """
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail=f"Facility with ID {facility_id} not found")
    
    return {
        "id": facility.id,
        "osm_id": facility.osm_id,
        "name": facility.name,
        "type": facility.facility_type,
        "location": {"lat": facility.latitude, "lng": facility.longitude},
        "address": facility.address or "",
        "contact": facility.contact or "",
        "lastUpdated": facility.last_updated_osm.isoformat() if facility.last_updated_osm else "",
        "score": facility.quality_score,
        "osm_tags": facility.osm_tags,
        "created_at": facility.created_at.isoformat(),
        "updated_at": facility.updated_at.isoformat()
    }


@router.get("/health/database")
async def check_database_health(db: Session = Depends(get_db)):
    """
    Check database connection and PostGIS status
    """
    try:
        # Check basic connection
        db.execute(text("SELECT 1"))
        
        # Check PostGIS extension
        postgis_check = db.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis')")).scalar()
        
        if not postgis_check:
            return {
                "connected": True,
                "postgis_enabled": False,
                "status": "warning",
                "message": "Database connected but PostGIS extension not found"
            }
        
        return {
            "connected": True,
            "postgis_enabled": True,
            "status": "healthy",
            "message": "PostGIS Connected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "connected": False,
            "postgis_enabled": False,
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }


@router.get("/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """
    Get analytics data for dashboard including active users and facility stats
    """
    try:
        # Get facility stats directly (reuse logic from get_facility_stats)
        total = db.query(Facility).count()
        hospitals = db.query(Facility).filter(Facility.facility_type == "hospital").count()
        clinics = db.query(Facility).filter(Facility.facility_type == "clinic").count()
        
        avg_score_result = db.query(
            func.avg(Facility.quality_score)
        ).scalar()
        avg_score = round(float(avg_score_result or 0), 2)
        
        stats = {
            "total": total,
            "hospitals": hospitals,
            "clinics": clinics,
            "average_quality_score": avg_score
        }
        
        # Calculate active users from recent ETL job activity
        # Count distinct sources from ETL jobs created in the last 24 hours
        # This is a proxy metric until proper user tracking is implemented
        try:
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            recent_sources = db.query(ETLJob.source).filter(
                ETLJob.created_at >= twenty_four_hours_ago
            ).distinct().count()
            
            # If no recent activity, count distinct sources from all time as fallback
            if recent_sources == 0:
                recent_sources = db.query(ETLJob.source).distinct().count()
            
            active_users_count = recent_sources
        except Exception as e:
            logger.warning(f"Error calculating active users from ETL jobs: {e}")
            active_users_count = 0
        
        return {
            "active_users": active_users_count,
            "facilities": stats
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

