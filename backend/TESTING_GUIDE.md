# DOSM Scraping Testing Guide

This guide walks you through testing the complete DOSM integration system.

## Prerequisites

1. **PostgreSQL Database**: Ensure PostgreSQL is running and accessible
2. **Python Environment**: Python 3.11+ with pip
3. **Environment Variables**: Configure `.env` file (see `env.example`)

## Quick Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note**: If you plan to test browser automation (Tier 5), you'll also need to install Playwright browsers:

```bash
playwright install chromium
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/healthpulse_db
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
```

### 3. Initialize Database

Create all required tables:

```bash
python init_db.py
```

Expected output:
```
Creating database tables...
Database tables created successfully!
Created tables:
  - etl_jobs
  - dosm_datasets
  - dosm_records
  - dataset_versions
```

### 4. Start the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing Workflow

### Option 1: Automated Test Script

Run the comprehensive test script:

```bash
python test_dosm_api.py
```

This script will:
1. ✅ Check API health
2. 🔍 Discover DOSM datasets
3. 📋 List all registered datasets
4. 📊 Get dataset details
5. 🕷️ Test scraping (with user confirmation)
6. 📜 Check version history

### Option 2: Manual Testing via API

#### Step 1: Discover Datasets

Discover health-related datasets from OpenDOSM:

```bash
curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "health",
    "limit": 10,
    "auto_assign_tiers": true
  }'
```

**Expected Response**: Array of discovered datasets with metadata:
```json
[
  {
    "dataset_id": "health-statistics-2023",
    "title": "Health Statistics 2023",
    "category": "health",
    "scraping_tier": "tier1_opendosm",
    "source_url": "https://open.dosm.gov.my/...",
    "is_active": true
  }
]
```

#### Step 2: List All Datasets

Get all registered datasets:

```bash
curl "http://localhost:8000/api/v1/etl-jobs/dosm/datasets?limit=10&is_active=true"
```

#### Step 3: Get Dataset Details

Get specific dataset information:

```bash
curl "http://localhost:8000/api/v1/etl-jobs/dosm/datasets/{dataset_id}"
```

Replace `{dataset_id}` with an actual dataset ID from discovery.

#### Step 4: Scrape a Dataset

Trigger scraping for a specific dataset:

```bash
curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "force": false,
    "tier_override": null
  }'
```

**Parameters**:
- `force`: If `true`, re-scrapes even if data hasn't changed
- `tier_override`: Optional tier number (1-5) to force a specific scraper

**Expected Response**:
```json
{
  "etl_job_id": 1,
  "dataset_id": "health-statistics-2023",
  "result": {
    "status": "success",
    "records_count": 150,
    "tier_used": "tier1_opendosm",
    "warnings": []
  }
}
```

#### Step 5: Check Version History

View version history for a dataset:

```bash
curl "http://localhost:8000/api/v1/etl-jobs/dosm/versions/{dataset_id}?limit=5"
```

### Option 3: Using Swagger UI

1. Open http://localhost:8000/docs in your browser
2. Navigate to the "ETL Jobs" section
3. Expand the DOSM endpoints:
   - `POST /api/v1/etl-jobs/dosm/discover`
   - `GET /api/v1/etl-jobs/dosm/datasets`
   - `GET /api/v1/etl-jobs/dosm/datasets/{dataset_id}`
   - `POST /api/v1/etl-jobs/dosm/scrape/{dataset_id}`
   - `GET /api/v1/etl-jobs/dosm/versions/{dataset_id}`
4. Click "Try it out" and fill in the parameters
5. Click "Execute" to test

## Testing Different Scraping Tiers

The system automatically selects the safest available tier. You can test specific tiers:

### Tier 1: OpenDOSM API (Safest)
```bash
curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}" \
  -H "Content-Type: application/json" \
  -d '{"tier_override": 1}'
```

### Tier 2: Direct Download (CSV/Excel)
```bash
curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}" \
  -H "Content-Type: application/json" \
  -d '{"tier_override": 2}'
```

### Tier 3: PDF Extraction
```bash
curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}" \
  -H "Content-Type: application/json" \
  -d '{"tier_override": 3}'
```

### Tier 4: HTML Parsing
```bash
curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}" \
  -H "Content-Type: application/json" \
  -d '{"tier_override": 4}'
```

### Tier 5: Browser Automation (Requires Configuration)

**⚠️ Warning**: Tier 5 is disabled by default. To enable:

1. Set environment variable:
   ```bash
   export DOSM_ENABLE_BROWSER_AUTOMATION=true
   ```

2. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

3. Test with tier override:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/etl-jobs/dosm/scrape/{dataset_id}" \
     -H "Content-Type: application/json" \
     -d '{"tier_override": 5}'
   ```

## Monitoring ETL Jobs

Check the status of all ETL jobs:

```bash
curl "http://localhost:8000/api/v1/etl-jobs/"
```

Get a specific ETL job:

```bash
curl "http://localhost:8000/api/v1/etl-jobs/{job_id}"
```

## Common Issues and Troubleshooting

### Issue: "Cannot connect to database"

**Solution**:
1. Verify PostgreSQL is running: `pg_isready` or check service status
2. Check `DATABASE_URL` in `.env` file
3. Ensure database exists: `createdb healthpulse_db` (if needed)
4. Verify credentials match your PostgreSQL setup

### Issue: "Source gate blocked"

**Solution**: This means the source URL is not whitelisted. Check:
- The URL is from an official DOSM domain
- The source gate service is properly configured
- See `backend/app/services/source_gate.py` for whitelist

### Issue: "Dataset not found"

**Solution**:
1. Run discovery first: `POST /api/v1/etl-jobs/dosm/discover`
2. Check the dataset ID is correct
3. Verify the dataset exists in the database

### Issue: "Scraping timeout"

**Solution**:
- Large datasets or browser automation can take time
- Increase timeout in your HTTP client
- Check server logs for progress
- Consider testing with smaller datasets first

### Issue: "Playwright not found" (Tier 5)

**Solution**:
```bash
pip install playwright
playwright install chromium
```

## Expected Test Results

### Successful Discovery
- Returns array of datasets
- Each dataset has `dataset_id`, `title`, `scraping_tier`
- Datasets are registered in database

### Successful Scraping
- Returns ETL job ID
- `records_count` > 0
- `status` is "success"
- New version created in `dataset_versions` table

### Version Tracking
- Each scrape creates a new version
- Versions include file hash and schema fingerprint
- Can detect when data has changed

## Next Steps After Testing

1. **Review Discovered Datasets**: Check what datasets were found
2. **Test Different Categories**: Try different categories beyond "health"
3. **Monitor Performance**: Check scraping times for different tiers
4. **Verify Data Quality**: Inspect scraped records in database
5. **Test Error Handling**: Try invalid dataset IDs, network failures, etc.

## Database Inspection

To inspect scraped data directly:

```bash
# Connect to PostgreSQL
psql -U healthpulse -d healthpulse_db

# View discovered datasets
SELECT dataset_id, title, scraping_tier, is_active FROM dosm_datasets;

# View scraped records
SELECT COUNT(*) FROM dosm_records;
SELECT * FROM dosm_records LIMIT 10;

# View version history
SELECT dataset_id, version_number, record_count, created_at 
FROM dataset_versions 
ORDER BY created_at DESC;
```

## Performance Benchmarks

Expected performance by tier:
- **Tier 1 (API)**: < 5 seconds for typical datasets
- **Tier 2 (Direct Download)**: 5-30 seconds depending on file size
- **Tier 3 (PDF)**: 30-120 seconds for typical PDFs
- **Tier 4 (HTML)**: 10-60 seconds depending on page complexity
- **Tier 5 (Browser)**: 60-300+ seconds (slowest, use as last resort)

## Support

For issues or questions:
1. Check server logs for detailed error messages
2. Review API documentation at `/docs`
3. Check database for data integrity
4. Verify all dependencies are installed correctly

