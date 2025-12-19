"""
Facility database model
Stores healthcare facilities fetched from Overpass API via ETL
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, func, Index
from sqlalchemy.dialects.postgresql import JSON
from app.database import Base


class Facility(Base):
    """
    Facility model - Stores healthcare facilities (hospitals and clinics)
    fetched from Overpass API and processed via ETL jobs
    """
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "node-12345"
    name = Column(String(255), nullable=False, index=True)
    facility_type = Column(String(50), nullable=False, index=True)  # "hospital" or "clinic"
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(String(500))
    contact = Column(String(100))
    quality_score = Column(Integer, default=0)
    osm_tags = Column(JSON)  # Store full OSM tags as JSON
    last_updated_osm = Column(DateTime(timezone=True))  # Last update time from OSM
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_type_location', 'facility_type', 'latitude', 'longitude'),
        Index('idx_name_search', 'name'),  # For text search
    )

    def __repr__(self):
        return f"<Facility(id={self.id}, osm_id={self.osm_id}, name={self.name}, type={self.facility_type})>"

