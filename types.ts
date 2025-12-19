
export enum FacilityType {
  HOSPITAL = 'Hospital',
  CLINIC = 'Clinic'
}

export enum PipelineStatus {
  COMPLETED = 'Completed',
  PROCESSING = 'Processing',
  FAILED = 'Failed',
  PENDING = 'Pending'
}

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Facility {
  id: string;
  name: string;
  type: FacilityType;
  location: Coordinates;
  address: string;
  contact: string;
  lastUpdated: string;
  isDuplicate: boolean;
  score: number; // Quality score
}

export interface ETLJob {
  id: string;
  source: string;
  status: PipelineStatus;
  recordsProcessed: number;
  startTime: string;
  errors: number;
}

export type AppView = 'dashboard' | 'map' | 'registry' | 'etl';
