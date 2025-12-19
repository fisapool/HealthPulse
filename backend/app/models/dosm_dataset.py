"""
DOSM Dataset database model
Tracks discovered datasets and their scraping configuration
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ScrapeTier(str, enum.Enum):
    """Enum for scraping tier levels"""
    TIER1_OPENDOSM = "tier1_opendosm"
    TIER2_DIRECT_DOWNLOAD = "tier2_direct_download"
    TIER3_PDF_EXTRACTION = "tier3_pdf_extraction"
    TIER4_HTML_PARSING = "tier4_html_parsing"
    TIER5_BROWSER_AUTOMATION = "tier5_browser_automation"


class DOSMDataset(Base):
    """
    DOSM Dataset model - Registry of discovered datasets
    """
    __tablename__ = "dosm_datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(String(2000), nullable=True)
    source_url = Column(String(1000), nullable=False)
    tier = Column(SQLEnum(ScrapeTier), nullable=False, index=True)
    scrape_method = Column(String(100), nullable=False)
    update_frequency = Column(String(50), nullable=True)  # e.g., "monthly", "quarterly", "annually"
    last_checked = Column(DateTime(timezone=True), nullable=True)
    last_successful_scrape = Column(DateTime(timezone=True), nullable=True)
    is_statistical = Column(Boolean, default=True, nullable=False)  # DOSM is statistical reference
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    confidence = Column(String(20), nullable=False, default="high")  # "high", "medium", "low"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")
    records = relationship("DOSMRecord", back_populates="dataset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DOSMDataset(id={self.id}, dataset_id={self.dataset_id}, tier={self.tier})>"

