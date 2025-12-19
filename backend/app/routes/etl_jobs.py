"""
ETL Jobs API routes
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.etl_job import ETLJob
from app.models.dosm_dataset import DOSMDataset
from app.models.dataset_version import DatasetVersion
from app.schemas.etl_job import ETLJobCreate, ETLJobResponse, ETLJobStatus
from app.schemas.dosm_dataset import DOSMDatasetResponse
from app.schemas.dosm_record import DatasetVersionResponse
from app.schemas.scraper_config import DatasetDiscoveryRequest, ScrapeRequest
from app.services.dosm_scraper import DOSMScraper
from app.services.dataset_discovery import DatasetDiscovery
from app.services.source_gate import SourceGateError
from app.services.facility_etl import run_facility_etl_job

router = APIRouter()
logger = logging.getLogger(__name__)


def map_to_response(job: ETLJob) -> ETLJobResponse:
    """Map database model to response schema"""
    return ETLJobResponse(
        id=str(job.id),
        source=job.source,
        status=job.status,
        records_processed=job.records_processed,
        start_time=job.start_time.isoformat() if job.start_time else "",
        errors=job.errors
    )


@router.get("/etl-jobs/", response_model=List[ETLJobResponse])
async def get_etl_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all ETL jobs

    Returns a list of all ETL jobs, optionally paginated
    """
    # Validate pagination parameters
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="skip must be non-negative")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="limit must be between 1 and 1000")

    try:
        jobs = db.query(ETLJob).order_by(ETLJob.created_at.desc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(jobs)} ETL jobs with skip={skip}, limit={limit}")
        return [map_to_response(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error retrieving ETL jobs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/etl-jobs/{job_id}", response_model=ETLJobResponse)
async def get_etl_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get a specific ETL job by ID
    """
    try:
        job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ETL job with ID {job_id} not found"
            )
        logger.info(f"Retrieved ETL job with ID {job_id}")
        return map_to_response(job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ETL job with ID {job_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/etl-jobs/", response_model=ETLJobResponse, status_code=status.HTTP_201_CREATED)
async def create_etl_job(
    job_data: ETLJobCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ETL job
    
    Creates a new ETL job with the specified source and status
    """
    # Create new ETL job
    db_job = ETLJob(
        source=job_data.source,
        status=job_data.status or "Pending"
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return map_to_response(db_job)


@router.patch("/etl-jobs/{job_id}", response_model=ETLJobResponse)
async def update_etl_job(
    job_id: int,
    job_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update an ETL job
    
    Updates job status, records_processed, or errors
    """
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ETL job with ID {job_id} not found"
        )
    
    # Update allowed fields
    if "status" in job_data:
        job.status = job_data["status"]
    if "records_processed" in job_data:
        job.records_processed = job_data["records_processed"]
    if "errors" in job_data:
        job.errors = job_data["errors"]
    
    db.commit()
    db.refresh(job)
    
    return map_to_response(job)


@router.delete("/etl-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_etl_job(job_id: int, db: Session = Depends(get_db)):
    """
    Delete an ETL job
    """
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ETL job with ID {job_id} not found"
        )
    
    db.delete(job)
    db.commit()
    
    return None


# ==================== DOSM Scraping Endpoints ====================

@router.post("/etl-jobs/dosm/discover", response_model=List[DOSMDatasetResponse])
async def discover_dosm_datasets(
    request: DatasetDiscoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Discover DOSM datasets from OpenDOSM catalog
    
    Scans the OpenDOSM catalog and identifies health-related datasets.
    Auto-assigns scraping tiers based on available formats.
    """
    try:
        discovery = DatasetDiscovery(db)
        datasets = discovery.discover_and_register(
            category=request.category,
            limit=request.limit,
            auto_assign_tiers=request.auto_assign_tiers
        )
        
        return [DOSMDatasetResponse.model_validate(ds) for ds in datasets]
        
    except Exception as e:
        logger.error(f"Error discovering DOSM datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error discovering datasets: {str(e)}"
        )


@router.get("/etl-jobs/dosm/datasets", response_model=List[DOSMDatasetResponse])
async def list_dosm_datasets(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all discovered DOSM datasets
    """
    try:
        query = db.query(DOSMDataset)
        if is_active is not None:
            query = query.filter(DOSMDataset.is_active == is_active)
        
        datasets = query.order_by(DOSMDataset.created_at.desc()).offset(skip).limit(limit).all()
        return [DOSMDatasetResponse.model_validate(ds) for ds in datasets]
        
    except Exception as e:
        logger.error(f"Error listing DOSM datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing datasets"
        )


@router.get("/etl-jobs/dosm/datasets/{dataset_id}", response_model=DOSMDatasetResponse)
async def get_dosm_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific DOSM dataset by ID
    """
    dataset = db.query(DOSMDataset).filter(DOSMDataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    return DOSMDatasetResponse.model_validate(dataset)


@router.post("/etl-jobs/dosm/scrape/{dataset_id}")
async def trigger_dosm_scrape(
    dataset_id: str,
    request: ScrapeRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger scraping for a specific DOSM dataset
    
    Creates an ETL job record and runs the scraper.
    """
    # Create ETL job record
    etl_job = ETLJob(
        source=f"DOSM_{dataset_id}",
        status=ETLJobStatus.RUNNING
    )
    db.add(etl_job)
    db.commit()
    db.refresh(etl_job)
    
    try:
        # Initialize scraper
        scraper = DOSMScraper(db)
        
        # Run scrape
        result = scraper.scrape(
            dataset_id=dataset_id,
            force=request.force,
            tier_override=request.tier_override
        )
        
        # Update ETL job
        etl_job.status = ETLJobStatus.COMPLETED
        etl_job.records_processed = result.get("records_count", 0)
        etl_job.errors = 0
        db.commit()
        
        return {
            "etl_job_id": etl_job.id,
            "dataset_id": dataset_id,
            "result": result
        }
        
    except SourceGateError as e:
        etl_job.status = ETLJobStatus.FAILED
        etl_job.errors = 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Source gate blocked: {str(e)}"
        )
    except ValueError as e:
        etl_job.status = ETLJobStatus.FAILED
        etl_job.errors = 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        etl_job.status = ETLJobStatus.FAILED
        etl_job.errors = 1
        db.commit()
        logger.error(f"Error scraping dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping dataset: {str(e)}"
        )


@router.get("/etl-jobs/dosm/versions/{dataset_id}", response_model=List[DatasetVersionResponse])
async def get_dataset_versions(
    dataset_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get version history for a dataset
    """
    # Verify dataset exists
    dataset = db.query(DOSMDataset).filter(DOSMDataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    
    versions = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version_number.desc()).limit(limit).all()
    
    return [DatasetVersionResponse.model_validate(v) for v in versions]


# ==================== Overpass Facilities ETL Endpoints ====================

@router.post("/etl-jobs/overpass-facilities")
async def trigger_facility_etl(
    bbox: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger ETL job to fetch and store healthcare facilities from Overpass API
    
    This endpoint:
    1. Creates an ETL job record
    2. Fetches facilities from Overpass API (may take 10-30 seconds)
    3. Stores/updates facilities in the database
    4. Returns job status and statistics
    
    Query parameters:
    - bbox: Optional bounding box as "south,west,north,east". Defaults to Malaysia bounds.
    
    Note: This is a long-running operation. The Overpass API query can take 10-30+ seconds.
    """
    # Parse bounding box if provided
    parsed_bbox = None
    if bbox:
        try:
            coords = [float(x.strip()) for x in bbox.split(",")]
            if len(coords) != 4:
                raise ValueError("Bounding box must have 4 coordinates")
            parsed_bbox = coords
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bounding box format: {str(e)}. Expected: south,west,north,east"
            )
    
    # Create ETL job record
    etl_job = ETLJob(
        source="Overpass_API_Facilities",
        status=ETLJobStatus.RUNNING
    )
    db.add(etl_job)
    db.commit()
    db.refresh(etl_job)
    
    try:
        logger.info(f"Starting facility ETL job {etl_job.id} (bbox: {parsed_bbox})")
        
        # Run ETL job
        result = await run_facility_etl_job(
            db=db,
            bbox=parsed_bbox,
            client_id=f"etl_job_{etl_job.id}"
        )
        
        # Update ETL job with results
        etl_job.status = ETLJobStatus.COMPLETED
        etl_job.records_processed = result.get("stored", 0) + result.get("updated", 0)
        etl_job.errors = result.get("errors", 0)
        db.commit()
        
        logger.info(f"Facility ETL job {etl_job.id} completed successfully")
        
        return {
            "etl_job_id": etl_job.id,
            "status": "completed",
            "result": result,
            "message": f"Successfully processed {result['stored']} new and {result['updated']} updated facilities"
        }
        
    except Exception as e:
        # Update ETL job with error
        etl_job.status = ETLJobStatus.FAILED
        etl_job.errors = 1
        db.commit()
        
        logger.error(f"Facility ETL job {etl_job.id} failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL job failed: {str(e)}"
        )

