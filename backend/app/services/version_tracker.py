"""
Version Tracker - Tracks dataset versions using file hashes and schema fingerprints
Prevents duplicate scraping and tracks data changes
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.dataset_version import DatasetVersion
from app.models.dosm_dataset import DOSMDataset

logger = logging.getLogger(__name__)


def calculate_file_hash(content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content
    
    Args:
        content: File content as bytes
        
    Returns:
        SHA-256 hash as hex string
    """
    return hashlib.sha256(content).hexdigest()


def calculate_schema_fingerprint(records: List[Dict[str, Any]]) -> str:
    """
    Calculate schema fingerprint from a list of records
    Creates a fingerprint based on field names and types
    
    Args:
        records: List of record dictionaries
        
    Returns:
        Schema fingerprint as string
    """
    if not records:
        return "empty"
    
    # Get all unique keys from all records
    all_keys = set()
    for record in records:
        if isinstance(record, dict):
            all_keys.update(record.keys())
    
    # Sort keys for consistent fingerprint
    sorted_keys = sorted(all_keys)
    
    # Get sample types for each key (from first record that has the key)
    schema_info = {}
    for key in sorted_keys:
        for record in records:
            if isinstance(record, dict) and key in record:
                value = record[key]
                if value is None:
                    schema_info[key] = "null"
                elif isinstance(value, bool):
                    schema_info[key] = "bool"
                elif isinstance(value, int):
                    schema_info[key] = "int"
                elif isinstance(value, float):
                    schema_info[key] = "float"
                elif isinstance(value, str):
                    schema_info[key] = "string"
                elif isinstance(value, list):
                    schema_info[key] = "array"
                elif isinstance(value, dict):
                    schema_info[key] = "object"
                else:
                    schema_info[key] = type(value).__name__
                break
    
    # Create fingerprint JSON and hash it
    fingerprint_data = json.dumps(schema_info, sort_keys=True)
    fingerprint_hash = hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    return fingerprint_hash


def check_version_exists(
    db: Session,
    dataset_id: str,
    file_hash: str
) -> Optional[DatasetVersion]:
    """
    Check if a version with the given hash already exists
    
    Args:
        db: Database session
        dataset_id: Dataset identifier
        file_hash: File hash to check
        
    Returns:
        DatasetVersion if exists, None otherwise
    """
    return db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.file_hash == file_hash
    ).first()


def get_latest_version(
    db: Session,
    dataset_id: str
) -> Optional[DatasetVersion]:
    """
    Get the latest version for a dataset
    
    Args:
        db: Database session
        dataset_id: Dataset identifier
        
    Returns:
        Latest DatasetVersion or None
    """
    return db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version_number.desc()).first()


def create_version(
    db: Session,
    dataset_id: str,
    file_hash: str,
    schema_fingerprint: Optional[str],
    record_count: int,
    file_size: Optional[int] = None
) -> DatasetVersion:
    """
    Create a new dataset version
    
    Args:
        db: Database session
        dataset_id: Dataset identifier
        file_hash: File content hash
        schema_fingerprint: Schema fingerprint
        record_count: Number of records
        file_size: File size in bytes (optional)
        
    Returns:
        Created DatasetVersion
    """
    # Get next version number
    latest = get_latest_version(db, dataset_id)
    next_version = (latest.version_number + 1) if latest else 1
    
    version = DatasetVersion(
        dataset_id=dataset_id,
        file_hash=file_hash,
        schema_fingerprint=schema_fingerprint,
        version_number=next_version,
        record_count=record_count,
        file_size=file_size,
        retrieved_at=datetime.utcnow()
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    logger.info(
        f"Created new version for dataset {dataset_id}: "
        f"version={next_version}, hash={file_hash[:8]}..., records={record_count}"
    )
    
    return version


def is_duplicate_version(
    db: Session,
    dataset_id: str,
    file_hash: str
) -> bool:
    """
    Check if a version with this hash already exists (duplicate)
    
    Args:
        db: Database session
        dataset_id: Dataset identifier
        file_hash: File hash to check
        
    Returns:
        True if duplicate exists
    """
    existing = check_version_exists(db, dataset_id, file_hash)
    return existing is not None


def track_dataset_version(
    db: Session,
    dataset_id: str,
    content: bytes,
    records: List[Dict[str, Any]],
    force: bool = False
) -> Tuple[bool, Optional[DatasetVersion]]:
    """
    Track a dataset version, checking for duplicates
    
    Args:
        db: Database session
        dataset_id: Dataset identifier
        content: File content as bytes
        records: Parsed records
        force: Force creation even if duplicate exists
        
    Returns:
        Tuple of (is_new_version, DatasetVersion or None)
    """
    file_hash = calculate_file_hash(content)
    schema_fingerprint = calculate_schema_fingerprint(records) if records else None
    
    # Check if this version already exists
    if not force and is_duplicate_version(db, dataset_id, file_hash):
        logger.info(
            f"Duplicate version detected for dataset {dataset_id}: "
            f"hash={file_hash[:8]}... (skipping)"
        )
        existing = check_version_exists(db, dataset_id, file_hash)
        return False, existing
    
    # Create new version
    version = create_version(
        db=db,
        dataset_id=dataset_id,
        file_hash=file_hash,
        schema_fingerprint=schema_fingerprint,
        record_count=len(records),
        file_size=len(content)
    )
    
    return True, version

