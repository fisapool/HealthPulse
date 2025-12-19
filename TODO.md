# TODO: Update services/api.ts for Overpass API Integration

- [ ] Update facilitiesApi.getAll() to query Overpass API instead of backend API, using buildOverpassQuery(), axios.post with timeout, filter elements, and map with mapOSMToFacility().
- [ ] Add facilitiesApi.getByBoundingBox(bounds: number[]) with similar logic for custom bounding boxes.
- [ ] Test the Overpass API integration: run the app, verify facilities load from OSM, check for TypeScript errors.
- [ ] Ensure search() works correctly since it depends on getAll().
