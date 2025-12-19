# Testing State/City Filtering for Overpass API

This document describes how to test the new state and city filtering functionality in the HealthPulse Overpass API integration.

## Prerequisites

1. **Backend is running**: `docker-compose up -d backend` (or `docker-compose up -d` for all services)
2. **Overpass API is accessible**: The backend should be able to reach the Overpass instance at `http://172.17.0.1:8080`

## Test Cases

### 1. Health Check
Verify the Overpass API connection is working:

```bash
curl "http://localhost:8002/api/v1/overpass/health"
```

**Expected**: `{"status": "healthy", "available": true, ...}`

### 2. State Filtering (GET endpoint)
Test filtering by state name using query parameters:

```bash
# Test with Selangor
curl "http://localhost:8002/api/v1/overpass/facilities?state_name=Selangor"

# Test with Johor
curl "http://localhost:8002/api/v1/overpass/facilities?state_name=Johor"

# Test with Perak
curl "http://localhost:8002/api/v1/overpass/facilities?state_name=Perak"
```

**Expected**: JSON response with `facilities` array and `count`. May return empty if no facilities exist for that state in OSM data.

### 3. City Filtering (GET endpoint)
Test filtering by city name:

```bash
# Test with Kuala Lumpur
curl "http://localhost:8002/api/v1/overpass/facilities?city_name=Kuala%20Lumpur"

# Test with Penang (note: city boundaries may not exist in OSM)
curl "http://localhost:8002/api/v1/overpass/facilities?city_name=Penang"
```

**Expected**: JSON response with facilities in that city, or empty array if boundary doesn't exist.

### 4. State Filtering (POST endpoint)
Test using POST with JSON body:

```bash
curl -X POST "http://localhost:8002/api/v1/overpass/facilities" \
  -H "Content-Type: application/json" \
  -d '{"state_name": "Selangor"}'

curl -X POST "http://localhost:8002/api/v1/overpass/facilities" \
  -H "Content-Type: application/json" \
  -d '{"city_name": "Kuala Lumpur"}'
```

**Expected**: Same as GET endpoint responses.

### 5. Validation Test
Test that validation prevents using both state and city together:

```bash
curl "http://localhost:8002/api/v1/overpass/facilities?state_name=Selangor&city_name=Kuala%20Lumpur"
```

**Expected**: `400 Bad Request` with error message: "Specify either state_name or city_name, not both."

### 6. Bounding Box (existing functionality)
Verify existing bbox filtering still works:

```bash
# Using GET endpoint with bbox parameter
curl "http://localhost:8002/api/v1/overpass/facilities/bbox?south=2.5&west=101.0&north=3.5&east=102.0"

# Using POST endpoint
curl -X POST "http://localhost:8002/api/v1/overpass/facilities" \
  -H "Content-Type: application/json" \
  -d '{"bbox": [2.5, 101.0, 3.5, 102.0]}'
```

**Expected**: Facilities within the bounding box.

## Understanding Results

### Empty Results (`count: 0`)
Empty results can occur if:
1. **No facilities exist**: The OSM data doesn't contain healthcare facilities in that area
2. **Boundary doesn't exist**: The state/city boundary relation doesn't exist in OSM with that exact name
3. **Name mismatch**: The name in OSM might be different (e.g., "Kuala Lumpur" vs "Kuala Lumpur Federal Territory")

### Valid Results
A successful response looks like:
```json
{
  "facilities": [
    {
      "id": "node-123456",
      "name": "Hospital Name",
      "type": "hospital",
      "location": {"lat": 3.1234, "lng": 101.5678},
      "address": "Street, City, State",
      "contact": "+60-xxx-xxxx",
      "lastUpdated": "2024-01-01T00:00:00Z",
      "score": 85,
      "osm_tags": {...}
    }
  ],
  "count": 1,
  "bbox": null,
  "cached": false
}
```

## Malaysian States to Test

The following states should work (if boundaries exist in OSM):
- Selangor
- Johor
- Kedah
- Kelantan
- Melaka (or Malacca)
- Negeri Sembilan
- Pahang
- Penang
- Perak
- Perlis
- Sabah
- Sarawak
- Terengganu

## Troubleshooting

### Connection Error
If you get "Unable to connect to Overpass API":
1. Check Overpass is running: `curl http://localhost:8080/api/status`
2. Check backend logs: `docker-compose logs backend`
3. Verify environment variable: `docker exec healthpulse-backend printenv | grep OVERPASS`

### Empty Results
If queries return empty arrays:
1. Verify the state/city name matches OSM exactly (case-sensitive)
2. Check if boundary relations exist in OSM using Overpass QL directly
3. Test with a known working bbox query to verify facilities exist in the dataset

### Testing Overpass Query Directly
You can test the Overpass query syntax directly:

```bash
cat > /tmp/test_query.txt << 'EOF'
[out:json][timeout:25];
rel["name"="Selangor"]["admin_level"="4"]["boundary"="administrative"];
map_to_area;
node["amenity"="hospital"](area);
way["amenity"="hospital"](area);
out center;
EOF

curl -X POST "http://localhost:8080/api/interpreter" \
  -H "Content-Type: text/plain" \
  -d @/tmp/test_query.txt
```

