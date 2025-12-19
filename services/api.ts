
import axios from 'axios';
import { Facility, FacilityType, ETLJob, PipelineStatus } from '../types';



// API_BASE_URL is used for backend API calls
// In Docker: browser runs on host, needs host-accessible URL (not localhost if accessed via network IP)
// Inside container: backend:8000 works, but browser can't resolve 'backend'
// Solution: Replace Docker service name with current hostname + mapped port for browser
const envVar = import.meta.env.VITE_API_BASE_URL;
let resolvedUrl = envVar || 'http://localhost:8002/api/v1';
if (typeof window !== 'undefined') {
  const currentHost = window.location.hostname;
  const backendPort = '8002'; // Docker mapped port from docker-compose.yml
  if (resolvedUrl.includes('backend:8000')) {
    // Browser context: replace Docker service name with current hostname
    resolvedUrl = resolvedUrl.replace('http://backend:8000', `http://${currentHost}:${backendPort}`);
  } else if (resolvedUrl.includes('localhost') && currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
    // If accessing via network IP, use that IP for backend too
    resolvedUrl = resolvedUrl.replace('localhost', currentHost);
  }
}
const API_BASE_URL = resolvedUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});


// API Functions
export const facilitiesApi = {
  /**
   * Fetch all health facilities from database (fast!)
   * 
   * This endpoint queries the local database instead of Overpass API,
   * providing much faster response times (milliseconds vs seconds).
   * 
   * Facilities are populated via ETL jobs. Use triggerFacilityETL() to refresh data.
   */
  async getAll(signal?: AbortSignal): Promise<Facility[]> {
    try {
      const response = await api.get('/facilities', {
        timeout: 5000,  // Much faster - database query
        signal: signal,
      });

      if (response.data && response.data.facilities) {
        // Backend returns pre-mapped facilities from database
        const mapped = response.data.facilities.map((facility: any) => ({
          id: facility.id?.toString() || facility.osm_id || '',
          name: facility.name,
          type: facility.type === 'hospital' ? FacilityType.HOSPITAL : FacilityType.CLINIC,
          location: facility.location,
          address: facility.address || '',
          contact: facility.contact || '',
          lastUpdated: facility.lastUpdated || '',
          isDuplicate: false,
          score: facility.score || 0,
        }));
        return mapped;
      }
      return [];
    } catch (error: any) {
      // Don't throw error if request was cancelled
      if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED' || (signal && signal.aborted)) {
        return [];
      }
      console.error('Error fetching facilities from database:', error);
      // Handle empty database case (no facilities loaded yet)
      if (error.response?.status === 404 || error.response?.status === 200) {
        // If database is empty, return empty array (user needs to run ETL first)
        return [];
      }
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. Please try again.');
      }
      throw new Error(`Failed to fetch facilities: ${error.message || 'Unknown error'}`);
    }
  },

  /**
   * Fetch facilities by bounding box (for map viewport filtering)
   * Queries database instead of Overpass API (fast!)
   */
  async getByBoundingBox(bbox: { south: number; west: number; north: number; east: number }): Promise<Facility[]> {
    try {
      const bboxString = `${bbox.south},${bbox.west},${bbox.north},${bbox.east}`;
      const response = await api.get('/facilities', {
        params: {
          bbox: bboxString,
        },
        timeout: 5000,  // Much faster - database query
      });

      if (response.data && response.data.facilities) {
        // Backend returns pre-mapped facilities from database
        return response.data.facilities.map((facility: any) => ({
          id: facility.id?.toString() || facility.osm_id || '',
          name: facility.name,
          type: facility.type === 'hospital' ? FacilityType.HOSPITAL : FacilityType.CLINIC,
          location: facility.location,
          address: facility.address || '',
          contact: facility.contact || '',
          lastUpdated: facility.lastUpdated || '',
          isDuplicate: false,
          score: facility.score || 0,
        }));
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

  /**
   * Get facilities grouped by state
   */
  async getByState(): Promise<Array<{ name: string; facilities: number }>> {
    try {
      const response = await api.get('/facilities/by-state');
      return response.data || [];
    } catch (error: any) {
      console.error('Error fetching facilities by state:', error);
      // Return empty array on error
      return [];
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

  /**
   * Trigger facility ETL job to fetch and store facilities from Overpass API
   * This is a long-running operation (10-30+ seconds) that fetches fresh data
   * from Overpass API and stores it in the database.
   * 
   * @param bbox Optional bounding box as "south,west,north,east"
   */
  async triggerFacilityETL(bbox?: string): Promise<{ etl_job_id: number; result: any; message: string }> {
    try {
      const params = bbox ? { bbox } : {};
      const response = await api.post('/etl-jobs/overpass-facilities', null, {
        params,
        timeout: 120000,  // 2 minutes timeout for long-running ETL job
      });
      return response.data;
    } catch (error: any) {
      console.error('Error triggering facility ETL job:', error);
      throw new Error(`Failed to trigger facility ETL: ${error.message || 'Unknown error'}`);
    }
  },

  /**
   * Get ETL pipeline metrics
   */
  async getMetrics(): Promise<{
    sources_active: string;
    avg_confidence_score: number;
    write_success_rate: number;
  }> {
    try {
      const response = await api.get('/etl-jobs/metrics');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching ETL metrics:', error);
      // Return defaults on error
      return {
        sources_active: '0/0',
        avg_confidence_score: 0,
        write_success_rate: 0
      };
    }
  },
};

// Analytics API
export const analyticsApi = {
  /**
   * Get analytics data including active users and facility stats
   */
  async getAnalytics(): Promise<{ active_users: number; facilities: any }> {
    try {
      const response = await api.get('/analytics');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching analytics:', error);
      // Return defaults on error
      return { active_users: 0, facilities: null };
    }
  },
};

// Health API
export const healthApi = {
  /**
   * Check database health status
   */
  async checkDatabaseHealth(): Promise<{
    connected: boolean;
    postgis_enabled: boolean;
    status: string;
    message: string;
  }> {
    try {
      const response = await api.get('/health/database');
      return response.data;
    } catch (error: any) {
      console.error('Error checking database health:', error);
      return {
        connected: false,
        postgis_enabled: false,
        status: 'error',
        message: 'Failed to check database status'
      };
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