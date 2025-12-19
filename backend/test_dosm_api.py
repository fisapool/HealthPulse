"""
Comprehensive test script for DOSM scraping endpoints
Tests the complete DOSM integration workflow
"""
import requests
import json
import time
import sys
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000/api/v1"
API_BASE = "http://localhost:8000"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(success: bool, message: str, data: Optional[Dict[Any, Any]] = None):
    """Print a formatted test result"""
    status = "✅" if success else "❌"
    print(f"{status} {message}")
    if data:
        print(f"   Response: {json.dumps(data, indent=2)}")

def test_health_check():
    """Test API health check"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print_result(True, f"API is healthy: {response.json()}")
            return True
        else:
            print_result(False, f"Health check returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to API. Is the server running?")
        print("   Start the server with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"Health check failed: {e}")
        return False

def test_discover_datasets(category: str = "health", limit: int = 5):
    """Test dataset discovery endpoint"""
    print_section("2. Dataset Discovery")
    try:
        payload = {
            "category": category,
            "limit": limit,
            "auto_assign_tiers": True
        }
        print(f"   Request: POST /etl-jobs/dosm/discover")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/etl-jobs/dosm/discover",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # Discovery can take time
        )
        
        if response.status_code == 200:
            datasets = response.json()
            print_result(True, f"Discovered {len(datasets)} datasets")
            
            if datasets:
                print("\n   Sample dataset:")
                sample = datasets[0]
                print(f"   - ID: {sample.get('dataset_id')}")
                print(f"   - Title: {sample.get('title', 'N/A')}")
                print(f"   - Tier: {sample.get('scraping_tier', 'N/A')}")
                print(f"   - Category: {sample.get('category', 'N/A')}")
                return datasets
            else:
                print("   ⚠️  No datasets discovered. This might be normal if no health datasets exist.")
                return []
        else:
            print_result(False, f"Discovery failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Discovery error: {e}")
        return None

def test_list_datasets(limit: int = 10):
    """Test listing all discovered datasets"""
    print_section("3. List All Datasets")
    try:
        response = requests.get(
            f"{BASE_URL}/etl-jobs/dosm/datasets",
            params={"limit": limit, "is_active": True},
            timeout=30
        )
        
        if response.status_code == 200:
            datasets = response.json()
            print_result(True, f"Found {len(datasets)} registered datasets")
            
            if datasets:
                print("\n   Registered datasets:")
                for i, ds in enumerate(datasets[:5], 1):  # Show first 5
                    print(f"   {i}. {ds.get('dataset_id')} - {ds.get('title', 'N/A')[:50]}")
                if len(datasets) > 5:
                    print(f"   ... and {len(datasets) - 5} more")
            
            return datasets
        else:
            print_result(False, f"List failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"List error: {e}")
        return None

def test_get_dataset(dataset_id: str):
    """Test getting a specific dataset"""
    print_section(f"4. Get Dataset Details: {dataset_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/etl-jobs/dosm/datasets/{dataset_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            dataset = response.json()
            print_result(True, f"Retrieved dataset: {dataset.get('title', 'N/A')}")
            print(f"   - Dataset ID: {dataset.get('dataset_id')}")
            print(f"   - Scraping Tier: {dataset.get('scraping_tier')}")
            print(f"   - Source URL: {dataset.get('source_url', 'N/A')}")
            print(f"   - Is Active: {dataset.get('is_active')}")
            return dataset
        elif response.status_code == 404:
            print_result(False, f"Dataset {dataset_id} not found")
            return None
        else:
            print_result(False, f"Get failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Get error: {e}")
        return None

def test_scrape_dataset(dataset_id: str, force: bool = False, tier_override: Optional[int] = None):
    """Test scraping a specific dataset"""
    print_section(f"5. Scrape Dataset: {dataset_id}")
    try:
        payload = {
            "force": force
        }
        if tier_override:
            payload["tier_override"] = tier_override
        
        print(f"   Request: POST /etl-jobs/dosm/scrape/{dataset_id}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        print("   ⏳ This may take a while depending on the dataset size and tier...")
        
        response = requests.post(
            f"{BASE_URL}/etl-jobs/dosm/scrape/{dataset_id}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # Scraping can take time
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, "Scraping completed successfully")
            print(f"   - ETL Job ID: {result.get('etl_job_id')}")
            
            scrape_result = result.get('result', {})
            print(f"   - Records Count: {scrape_result.get('records_count', 0)}")
            print(f"   - Tier Used: {scrape_result.get('tier_used', 'N/A')}")
            print(f"   - Status: {scrape_result.get('status', 'N/A')}")
            
            if scrape_result.get('warnings'):
                print(f"   - Warnings: {len(scrape_result.get('warnings', []))}")
            
            return result
        elif response.status_code == 403:
            print_result(False, "Scraping blocked by source gate")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
            return None
        elif response.status_code == 404:
            print_result(False, f"Dataset {dataset_id} not found")
            return None
        else:
            print_result(False, f"Scraping failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print_result(False, "Scraping timed out (exceeded 5 minutes)")
        print("   This might be normal for large datasets or browser automation")
        return None
    except Exception as e:
        print_result(False, f"Scraping error: {e}")
        return None

def test_get_versions(dataset_id: str, limit: int = 5):
    """Test getting version history for a dataset"""
    print_section(f"6. Version History: {dataset_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/etl-jobs/dosm/versions/{dataset_id}",
            params={"limit": limit},
            timeout=30
        )
        
        if response.status_code == 200:
            versions = response.json()
            print_result(True, f"Found {len(versions)} version(s)")
            
            if versions:
                print("\n   Version history:")
                for v in versions:
                    print(f"   - Version {v.get('version_number')}: {v.get('created_at', 'N/A')}")
                    print(f"     Records: {v.get('record_count', 0)}, Hash: {v.get('file_hash', 'N/A')[:16]}...")
            
            return versions
        elif response.status_code == 404:
            print_result(False, f"Dataset {dataset_id} not found")
            return None
        else:
            print_result(False, f"Get versions failed: {response.status_code}")
            return None
            
    except Exception as e:
        print_result(False, f"Get versions error: {e}")
        return None

def main():
    """Run all DOSM API tests"""
    print("\n" + "=" * 70)
    print("  DOSM Scraping API Test Suite")
    print("=" * 70)
    print("\nThis script tests the complete DOSM integration workflow:")
    print("  1. Health check")
    print("  2. Dataset discovery")
    print("  3. List datasets")
    print("  4. Get dataset details")
    print("  5. Scrape dataset")
    print("  6. Version history")
    
    # Step 1: Health check
    if not test_health_check():
        print("\n❌ API is not available. Please start the server first:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Step 2: Discover datasets
    datasets = test_discover_datasets(category="health", limit=5)
    if datasets is None:
        print("\n⚠️  Discovery failed. Continuing with other tests...")
        datasets = []
    
    # Step 3: List all datasets
    all_datasets = test_list_datasets(limit=10)
    if all_datasets is None:
        all_datasets = []
    
    # If we have datasets, test individual operations
    if all_datasets:
        # Use the first dataset for detailed tests
        test_dataset = all_datasets[0]
        dataset_id = test_dataset.get('dataset_id')
        
        if dataset_id:
            # Step 4: Get dataset details
            test_get_dataset(dataset_id)
            
            # Step 5: Scrape dataset (optional - can be slow)
            print("\n" + "=" * 70)
            user_input = input("  Do you want to test scraping? This may take several minutes (y/n): ").strip().lower()
            if user_input == 'y':
                test_scrape_dataset(dataset_id, force=False)
            else:
                print("   Skipping scrape test")
            
            # Step 6: Get version history
            test_get_versions(dataset_id, limit=5)
    else:
        print("\n⚠️  No datasets available for detailed testing.")
        print("   You can manually test scraping with:")
        print("   curl -X POST 'http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}' \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"force\": false}'")
    
    # Summary
    print_section("Test Summary")
    print("✅ Basic API tests completed")
    print("\nNext steps:")
    print("  1. Check the API documentation at: http://localhost:8000/docs")
    print("  2. Review discovered datasets in the database")
    print("  3. Test scraping with specific dataset IDs")
    print("  4. Monitor ETL jobs via: GET /api/v1/etl-jobs/")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

