"""
Simple test script to verify backend API is working
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_get_etl_jobs():
    """Test getting all ETL jobs"""
    print("\nTesting GET /etl-jobs/...")
    try:
        response = requests.get(f"{BASE_URL}/etl-jobs/")
        print(f"✅ GET /etl-jobs/: {response.status_code}")
        jobs = response.json()
        print(f"   Found {len(jobs)} jobs")
        if jobs:
            print(f"   First job: {json.dumps(jobs[0], indent=2)}")
        return True
    except Exception as e:
        print(f"❌ GET /etl-jobs/ failed: {e}")
        return False

def test_create_etl_job():
    """Test creating a new ETL job"""
    print("\nTesting POST /etl-jobs/...")
    try:
        data = {
            "source": "DHIS2",
            "status": "Pending"
        }
        response = requests.post(
            f"{BASE_URL}/etl-jobs/",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ POST /etl-jobs/: {response.status_code}")
        job = response.json()
        print(f"   Created job: {json.dumps(job, indent=2)}")
        return job.get("id")
    except Exception as e:
        print(f"❌ POST /etl-jobs/ failed: {e}")
        return None

def test_get_single_job(job_id):
    """Test getting a single ETL job"""
    print(f"\nTesting GET /etl-jobs/{job_id}...")
    try:
        response = requests.get(f"{BASE_URL}/etl-jobs/{job_id}")
        print(f"✅ GET /etl-jobs/{job_id}: {response.status_code}")
        job = response.json()
        print(f"   Job: {json.dumps(job, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ GET /etl-jobs/{job_id} failed: {e}")
        return False

def main():
    print("=" * 50)
    print("HealthPulse Registry Backend API Test")
    print("=" * 50)
    
    # Test health check
    if not test_health():
        print("\n❌ Backend is not running. Please start it first.")
        return
    
    # Test getting jobs (should be empty initially)
    test_get_etl_jobs()
    
    # Test creating a job
    job_id = test_create_etl_job()
    
    # Test getting the created job
    if job_id:
        test_get_single_job(job_id)
    
    # Test getting all jobs again
    test_get_etl_jobs()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()

