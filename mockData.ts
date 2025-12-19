
import { Facility, FacilityType, ETLJob, PipelineStatus } from './types';

export const mockFacilities: Facility[] = [
  {
    id: 'FAC-001',
    name: 'St. Mary\'s General Hospital',
    type: FacilityType.HOSPITAL,
    location: { lat: 5.6037, lng: -0.1870 },
    address: '123 Health Ave, Accra',
    contact: '+233 24 123 4567',
    lastUpdated: '2023-10-25',
    isDuplicate: false,
    score: 98
  },
  {
    id: 'FAC-002',
    name: 'Unity Community Clinic',
    type: FacilityType.CLINIC,
    location: { lat: 5.6147, lng: -0.2050 },
    address: '45 Mercy St, Kumasi',
    contact: '+233 24 987 6543',
    lastUpdated: '2023-11-01',
    isDuplicate: true,
    score: 85
  },
  {
    id: 'FAC-003',
    name: 'Accra West Health Center',
    type: FacilityType.HEALTH_CENTER,
    location: { lat: 5.5800, lng: -0.2200 },
    address: '99 Central Dr, Accra',
    contact: '+233 24 555 0199',
    lastUpdated: '2023-11-12',
    isDuplicate: false,
    score: 92
  },
  {
    id: 'FAC-004',
    name: 'City Lab & Diagnostics',
    type: FacilityType.LABORATORY,
    location: { lat: 5.6200, lng: -0.1700 },
    address: '12 Lab Way, Accra',
    contact: '+233 24 333 4444',
    lastUpdated: '2023-11-14',
    isDuplicate: false,
    score: 95
  },
  {
    id: 'FAC-005',
    name: 'PharmaPlus Express',
    type: FacilityType.PHARMACY,
    location: { lat: 5.5600, lng: -0.2500 },
    address: '88 Market Rd, Tema',
    contact: '+233 24 777 8888',
    lastUpdated: '2023-11-15',
    isDuplicate: false,
    score: 89
  }
];

export const mockETLJobs: ETLJob[] = [
  {
    id: 'JOB-101',
    source: 'District Health Information System (DHIS2)',
    status: PipelineStatus.COMPLETED,
    recordsProcessed: 12450,
    startTime: '2023-11-20 08:00',
    errors: 12
  },
  {
    id: 'JOB-102',
    source: 'OSM Healthcare Import',
    status: PipelineStatus.PROCESSING,
    recordsProcessed: 5400,
    startTime: '2023-11-21 14:30',
    errors: 0
  },
  {
    id: 'JOB-103',
    source: 'UNICEF Facility Survey',
    status: PipelineStatus.FAILED,
    recordsProcessed: 890,
    startTime: '2023-11-19 10:15',
    errors: 45
  }
];
