# Configure HealthPulse Backend for Local Overpass API

## Tasks
- [x] Update docker-compose.yml to add OVERPASS_API_URL=http://host.docker.internal:8080 to backend environment variables
- [x] Restart Docker services to apply configuration changes
- [ ] Test Overpass API integration with local instance

## Notes
- Keep public API (https://overpass-api.de) as fallback in env.example
- Local Overpass API runs on host at port 8080
- Use host.docker.internal to access host from Docker container
