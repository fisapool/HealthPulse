# HealthPulse Registry – Onboarding Documentation

## Project Overview

The HealthPulse Registry is a comprehensive full-stack web application designed to manage and analyze health facility data in Malaysia. It aggregates geospatial data from OpenStreetMap via the public Overpass API, provides an interactive dashboard for real-time analytics, and includes a robust ETL (Extract, Transform, Load) pipeline for data ingestion from various sources, such as the Department of Statistics Malaysia (DOSM). The application focuses on hospitals and clinics, enabling data-driven insights for healthcare planning and management.

## Key Features

- **Interactive Dashboard**: Real-time analytics with map view, registry table, and ETL monitoring.
- **ETL Pipeline**: Automated data ingestion from DOSM with version tracking, metadata enrichment, and tiered scraping strategies.
- **Geospatial Capabilities**: Integration with public Overpass API for accurate geospatial data from OpenStreetMap.
- **Scraping Strategies**: Multi-tiered approaches using requests, pandas, pdfplumber, BeautifulSoup, and Playwright for diverse data sources.
- **AI-Powered Deduplication**: Integration with Google Gemini for intelligent duplicate detection and data cleaning.
- **Containerized Deployment**: Full Docker and Docker Compose support for easy setup and scalability.
- **Optional Caching**: Redis integration for improved performance.
- **Modular Architecture**: Clean separation of frontend, backend, and services for maintainability.

## Screenshots

### Dashboard Overview
![Dashboard Overview](Screenshot/Screenshot%202025-12-20%20041116.png)

### Interactive Map View
![Map View](Screenshot/Screenshot%202025-12-20%20041137.png)

### Registry Table
![Registry Table](Screenshot/Screenshot%202025-12-20%20041147.png)

### ETL Pipeline Management
![ETL Pipeline](Screenshot/Screenshot%202025-12-20%20041157.png)

## Architecture

The application follows a modular, microservices-inspired architecture:

- **Frontend**: Built with React 18, TypeScript, Vite, and Tailwind CSS for a responsive, interactive user interface.
- **Backend**: Developed using Python 3.11, FastAPI, SQLAlchemy, and Pydantic for high-performance API services.
- **Database**: PostgreSQL with PostGIS extension for geospatial data storage and querying.
- **Geospatial Services**: Public Overpass API for querying OpenStreetMap data.
- **ETL Services**: Dedicated services for data extraction, transformation, and loading with tiered scraping.
- **Caching Layer**: Optional Redis for caching API responses and improving performance.
- **AI Integration**: Google Gemini for advanced data processing tasks like deduplication.

Data flows from external sources (e.g., DOSM, OpenStreetMap) through the ETL pipeline into the database, where it's served via the backend API to the frontend for visualization and analysis.

## Tech Stack

- **Frontend**:
  - React 18 (UI framework)
  - TypeScript (type safety)
  - Vite (build tool)
  - Tailwind CSS (styling)
  - Leaflet or similar for map rendering

- **Backend**:
  - Python 3.11 (runtime)
  - FastAPI (web framework)
  - SQLAlchemy (ORM)
  - Pydantic (data validation)
  - Uvicorn (ASGI server)

- **Database**:
  - PostgreSQL (relational database)
  - PostGIS (geospatial extension)

- **Geospatial**:
  - Overpass API (public API for querying OpenStreetMap)
  - OpenStreetMap (data source)

- **Scraping & ETL**:
  - requests (HTTP client)
  - pandas (data manipulation)
  - pdfplumber (PDF parsing)
  - BeautifulSoup (HTML parsing)
  - Playwright (browser automation)

- **AI & ML**:
  - Google Gemini (deduplication and analysis)

- **Infrastructure**:
  - Docker & Docker Compose (containerization)
  - Redis (caching, optional)

- **Development Tools**:
  - Git (version control)
  - Pre-commit hooks (code quality)
  - Testing frameworks (pytest for backend, Jest for frontend)

## Quick Start

### Docker (Recommended)

1. **Prerequisites**: Ensure Docker and Docker Compose are installed on your system.

2. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd healthpulse-registry
   ```

3. **Start Services**:
   ```bash
   docker-compose up -d
   ```
   This command starts:
   - PostgreSQL database (port 5434)
   - Backend API (port 8002)
   - Frontend (port 3001)

4. **Access the Application**:
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8002
   - API Docs: http://localhost:8002/docs

### Local Development

#### Frontend Setup

1. **Prerequisites**: Node.js 18+ and npm.

2. **Install Dependencies**:
   ```bash
   npm install
   ```


3. **Configure Environment**:
   Create a `.env.local` file:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run Development Server**:
   ```bash
   npm run dev
   ```
   Access at http://localhost:5173.

#### Backend Setup

1. **Prerequisites**: Python 3.11+, PostgreSQL 14+ with PostGIS.

2. **Navigate to Backend Directory**:
   ```bash
   cd backend
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment**:
   ```bash
   cp env.example .env
   # Edit .env with your database URL, e.g., DATABASE_URL=postgresql://user:password@localhost/healthpulse_db
   ```

5. **Initialize Database**:
   ```bash
   python init_db.py
   ```

6. **Run Backend Server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   API docs at http://localhost:8000/docs.

## Usage Guide

After setup, access the application at http://localhost:5173. The interface includes:

- **Dashboard**: Overview of metrics, charts for facilities by region and infrastructure mix.
- **Map View**: Interactive map with facility markers, search, and filters.
- **Registry Table**: Detailed table with sorting, filtering, and pagination.
- **ETL Pipeline**: Manage data processing jobs, view status, and launch new jobs.

For detailed usage, refer to [USAGE_GUIDE.md](USAGE_GUIDE.md).

## API Reference

The backend provides RESTful APIs for ETL jobs, Overpass proxy, and data management.

### ETL Jobs Endpoints

- `GET /api/v1/etl-jobs/` - List all ETL jobs
- `POST /api/v1/etl-jobs/` - Create a new ETL job
- `GET /api/v1/etl-jobs/{id}` - Get job details
- `PUT /api/v1/etl-jobs/{id}` - Update job
- `DELETE /api/v1/etl-jobs/{id}` - Delete job

### Overpass Proxy Endpoints

- `GET /api/v1/overpass/facilities` - Query facilities via backend proxy

For full API documentation, visit http://localhost:8000/docs.

## Project Structure

```
healthpulse-registry/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── dosm_dataset.py
│   │   │   ├── dosm_record.py
│   │   │   ├── etl_job.py
│   │   │   └── dataset_version.py
│   │   ├── routes/
│   │   │   ├── etl_jobs.py
│   │   │   └── overpass.py
│   │   ├── schemas/
│   │   │   ├── dosm_dataset.py
│   │   │   ├── dosm_record.py
│   │   │   ├── etl_job.py
│   │   │   └── scraper_config.py
│   │   └── services/
│   │       ├── dataset_discovery.py
│   │       ├── dosm_scraper.py
│   │       ├── overpass_proxy.py
│   │       ├── source_gate.py
│   │       ├── version_tracker.py
│   │       └── scrapers/
│   │           ├── tier1_opendosm.py
│   │           ├── tier2_direct_download.py
│   │           ├── tier3_pdf_extraction.py
│   │           ├── tier4_html_parsing.py
│   │           └── tier5_browser_automation.py
│   ├── data/
│   │   └── malaysia-latest.osm.pbf
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── env.example
│   └── init_db.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MapView.tsx
│   │   │   ├── RegistryTable.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── geminiService.ts
│   │   └── types.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
├── docker-compose.yml
├── Dockerfile
├── README.md
├── BACKEND_SETUP.md
├── USAGE_GUIDE.md
└── TESTING_GUIDE.md
```

## Testing

Run tests for backend and frontend separately.

### Backend Testing

1. Navigate to backend directory.
2. Install test dependencies if needed.
3. Run `pytest` or refer to [backend/TESTING_GUIDE.md](backend/TESTING_GUIDE.md).

### Frontend Testing

1. Run `npm test` in the root directory.

For detailed testing procedures, see [TESTING_GUIDE.md](TESTING_GUIDE.md).

## Contributing Guidelines

1. **Fork the Repository**: Create a fork for your changes.
2. **Create a Branch**: Use descriptive branch names (e.g., `feature/add-etl-monitoring`).
3. **Follow Coding Standards**: Use TypeScript for frontend, adhere to PEP 8 for Python.
4. **Write Tests**: Ensure new features include tests.
5. **Commit Messages**: Use clear, concise commit messages.
6. **Pull Requests**: Provide detailed descriptions and link to issues.
7. **Code Reviews**: All changes require review before merging.

## Safety Notes

- **API Keys**: Never commit API keys (e.g., Gemini) to version control. Use environment variables.
- **Data Privacy**: Handle health facility data responsibly; ensure compliance with data protection regulations.
- **Security**: Use HTTPS in production, validate inputs, and sanitize data.
- **Performance**: Monitor resource usage, especially with large datasets.
- **Dependencies**: Regularly update dependencies for security patches.
- **Backup**: Regularly back up the database.
- **Access Control**: Implement authentication for production deployments.
