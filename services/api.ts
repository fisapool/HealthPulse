import axios from 'axios';
import { Facility, FacilityType, ETLJob, PipelineStatus } from '../types';

// Malaysia bounding box: [south, west, north, east]
const MALAYSIA_BOUNDS = [0.855, 98.942, 7.363, 119.267];

// Overpass API configuration
const USE_BACKEND_PROXY = import.meta.env.VITE_USE_BACKEND_OVERPASS_PROXY === 'true';
const OVERPASS_API_URL = import.meta.env.VITE_OVERPASS_API_URL || 'http://192.168.0.145:8083/api/interpreter';

// Alternative endpoints:
// 'https://overpass-api.de/api/interpreter' (public)
// 'https://overpass.kumi.systems/api/interpreter' (public)
// 'https://lz4.overpass-api.de/api/interpreter' (public)

// Build Overpass query for healthcare facilities (hospitals and clinics only)
function buildOverpassQuery(bounds: number[] = MALAYSIA_BOUNDS): string {
  const [south, west, north, east] = bounds;
  return `
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](${south},${west},${north},${east});
      way["amenity"="hospital"](${south},${west},${north},${east});
      relation["amenity"="hospital"](${south},${west},${north},${east});
      node["amenity"="clinic"](${south},${west},${north},${east});
      way["amenity"="clinic"](${south},${west},${north},${east});
      relation["amenity"="clinic"](${south},${west},${north},${east});
      node["healthcare"="hospital"](${south},${west},${north},${east});
      way["healthcare"="hospital"](${south},${west},${north},${east});
      relation["healthcare"="hospital"](${south},${west},${north},${east});
      node["healthcare"="clinic"](${south},${west},${north},${east});
      way["healthcare"="clinic"](${south},${west},${north},${east});
      relation["healthcare"="clinic"](${south},${west},${north},${east});
      node["healthcare"="health_centre"](${south},${west},${north},${east});
      way["healthcare"="health_centre"](${south},${west},${north},${east});
      relation["healthcare"="health_centre"](${south},${west},${north},${east});
    );
    out center;
  `.trim();
}

// Map OSM element to Facility type
function mapOSMToFacility(element: any): Facility {
  let location = { lat: 0, lng: 0 };

  // Extract coordinates
  if (element.type === 'node') {
    location = { lat: parseFloat(element.lat), lng: parseFloat(element.lon) };
  } else if (element.type === 'way' || element.type === 'relation') {
    if (element.center) {
      location = { lat: parseFloat(element.center.lat), lng: parseFloat(element.center.lon) };
    }
  }

  // Determine facility type - only hospitals and clinics
  let facilityType: FacilityType = FacilityType.CLINIC; // Default to clinic
  const amenity = element.tags?.amenity?.toLowerCase();
  const healthcare = element.tags?.healthcare?.toLowerCase();

  if (amenity === 'hospital' || healthcare === 'hospital') {
    facilityType = FacilityType.HOSPITAL;
  } else if (amenity === 'clinic' || healthcare === 'clinic' || healthcare === 'health_centre') {
    facilityType = FacilityType.CLINIC;
  }

  // Calculate quality score based on tag completeness
  let score = 0;
  if (element.tags?.name) score += 25;
  if (element.tags?.amenity || element.tags?.healthcare) score += 20;
  if (element.tags?.operator) score += 15;
  if (element.tags?.phone || element.tags?.['contact:phone']) score += 10;
  if (element.tags?.['addr:full'] || element.tags?.['addr:street']) score += 15;
  if (location.lat !== 0 && location.lng !== 0) score += 15;

  // Build address from OSM tags
  let address = element.tags?.['addr:full'] || '';
  if (!address) {
    const parts = [];
    if (element.tags?.['addr:street']) parts.push(element.tags['addr:street']);
    if (element.tags?.['addr:city']) parts.push(element.tags['addr:city']);
    if (element.tags?.['addr:postcode']) parts.push(element.tags['addr:postcode']);
    if (element.tags?.['addr:state']) parts.push(element.tags['addr:state']);
    address = parts.join(', ') || `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`;
  }

  return {
    id: element.id?.toString() || `${element.type}-${element.id}`,
    name: element.tags?.name || 'Unnamed Facility',
    type: facilityType,
    location,
    address,
    contact: element.tags?.phone || element.tags?.['contact:phone'] || '',
    lastUpdated: element.timestamp ? new Date(element.timestamp).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
    isDuplicate: false, // OSM data doesn't have duplicates flag
    score: Math.min(score, 100),
  };
}

// API_BASE_URL is used for backend API calls
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Functions
export const facilitiesApi = {
  /**
   * Fetch all health facilities from Overpass API (Malaysia only, hospitals and clinics)
   * Uses backend proxy if VITE_USE_BACKEND_OVERPASS_PROXY is enabled
   */
  async getAll(signal?: AbortSignal): Promise<Facility[]> {
    try {
      // Use backend proxy if enabled
      if (USE_BACKEND_PROXY) {
        const response = await api.post('/overpass/facilities', {}, {
          timeout: 60000,
          signal: signal,
        });

        if (response.data && response.data.facilities) {
          // Backend returns pre-mapped facilities
          return response.data.facilities.map((facility: any) => ({
            id: facility.id,
            name: facility.name,
            type: facility.type === 'hospital' ? FacilityType.HOSPITAL : FacilityType.CLINIC,
            location: facility.location,
            address: facility.address,
            contact: facility.contact || '',
            lastUpdated: facility.lastUpdated,
            isDuplicate: false,
            score: facility.score || 0,
          }));
        }
        return [];
      }

      // Direct Overpass API query (original behavior)
      const query = buildOverpassQuery();
      const response = await axios.post(OVERPASS_API_URL, query, {
        headers: {
          'Content-Type': 'text/plain',
        },
        timeout: 60000, // 60 second timeout for local API
        signal: signal, // Support request cancellation
      });

      // Check for Overpass API errors in response
      if (response.data?.remark) {
        // Handle remark/error if needed
      }

      // Handle different response formats from Overpass API
      let elements: any[] = [];
      
      // Case 1: Standard format with elements property
      if (response.data && response.data.elements && Array.isArray(response.data.elements)) {
        elements = response.data.elements;
      }
      // Case 2: Response data is directly an array
      else if (Array.isArray(response.data)) {
        elements = response.data;
      }
      // Case 3: Response data is object with numeric keys (array-like object)
      else if (response.data && typeof response.data === 'object' && !Array.isArray(response.data)) {
        const keys = Object.keys(response.data);
        const isArrayLike = keys.length > 0 && keys.every((key, idx) => key === String(idx));
        if (isArrayLike) {
          elements = Object.values(response.data);
        }
      }

      if (elements.length > 0) {
        const facilities = elements
          .map((element: any) => mapOSMToFacility(element))
          .filter((facility: Facility) => 
            // Double-check: only hospitals and clinics
            facility.type === FacilityType.HOSPITAL || facility.type === FacilityType.CLINIC
          )
          .filter((facility: Facility) => 
            // Only include facilities with valid coordinates
            facility.location.lat !== 0 && facility.location.lng !== 0
          );
        return facilities;
      }
      
      return [];
    } catch (error: any) {
      // Don't throw error if request was cancelled
      if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED' || (signal && signal.aborted)) {
        return [];
      }
      console.error('Error fetching facilities from Overpass API:', error);
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. The Overpass API may be slow. Please try again.');
      }
      throw new Error(`Failed to fetch facilities: ${error.message || 'Unknown error'}`);
    }
  },

  /**
   * Fetch facilities by bounding box (for map viewport filtering)
   * Uses backend proxy if VITE_USE_BACKEND_OVERPASS_PROXY is enabled
   */
  async getByBoundingBox(bbox: { south: number; west: number; north: number; east: number }): Promise<Facility[]> {
    try {
      // Use backend proxy if enabled
      if (USE_BACKEND_PROXY) {
        const response = await api.get('/overpass/facilities/bbox', {
          params: {
            south: bbox.south,
            west: bbox.west,
            north: bbox.north,
            east: bbox.east,
          },
          timeout: 60000,
        });

        if (response.data && response.data.facilities) {
          // Backend returns pre-mapped facilities
          return response.data.facilities.map((facility: any) => ({
            id: facility.id,
            name: facility.name,
            type: facility.type === 'hospital' ? FacilityType.HOSPITAL : FacilityType.CLINIC,
            location: facility.location,
            address: facility.address,
            contact: facility.contact || '',
            lastUpdated: facility.lastUpdated,
            isDuplicate: false,
            score: facility.score || 0,
          }));
        }
        return [];
      }

      // Direct Overpass API query (original behavior)
      const bounds = [bbox.south, bbox.west, bbox.north, bbox.east];
      const query = buildOverpassQuery(bounds);
      const response = await axios.post(OVERPASS_API_URL, query, {
        headers: {
          'Content-Type': 'text/plain',
        },
        timeout: 60000, // 60 second timeout for local API
      });

      if (response.data && response.data.elements) {
        const facilities = response.data.elements
          .map((element: any) => mapOSMToFacility(element))
          .filter((facility: Facility) => 
            facility.type === FacilityType.HOSPITAL || facility.type === FacilityType.CLINIC
          )
          .filter((facility: Facility) => 
            facility.location.lat !== 0 && facility.location.lng !== 0
          );
        return facilities;
      }
      return [];
    } catch (error: any) {
      console.error('Error fetching facilities by bounding box:', error);
      throw new Error(`Failed to fetch facilities: ${error.message || 'Unknown error'}`);
    }
  },

  /**
   * Fetch a single facility by ID (not supported by Overpass API)
   */
  async getById(id: string): Promise<Facility> {
    throw new Error('Overpass API is read-only. Use getAll() and filter by ID.');
  },

  /**
   * Create a new facility (not supported by Overpass API)
   */
  async create(facility: Partial<Facility>): Promise<Facility> {
    throw new Error('Overpass API is read-only. Use OpenStreetMap editing tools to add facilities.');
  },

  /**
   * Update an existing facility (not supported by Overpass API)
   */
  async update(id: string, facility: Partial<Facility>): Promise<Facility> {
    throw new Error('Overpass API is read-only. Use OpenStreetMap editing tools to update facilities.');
  },

  /**
   * Delete a facility (not supported by Overpass API)
   */
  async delete(id: string): Promise<void> {
    throw new Error('Overpass API is read-only. Use OpenStreetMap editing tools to delete facilities.');
  },

  /**
   * Search facilities by name or location (client-side filtering)
   */
  async search(query: string): Promise<Facility[]> {
    try {
      // Fetch all and filter client-side
      // Note: For better performance, consider implementing a backend search proxy
      const allFacilities = await this.getAll();
      const lowerQuery = query.toLowerCase();
      return allFacilities.filter(facility => 
        facility.name.toLowerCase().includes(lowerQuery) ||
        facility.address.toLowerCase().includes(lowerQuery) ||
        facility.id.toLowerCase().includes(lowerQuery)
      );
    } catch (error: any) {
      console.error('Error searching facilities:', error);
      throw new Error(`Failed to search facilities: ${error.message || 'Unknown error'}`);
    }
  },
};

// ETL Jobs API (to be implemented in backend)
export const etlApi = {
  /**
   * Fetch all ETL jobs
   */
  async getAll(): Promise<ETLJob[]> {
    try {
      const response = await api.get('/etl-jobs/');
      if (Array.isArray(response.data)) {
        return response.data.map(mapToETLJob);
      }
      if (response.data.results) {
        return response.data.results.map(mapToETLJob);
      }
      return [];
    } catch (error: any) {
      // Don't show error if endpoint doesn't exist (404)
      if (error.response?.status === 404) {
        console.warn('ETL jobs API endpoint not found');
        return [];
      }
      // Network errors (connection refused, no server running) - silently return empty array
      // The browser console will still show the network error, which is expected browser behavior
      // Suppress console warning for network errors (backend not running is expected in development)
      // Only warn for unexpected errors (not network/connection errors)
      const isNetworkError = error.code === 'ERR_NETWORK' || error.code === 'ERR_CONNECTION_REFUSED' || !error.response;
      if (!isNetworkError) {
        console.warn('ETL jobs API not available, returning empty array', error.message);
      }
      return [];
    }
  },

  /**
   * Create a new ETL job
   */
  async create(job: Partial<ETLJob>): Promise<ETLJob> {
    try {
      const response = await api.post('/etl-jobs/', {
        source: job.source,
        status: job.status || PipelineStatus.PENDING,
      });
      return mapToETLJob(response.data);
    } catch (error: any) {
      console.error('Error creating ETL job:', error);
      throw new Error(`Failed to create ETL job: ${error.message || 'Unknown error'}`);
    }
  },
};

function mapToETLJob(item: any): ETLJob {
  return {
    id: item.id?.toString() || '',
    source: item.source || 'Unknown',
    status: (item.status as PipelineStatus) || PipelineStatus.PENDING,
    recordsProcessed: item.records_processed || item.recordsProcessed || 0,
    startTime: item.start_time || item.startTime || new Date().toISOString(),
    errors: item.errors || 0,
  };
}

export default api;