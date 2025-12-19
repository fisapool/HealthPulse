# Overpass API Setup Guide

This guide explains how to set up a self-hosted Overpass API instance for the HealthPulse Registry application, configured for Malaysia OpenStreetMap data.

## Overview

The Overpass API is a read-only API that serves up-to-date OpenStreetMap data. This setup uses the `wiktorn/overpass-api` Docker image to run a self-hosted instance with Malaysia OSM data.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM (Overpass API is memory-intensive)
- 2-3GB of free disk space for OSM database
- Internet connection for downloading OSM extract

## Step 1: Download Malaysia OSM Extract

1. Download the latest Malaysia OSM extract from Geofabrik:
   ```bash
   # Create data directory
   mkdir -p backend/data
   
   # Download Malaysia extract (approximately 50-100MB compressed)
   cd backend/data
   wget https://download.geofabrik.de/asia/malaysia-latest.osm.pbf
   ```

   **Alternative:** If `wget` is not available, you can:
   - Download manually from: https://download.geofabrik.de/asia/malaysia-latest.osm.pbf
   - Place the file at `backend/data/malaysia-latest.osm.pbf`

## Step 2: Configure Docker Compose

The Overpass API service is already configured in `docker-compose.yml`. Verify the configuration:

```yaml
overpass-api:
  image: wiktorn/overpass-api:latest
  container_name: healthpulse-overpass-api
  ports:
    - "8083:80"
  volumes:
    - overpass_data:/db
    - ./backend/data:/data:ro
  environment:
    - OVERPASS_META=yes
    - OVERPASS_MODE=clone
    - OVERPASS_RULES_LOAD=10
```

## Step 3: Initialize Overpass API

1. Start the Overpass API service:
   ```bash
   docker compose up -d overpass-api
   ```

2. Monitor the initialization process:
   ```bash
   docker compose logs -f overpass-api
   ```

   The first startup will:
   - Import the Malaysia OSM extract into the database
   - This process can take **30-60 minutes** depending on your system
   - You'll see progress messages in the logs

3. Wait for the import to complete. The service is ready when you see:
   ```
   Overpass API is ready
   ```

## Step 4: Verify Installation

1. Check service health:
   ```bash
   curl http://localhost:8083/api/status
   ```

2. Test a simple query:
   ```bash
   curl -X POST http://localhost:8083/api/interpreter \
     -H "Content-Type: text/plain" \
     -d '[out:json];node["amenity"="hospital"](0.855,98.942,7.363,119.267);out;'
   ```

3. Check from backend health endpoint:
   ```bash
   curl http://localhost:8000/api/v1/overpass/health
   ```

## Step 5: Update Environment Variables

If running outside Docker Compose, update your environment:

**Backend (`backend/.env`):**
```env
OVERPASS_API_URL=http://localhost:8083
OVERPASS_CACHE_TTL=300
OVERPASS_RATE_LIMIT=60
OVERPASS_TIMEOUT=60
```

**Frontend (`.env` or `docker-compose.yml`):**
```env
VITE_OVERPASS_API_URL=http://localhost:8083/api/interpreter
VITE_USE_BACKEND_OVERPASS_PROXY=false  # Set to true to use backend proxy
```

## Usage Modes

### Mode 1: Direct Frontend Queries (Default)

The frontend queries Overpass API directly:
- Set `VITE_USE_BACKEND_OVERPASS_PROXY=false`
- Frontend connects to `VITE_OVERPASS_API_URL`
- No caching or rate limiting from backend

### Mode 2: Backend Proxy (Recommended)

The frontend queries through the backend proxy:
- Set `VITE_USE_BACKEND_OVERPASS_PROXY=true`
- Frontend connects to backend at `/api/v1/overpass/facilities`
- Backend provides caching and rate limiting
- Better for production use

## Updating OSM Data

To update the Malaysia OSM data:

1. Download the latest extract:
   ```bash
   cd backend/data
   wget -O malaysia-latest.osm.pbf https://download.geofabrik.de/asia/malaysia-latest.osm.pbf
   ```

2. Restart the Overpass API service:
   ```bash
   docker compose restart overpass-api
   ```

   The service will automatically detect the new file and re-import.

## Troubleshooting

### Service Won't Start

- **Check logs:** `docker compose logs overpass-api`
- **Verify OSM file exists:** `ls -lh backend/data/malaysia-latest.osm.pbf`
- **Check disk space:** `df -h`
- **Check memory:** `free -h` (need at least 4GB free)

### Import Takes Too Long

- Normal for first import: 30-60 minutes
- Check system resources (CPU, RAM, disk I/O)
- Consider using a smaller regional extract for testing

### Health Check Fails

- Wait for initial import to complete
- Check service logs: `docker compose logs overpass-api`
- Verify port 8083 is not in use: `netstat -an | grep 8083`

### Out of Memory Errors

- Increase Docker memory limit
- Reduce `OVERPASS_RULES_LOAD` value
- Use a smaller OSM extract

### Database Corruption

If the database becomes corrupted:

1. Stop the service: `docker compose stop overpass-api`
2. Remove the volume: `docker volume rm healthpulse-registry_overpass_data`
3. Restart the service: `docker compose up -d overpass-api`

## Performance Tuning

### Memory Settings

Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 4G  # Increase if you have more RAM
    reservations:
      memory: 2G
```

### Cache Settings

Adjust in `backend/.env`:
```env
OVERPASS_CACHE_TTL=600  # Increase for better caching (10 minutes)
```

### Rate Limiting

Adjust in `backend/.env`:
```env
OVERPASS_RATE_LIMIT=120  # Increase for higher throughput
```

## Maintenance

### Regular Updates

- OSM data is updated daily by Geofabrik
- Consider updating weekly or monthly
- Monitor disk usage: database grows over time

### Backup

The Overpass database is stored in a Docker volume:
```bash
# Backup volume
docker run --rm -v healthpulse-registry_overpass_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/overpass-backup.tar.gz /data
```

### Monitoring

Check service status:
```bash
docker compose ps overpass-api
docker compose logs --tail=50 overpass-api
```

## Additional Resources

- Overpass API Documentation: https://wiki.openstreetmap.org/wiki/Overpass_API
- Geofabrik Downloads: https://download.geofabrik.de/
- Docker Image: https://hub.docker.com/r/wiktorn/overpass-api

## Support

For issues specific to this setup:
1. Check the troubleshooting section above
2. Review Docker Compose logs
3. Verify OSM extract file integrity
4. Check backend and frontend logs for API errors

