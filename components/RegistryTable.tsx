import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, Filter, MoreHorizontal, AlertCircle, CheckCircle2, ChevronRight, Download } from 'lucide-react';
import { facilitiesApi } from '../services/api';
import { Facility } from '../types';

const RegistryTable: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);
  const requestIdRef = useRef(0);
  const [showFilters, setShowFilters] = useState(false);
  const [filterType, setFilterType] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [filterMinScore, setFilterMinScore] = useState<number | null>(null);
  
  useEffect(() => {
    isMountedRef.current = true;
    loadFacilities();
    
    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const loadFacilities = async () => {
    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    const currentRequestId = ++requestIdRef.current;
    
    try {
      setLoading(true);
      setError(null);
      const data = await facilitiesApi.getAll(abortController.signal);
      
      // Check if this request was cancelled or component unmounted
      if (abortController.signal.aborted || !isMountedRef.current || currentRequestId !== requestIdRef.current) {
        return;
      }
      
      // Ignore empty responses - retry with exponential backoff (Overpass API may be rate-limited)
      if (data.length === 0) {
        // Retry with exponential backoff - Overpass API may be rate-limited
        const maxRetries = 3;
        for (let retryAttempt = 1; retryAttempt <= maxRetries; retryAttempt++) {
          try {
            // Exponential backoff: 2s, 4s, 8s
            const delay = Math.min(2000 * Math.pow(2, retryAttempt - 1), 8000);
            await new Promise(resolve => setTimeout(resolve, delay));
            if (abortController.signal.aborted || !isMountedRef.current || currentRequestId !== requestIdRef.current) {
              return;
            }
            const retryData = await facilitiesApi.getAll(abortController.signal);
            if (abortController.signal.aborted || !isMountedRef.current || currentRequestId !== requestIdRef.current) {
              return;
            }
            if (retryData.length > 0) {
              setFacilities(retryData);
              setLoading(false);
              return;
            }
          } catch (retryErr) {
            if (abortController.signal.aborted || !isMountedRef.current || currentRequestId !== requestIdRef.current) {
              return;
            }
            // Continue to next retry attempt
          }
        }
        // If still empty after all retries, only set empty if we don't have existing data
        if (facilities.length === 0) {
          setFacilities([]);
        }
        setLoading(false);
        return;
      }
      
      setFacilities(data);
    } catch (err) {
      // Check if this request was cancelled
      if (abortController.signal.aborted || !isMountedRef.current || currentRequestId !== requestIdRef.current) {
        return;
      }
      
      // Don't show error for cancelled requests
      const isCancelled = err instanceof Error && (err.name === 'CanceledError' || err.message.includes('canceled') || err.message.includes('aborted'));
      if (isCancelled) {
        return;
      }
      
      setError('Failed to load facilities. Please try again.');
      console.error('Error loading facilities:', err);
    } finally {
      // Only update loading state if this is still the latest request
      if (currentRequestId === requestIdRef.current && isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      loadFacilities();
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const results = await facilitiesApi.search(query);
      setFacilities(results);
    } catch (err) {
      setError('Search failed. Please try again.');
      console.error('Error searching facilities:', err);
    } finally {
      setLoading(false);
    }
  };

  // Memoize filtered facilities to avoid recalculating on every render
  const filteredFacilities = useMemo(() => {
    return facilities.filter(facility => {
      if (filterType && facility.type !== filterType) return false;
      if (filterStatus === 'duplicate' && !facility.isDuplicate) return false;
      if (filterStatus === 'verified' && facility.isDuplicate) return false;
      if (filterMinScore !== null && facility.score < filterMinScore) return false;
      return true;
    });
  }, [facilities, filterType, filterStatus, filterMinScore]);

  const handleFilterButtonClick = () => {
    setShowFilters(!showFilters);
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom duration-500">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Facility Registry</h2>
          <p className="text-slate-500 text-sm">Manage and maintain the master facility list (MFL).</p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search by name or ID..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                handleSearch(e.target.value);
              }}
            />
          </div>
          <button 
            onClick={handleFilterButtonClick}
            className={`p-2 border rounded-xl transition-colors ${
              showFilters 
                ? 'bg-blue-50 border-blue-300 text-blue-600' 
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <Filter size={20} className={showFilters ? 'text-blue-600' : 'text-slate-600'} />
          </button>
          <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20">
            <Download size={18} />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
          {error}
        </div>
      )}

      <div 
        className={`bg-white p-4 rounded-2xl border border-slate-200 shadow-sm transition-all duration-200 ${showFilters ? 'block' : 'hidden'}`}
      >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">Facility Type</label>
              <select
                value={filterType || ''}
                onChange={(e) => {
                  setFilterType(e.target.value || null);
                }}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                <option value="">All Types</option>
                <option value="Hospital">Hospital</option>
                <option value="Clinic">Clinic</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">Status</label>
              <select
                value={filterStatus || ''}
                onChange={(e) => {
                  setFilterStatus(e.target.value || null);
                }}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                <option value="">All Status</option>
                <option value="verified">Verified</option>
                <option value="duplicate">Suspected Duplicate</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">Min Quality Score</label>
              <select
                value={filterMinScore !== null ? filterMinScore : ''}
                onChange={(e) => {
                  setFilterMinScore(e.target.value ? Number(e.target.value) : null);
                }}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                <option value="">No Minimum</option>
                <option value="50">50%</option>
                <option value="70">70%</option>
                <option value="90">90%</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => {
                setFilterType(null);
                setFilterStatus(null);
                setFilterMinScore(null);
              }}
              className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800"
            >
              Clear Filters
            </button>
          </div>
        </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-slate-500 mt-4">Loading facilities...</p>
          </div>
        ) : facilities.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No facilities found.
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Facility ID</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Facility Details</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Integrity</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredFacilities.map((facility) => (
                <tr key={facility.id} className="hover:bg-slate-50/50 transition-colors group">
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs font-medium text-slate-400 group-hover:text-blue-600 transition-colors">{facility.id}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-semibold text-slate-900">{facility.name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{facility.address}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs px-2.5 py-1 rounded-lg font-medium bg-slate-100 text-slate-600">
                      {facility.type}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${facility.score > 90 ? 'bg-emerald-500' : 'bg-amber-500'}`} 
                          style={{ width: `${facility.score}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-bold text-slate-700">{facility.score}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {facility.isDuplicate ? (
                      <div className="flex items-center gap-1.5 text-amber-600 bg-amber-50 px-2 py-1 rounded-lg w-fit">
                        <AlertCircle size={14} />
                        <span className="text-xs font-bold">Suspected Duplicate</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg w-fit">
                        <CheckCircle2 size={14} />
                        <span className="text-xs font-bold">Verified</span>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all">
                      <ChevronRight size={20} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default RegistryTable;