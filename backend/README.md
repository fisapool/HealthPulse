# HealthPulse Registry Backend

FastAPI backend for managing ETL jobs and health facility data.

## Features

- **ETL Jobs Management**: Create, read, update, and delete ETL pipeline jobs
- **RESTful API**: Clean REST API with automatic OpenAPI documentation
- **PostgreSQL Database**: Persistent storage with PostGIS support for spatial data
- **Docker Support**: Containerized deployment with Docker Compose

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PostgreSQL**: Relational database with PostGIS extension
- **Uvicorn**: ASGI server for running FastAPI

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use Docker)
- pip

### Local Development Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Initialize database:**
   ```bash
   python init_db.py
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Setup

From the project root, run:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000
- Frontend on port 5173

## API Endpoints

### ETL Jobs

- `GET /api/v1/etl-jobs/` - List all ETL jobs
- `GET /api/v1/etl-jobs/{job_id}` - Get specific ETL job
- `POST /api/v1/etl-jobs/` - Create new ETL job
- `PATCH /api/v1/etl-jobs/{job_id}` - Update ETL job
- `DELETE /api/v1/etl-jobs/{job_id}` - Delete ETL job

### Health Check

- `GET /` - API information
- `GET /health` - Health check endpoint

## Database Schema

### ETL Jobs Table

```sql
CREATE TABLE etl_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    records_processed INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    errors INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://healthpulse:healthpulse@localhost:5432/healthpulse_db` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── etl_job.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   └── etl_job.py
│   └── routes/              # API routes
│       ├── __init__.py
│       └── etl_jobs.py
├── requirements.txt
├── Dockerfile
├── init_db.py
└── README.md
```

### Adding New Endpoints

1. Create model in `app/models/`
2. Create schema in `app/schemas/`
3. Create route in `app/routes/`
4. Include router in `app/main.py`

## Testing

Test the API using curl or the Swagger UI:

```bash
# Create a new ETL job
curl -X POST "http://localhost:8000/api/v1/etl-jobs/" \
  -H "Content-Type: application/json" \
  -d '{"source": "DHIS2", "status": "Pending"}'

# Get all ETL jobs
curl "http://localhost:8000/api/v1/etl-jobs/"
```

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env` file
- Verify database credentials

### Port Already in Use

If port 8000 is already in use, change it in `.env`:
```
API_PORT=8001
```

Then update the frontend `VITE_API_BASE_URL` accordingly.

## License

Same as main project

