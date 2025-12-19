"""
Facility ETL Service
Fetches healthcare facilities from Overpass API and stores them in the database
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.facility import Facility
from app.services.overpass_proxy import get_overpass_service
from app.routes.overpass import build_healthcare_facilities_query, map_osm_to_facility, MALAYSIA_BOUNDS

logger = logging.getLogger(__name__)


async def run_facility_etl_job(
    db: Session,
    bbox: Optional[List[float]] = None,
    client_id: str = "etl_job"
) -> Dict[str, Any]:
    """
    ETL job to fetch facilities from Overpass API and store in database
    
    Args:
        db: Database session
        bbox: Optional bounding box [south, west, north, east]. Defaults to Malaysia bounds
        client_id: Client identifier for rate limiting
        
    Returns:
        Dictionary with stats: stored, updated, total, errors
    """
    try:
        service = get_overpass_service()
        
        # Use provided bbox or default to Malaysia
        bounds = bbox if bbox and len(bbox) == 4 else MALAYSIA_BOUNDS
        
        # Build and execute query
        query = build_healthcare_facilities_query(bounds)
        logger.info(f"Executing Overpass query for ETL job (bbox: {bounds})")
        
        # Fetch from Overpass (don't use cache for ETL jobs - we want fresh data)
        response_data = await service.execute_query(
            query=query,
            client_id=client_id,
            use_cache=False
        )
        
        elements = response_data.get("elements", [])
        logger.info(f"Fetched {len(elements)} elements from Overpass API")
        
        # Process and store facilities
        stored_count = 0
        updated_count = 0
        error_count = 0
        
        for element in elements:
            try:
                facility_osm = map_osm_to_facility(element)
                if not facility_osm:
                    continue
                
                # Check if facility exists by OSM ID
                existing = db.query(Facility).filter(
                    Facility.osm_id == facility_osm.id
                ).first()
                
                # Parse last_updated_osm if available
                last_updated_osm = None
                if facility_osm.lastUpdated:
                    try:
                        # Try to parse ISO format timestamp
                        last_updated_osm = datetime.fromisoformat(facility_osm.lastUpdated.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        pass
                
                if existing:
                    # Update existing facility
                    existing.name = facility_osm.name
                    existing.facility_type = facility_osm.type
                    existing.latitude = facility_osm.location["lat"]
                    existing.longitude = facility_osm.location["lng"]
                    existing.address = facility_osm.address
                    existing.contact = facility_osm.contact
                    existing.quality_score = facility_osm.score
                    existing.osm_tags = facility_osm.osm_tags
                    if last_updated_osm:
                        existing.last_updated_osm = last_updated_osm
                    updated_count += 1
                else:
                    # Create new facility
                    new_facility = Facility(
                        osm_id=facility_osm.id,
                        name=facility_osm.name,
                        facility_type=facility_osm.type,
                        latitude=facility_osm.location["lat"],
                        longitude=facility_osm.location["lng"],
                        address=facility_osm.address,
                        contact=facility_osm.contact,
                        quality_score=facility_osm.score,
                        osm_tags=facility_osm.osm_tags,
                        last_updated_osm=last_updated_osm
                    )
                    db.add(new_facility)
                    stored_count += 1
                    
            except Exception as e:
                error_count += 1
                logger.warning(f"Error processing facility element: {e}")
                continue
        
        # Commit all changes
        db.commit()
        
        result = {
            "stored": stored_count,
            "updated": updated_count,
            "total": len(elements),
            "errors": error_count,
            "bbox": bounds
        }
        
        logger.info(
            f"ETL job completed: stored={stored_count}, updated={updated_count}, "
            f"errors={error_count}, total={len(elements)}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in facility ETL job: {e}")
        db.rollback()
        raise

