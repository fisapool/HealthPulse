"""
Dataset Version tracking model
Tracks file versions, hashes, and schema fingerprints to prevent duplicate scraping
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from app.database import Base


class DatasetVersion(Base):
    """
    Dataset Version model - Tracks versions of scraped datasets
    """
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(255), ForeignKey("dosm_datasets.dataset_id"), nullable=False, index=True)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    schema_fingerprint = Column(String(255), nullable=True)  # JSON schema fingerprint
    version_number = Column(Integer, nullable=False, default=1)
    record_count = Column(Integer, nullable=False, default=0)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    dataset = relationship("DOSMDataset", back_populates="versions")

    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_dataset_hash', 'dataset_id', 'file_hash'),
    )

    def __repr__(self):
        return f"<DatasetVersion(id={self.id}, dataset_id={self.dataset_id}, version={self.version_number}, hash={self.file_hash[:8]}...)>"

