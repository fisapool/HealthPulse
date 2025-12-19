from app.schemas.etl_job import ETLJobCreate, ETLJobResponse
from app.schemas.dosm_dataset import (
    DOSMDatasetCreate,
    DOSMDatasetUpdate,
    DOSMDatasetResponse
)
from app.schemas.dosm_record import (
    RecordMetadata,
    DOSMRecordCreate,
    DOSMRecordResponse,
    DatasetVersionResponse
)
from app.schemas.scraper_config import (
    ScraperConfig,
    DatasetDiscoveryRequest,
    ScrapeRequest
)

__all__ = [
    "ETLJobCreate",
    "ETLJobResponse",
    "DOSMDatasetCreate",
    "DOSMDatasetUpdate",
    "DOSMDatasetResponse",
    "RecordMetadata",
    "DOSMRecordCreate",
    "DOSMRecordResponse",
    "DatasetVersionResponse",
    "ScraperConfig",
    "DatasetDiscoveryRequest",
    "ScrapeRequest"
]

