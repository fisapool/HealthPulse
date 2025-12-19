"""
Database initialization script
Creates database tables if they don't exist
"""
from app.database import engine, Base
from app.models import ETLJob, DOSMDataset, DOSMRecord, DatasetVersion, Facility

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("Created tables:")
    print("  - etl_jobs")
    print("  - dosm_datasets")
    print("  - dosm_records")
    print("  - dataset_versions")
    print("  - facilities")

