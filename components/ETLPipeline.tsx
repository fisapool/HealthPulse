import React, { useEffect, useState } from 'react';
import { Database, FileJson, ArrowRight, CheckCircle2, RefreshCw, XCircle, Info, Activity } from 'lucide-react';
import { etlApi } from '../services/api';
import { PipelineStatus, ETLJob } from '../types';

const ETLPipeline: React.FC = () => {
  const [jobs, setJobs] = useState<ETLJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
    // Optionally set up polling for real-time updates
    const interval = setInterval(loadJobs, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await etlApi.getAll();
      setJobs(data);
    } catch (err) {
      setError('Failed to load ETL jobs. Please try again.');
      console.error('Error loading ETL jobs:', err);
      // Don't show error if API endpoint doesn't exist yet
      if ((err as any)?.response?.status !== 404) {
        setError('Failed to load ETL jobs. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async () => {
    // Implementation for creating a new job
    // This would typically open a modal or navigate to a form
    console.log('Create new ETL job');
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">ETL Pipeline</h2>
          <p className="text-slate-500 text-sm">Ingestion and validation workflow status.</p>
        </div>
        <button 
          onClick={handleCreateJob}
          className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition-all font-medium"
        >
          <Activity size={18} />
          Launch New Job
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        <div className="hidden md:block absolute top-1/2 left-1/3 -translate-y-1/2 text-slate-300 z-0">
          <ArrowRight size={48} className="animate-pulse" />
        </div>
        <div className="hidden md:block absolute top-1/2 left-2/3 -translate-y-1/2 text-slate-300 z-0">
          <ArrowRight size={48} className="animate-pulse" />
        </div>

        {/* Step 1: Extraction */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm z-10">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
            <FileJson size={24} />
          </div>
          <h4 className="font-bold text-slate-900">Extraction</h4>
          <p className="text-sm text-slate-500 mt-2">Connecting to DHIS2 and legacy SQL databases to fetch raw JSON/CSV data.</p>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Sources Active</span>
              <span className="text-emerald-600 font-bold">12/12</span>
            </div>
          </div>
        </div>

        {/* Step 2: Transformation */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm z-10">
          <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
            <RefreshCw size={24} className="animate-spin-slow" />
          </div>
          <h4 className="font-bold text-slate-900">Cleaning & Deduplication</h4>
          <p className="text-sm text-slate-500 mt-2">Deduplicating via stable ID generation and Fuzzy-matching using Gemini AI.</p>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Avg. Conf Score</span>
              <span className="text-blue-600 font-bold">94.2%</span>
            </div>
          </div>
        </div>

        {/* Step 3: Loading */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm z-10">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <Database size={24} />
          </div>
          <h4 className="font-bold text-slate-900">PostGIS Loading</h4>
          <p className="text-sm text-slate-500 mt-2">Storing transformed records into PostgreSQL with spatial indexes enabled.</p>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Write Success</span>
              <span className="text-emerald-600 font-bold">99.8%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-bold">Recent Job History</h3>
          <Info size={16} className="text-slate-400" />
        </div>
        {error && (
          <div className="px-6 py-4 bg-yellow-50 border-b border-yellow-200 text-yellow-700 text-sm">
            {error}
          </div>
        )}
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-slate-500 mt-4">Loading job history...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No ETL jobs found. Create a new job to get started.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {jobs.map(job => (
              <div key={job.id} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${
                    job.status === PipelineStatus.COMPLETED ? 'bg-emerald-50 text-emerald-600' :
                    job.status === PipelineStatus.PROCESSING ? 'bg-blue-50 text-blue-600' : 'bg-red-50 text-red-600'
                  }`}>
                    {job.status === PipelineStatus.COMPLETED ? <CheckCircle2 size={24} /> :
                     job.status === PipelineStatus.PROCESSING ? <RefreshCw size={24} className="animate-spin" /> : <XCircle size={24} />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900">{job.source}</span>
                      <span className="text-xs font-mono text-slate-400">{job.id}</span>
                    </div>
                    <div className="text-sm text-slate-500 mt-1">Started at {job.startTime}</div>
                  </div>
                </div>
                <div className="flex items-center gap-8">
                  <div className="text-center">
                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Processed</div>
                    <div className="font-bold text-slate-900">{job.recordsProcessed.toLocaleString()}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Errors</div>
                    <div className={`font-bold ${job.errors > 0 ? 'text-red-600' : 'text-slate-900'}`}>{job.errors}</div>
                  </div>
                  <div className={`px-3 py-1 rounded-lg text-xs font-bold ${
                    job.status === PipelineStatus.COMPLETED ? 'bg-emerald-100 text-emerald-700' :
                    job.status === PipelineStatus.PROCESSING ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {job.status.toUpperCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ETLPipeline;