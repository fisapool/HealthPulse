"""
ETL Job database model
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class ETLJob(Base):
    """
    ETL Job model representing a data pipeline job
    """
    __tablename__ = "etl_jobs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="Pending", index=True)
    records_processed = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    errors = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ETLJob(id={self.id}, source={self.source}, status={self.status})>"

