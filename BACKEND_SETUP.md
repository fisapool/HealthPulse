# Backend Setup Guide

This guide will help you set up and run the HealthPulse Registry backend.

## What Was Created

The backend component includes:

### Core Application
- **FastAPI application** (`backend/app/main.py`) - Main API server
- **Database models** (`backend/app/models/`) - SQLAlchemy models for ETL jobs
- **API routes** (`backend/app/routes/`) - REST endpoints for ETL job management
- **Pydantic schemas** (`backend/app/schemas/`) - Request/response validation

### Configuration Files
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `env.example` - Environment variables template
- `.gitignore` - Git ignore rules

### Scripts
- `init_db.py` - Database initialization
- `test_api.py` - API testing script
- `run.sh` / `run.bat` - Startup scripts

### Documentation
- `backend/README.md` - Detailed backend documentation

## Quick Start

### Using Docker Compose (Easiest)

From the project root:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Backend API (port 8000)
- Frontend (port 3000)

### Manual Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL:**
   - Install PostgreSQL 14+ with PostGIS extension
   - Create database: `createdb healthpulse_db`
   - Or use Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=healthpulse postgis/postgis:16-3.4`

3. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your database URL
   ```

4. **Initialize database:**
   ```bash
   python init_db.py
   ```

5. **Start server:**
   ```bash
   # Linux/Mac
   ./run.sh
   
   # Windows
   run.bat
   
   # Or directly
   uvicorn app.main:app --reload
   ```

## API Endpoints

Once running, access:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **ETL Jobs**: http://localhost:8000/api/v1/etl-jobs/

### API Reference

The backend provides RESTful APIs for ETL jobs, Overpass proxy, and data management.

#### ETL Jobs Endpoints

- `GET /api/v1/etl-jobs/` - List all ETL jobs
- `POST /api/v1/etl-jobs/` - Create a new ETL job
- `GET /api/v1/etl-jobs/{id}` - Get job details
- `PUT /api/v1/etl-jobs/{id}` - Update job
- `DELETE /api/v1/etl-jobs/{id}` - Delete job

#### Overpass Proxy Endpoints

- `GET /api/v1/overpass/facilities` - Query facilities via backend proxy

For full API documentation, visit http://localhost:8000/docs.

## Testing

Test the API:

```bash
cd backend
python test_api.py
```

Or use curl:

```bash
# Create a job
curl -X POST "http://localhost:8000/api/v1/etl-jobs/" \
  -H "Content-Type: application/json" \
  -d '{"source": "DHIS2", "status": "Pending"}'

# Get all jobs
curl "http://localhost:8000/api/v1/etl-jobs/"
```

## Integration with Frontend

The frontend is already configured to connect to the backend:

- Frontend expects backend at: `http://localhost:8000/api/v1`
- Configured via: `VITE_API_BASE_URL` environment variable
- The ETL Pipeline component will automatically connect when backend is running

## Troubleshooting

### Database Connection Error

- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env` file
- Verify database exists: `psql -U healthpulse -d healthpulse_db`

### Port Already in Use

- Change port in `.env`: `API_PORT=8001`
- Update frontend `VITE_API_BASE_URL` accordingly

### Module Not Found

- Ensure you're in the `backend` directory
- Install dependencies: `pip install -r requirements.txt`
- Activate virtual environment if using one

## Next Steps

1. **Add Background Jobs**: Implement async ETL processing with Celery
2. **Add Facility Caching**: Store Overpass API results in database
3. **Add Authentication**: Secure API endpoints
4. **Add WebSockets**: Real-time job status updates
5. **Add Gemini Integration**: Move AI deduplication to backend

## Support

See `backend/README.md` for detailed documentation.

