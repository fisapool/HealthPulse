"""
Facilities API routes
Query facilities from database (fast) instead of Overpass API (slow)
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.database import get_db
from app.models.facility import Facility

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

