"""
DOSM Record database model
Stores scraped records with mandatory metadata block
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func, Index
from sqlalchemy.orm import relationship
from app.database import Base


class DOSMRecord(Base):
    """
    DOSM Record model - Stores individual scraped records with mandatory metadata
    """
    __tablename__ = "dosm_records"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(255), ForeignKey("dosm_datasets.dataset_id"), nullable=False, index=True)
    
    # Data fields stored as JSON (flexible schema)
    data = Column(JSON, nullable=False)
    
    # Mandatory metadata block
    record_metadata = Column(JSON, nullable=False)
    # record_metadata structure:
    # {
    #   "source": "DOSM",
    #   "dataset_id": "...",
    #   "source_url": "...",
    #   "file_type": "api|csv|xlsx|pdf|html",
    #   "published_date": "ISO datetime or null",
    #   "retrieved_at": "ISO datetime",
    #   "scrape_method": "opendosm_api|direct_download|pdf_extraction|html_parsing|browser_automation",
    #   "confidence": "high|medium|low"
    # }
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    dataset = relationship("DOSMDataset", back_populates="records")

    # Index for efficient queries
    __table_args__ = (
        Index('idx_dataset_created', 'dataset_id', 'created_at'),
    )

    def __repr__(self):
        return f"<DOSMRecord(id={self.id}, dataset_id={self.dataset_id}, created_at={self.created_at})>"

