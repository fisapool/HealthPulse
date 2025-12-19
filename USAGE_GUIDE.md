# HealthPulse Registry - Usage Guide

This guide explains how to use the HealthPulse Registry application to manage and analyze health facility data.

## Application Overview

HealthPulse Registry is a web application that aggregates health facility data from OpenStreetMap via the Overpass API, provides analytics through an interactive dashboard, and manages ETL (Extract, Transform, Load) pipelines for data processing.

## Getting Started

After [setting up the application](./README.md#quick-start), access it at `http://localhost:5173`.

## Navigation

The application has four main views accessible via the sidebar:

- **Dashboard**: Analytics and statistics overview
- **Map View**: Interactive map of health facilities
- **Registry Table**: Detailed facility listings
- **ETL Pipeline**: Data processing job management

## Dashboard

The dashboard provides real-time analytics about your health facility registry.

### Key Metrics

- **Total Facilities**: Count of all facilities in the registry
- **Cleaned Records**: Facilities after deduplication
- **Potential Duplicates**: Facilities flagged as possible duplicates
- **Active Users**: Current system users (static for demo)

### Charts

- **Facilities by Region**: Bar chart showing facility distribution across regions
- **Infrastructure Mix**: Pie chart showing hospital vs clinic breakdown

### Data Loading

The dashboard automatically loads facility data from the Overpass API. If data fails to load, check:
- Network connectivity
- Overpass API endpoint configuration
- Browser console for errors

## Map View

Interactive map displaying health facilities as markers.

### Features

- **Facility Markers**: Click markers to view facility details
- **Clustering**: Markers cluster at higher zoom levels for performance
- **Search**: Search facilities by name or address
- **Filters**: Filter by facility type (Hospital/Clinic)
- **Bounding Box Queries**: Load facilities within current map bounds

### Using the Map

1. **Zoom and Pan**: Use mouse or touch to navigate
2. **Click Markers**: View facility popup with details
3. **Search Box**: Type to filter visible facilities
4. **Filter Buttons**: Toggle hospital/clinic visibility
5. **Refresh**: Reload data from Overpass API

### Map Data

- Data sourced from OpenStreetMap via Overpass API
- Limited to hospitals and clinics in Malaysia
- Real-time updates from OSM data

## Registry Table

Comprehensive table view of all facilities with advanced filtering and sorting.

### Table Features

- **Sorting**: Click column headers to sort
- **Filtering**: Use search box for text-based filtering
- **Pagination**: Navigate through large datasets
- **Export**: Export filtered results (future feature)

### Columns

- **Name**: Facility name
- **Type**: Hospital or Clinic
- **Address**: Full address
- **Contact**: Phone/contact information
- **Last Updated**: When data was last refreshed
- **Quality Score**: Data quality indicator
- **Duplicate Flag**: Whether facility is marked as duplicate

### Managing Records

- **View Details**: Click row to expand facility information
- **Edit Records**: Modify facility data (future feature)
- **Flag Duplicates**: Mark suspected duplicates (future feature)

## ETL Pipeline

Manage data extraction, transformation, and loading processes.

### Pipeline Stages

1. **Extraction**: Connect to data sources (DHIS2, legacy databases)
2. **Cleaning & Deduplication**: Remove duplicates using AI (Gemini)
3. **Loading**: Store processed data in PostGIS database

### Job Management

- **View Jobs**: See all ETL job history
- **Job Status**: Monitor running, completed, or failed jobs
- **Launch New Job**: Start new data processing job
- **Job Details**: View processing statistics and errors

### Creating ETL Jobs

1. Click "Launch New Job" button
2. Select data source (DHIS2, SQL databases, etc.)
3. Configure processing parameters
4. Monitor job progress in real-time

### Job Metrics

- **Records Processed**: Number of facilities processed
- **Errors**: Count of processing errors
- **Status**: Current job state
- **Start Time**: When job began processing

## API Integration


### Overpass API

The application integrates with OpenStreetMap's Overpass API through the backend proxy:

- **Endpoint**: Backend proxy at `/api/v1/overpass/facilities`
- **Query**: Limited to healthcare facilities in Malaysia
- **Timeout**: 60-second request timeout
- **Caching**: Backend proxy provides caching and rate limiting

### Backend API

ETL jobs managed through FastAPI backend:

- **Base URL**: `http://localhost:8000/api/v1`
- **Endpoints**: CRUD operations for ETL jobs
- **Documentation**: Available at `/docs`

## Configuration


### Environment Variables

```env
# Backend API for all requests
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Gemini API for AI features
GEMINI_API_KEY=your_gemini_api_key_here
```

### Backend Proxy

All Overpass API queries are routed through the backend proxy:
- **Health Facilities**: `/api/v1/overpass/facilities`
- **Bounding Box Queries**: `/api/v1/overpass/facilities/bbox`
- **Health Check**: `/api/v1/overpass/health`

## Troubleshooting

### Common Issues


#### Map Not Loading Facilities

- Check backend proxy configuration
- Verify backend is running on port 8000
- Check browser console for network errors
- Ensure Overpass instance is accessible to backend

#### ETL Jobs Not Appearing

- Verify backend is running on port 8000
- Check `VITE_API_BASE_URL` configuration
- Ensure database is initialized
- Check backend logs for errors

#### Search Not Working

- Search depends on loaded facility data
- Ensure facilities are loaded first
- Check for JavaScript errors in console

#### Performance Issues

- Large datasets may cause slow rendering
- Use filters to reduce visible facilities
- Consider pagination for table view

### Data Quality

- **Duplicates**: Flagged automatically or manually
- **Quality Scores**: Based on data completeness
- **Updates**: Data refreshed from OSM regularly

## Advanced Usage

### Custom Queries

Modify Overpass queries in `services/api.ts` for different data scopes.

### AI-Powered Deduplication

Uses Google Gemini AI for intelligent duplicate detection based on:
- Facility names
- Addresses
- Geographic proximity
- Contact information

### Spatial Analysis

PostGIS enables advanced spatial queries and analysis.

## Support

For technical support:
- Check backend logs: `docker-compose logs backend`
- Frontend console: Browser developer tools
- API documentation: `http://localhost:8000/docs`

## Future Features

- Advanced filtering and search
- Data export capabilities
- User authentication
- Real-time collaboration
- Mobile-responsive design
- Integration with additional data sources

## Safety Notes

- **API Keys**: Never commit API keys (e.g., Gemini) to version control. Use environment variables.
- **Data Privacy**: Handle health facility data responsibly; ensure compliance with data protection regulations.
- **Security**: Use HTTPS in production, validate inputs, and sanitize data.
- **Performance**: Monitor resource usage, especially with large datasets.
- **Dependencies**: Regularly update dependencies for security patches.
- **Backup**: Regularly back up the database.
- **Access Control**: Implement authentication for production deployments.
