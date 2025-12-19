import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Users, MapPin, CheckCircle2, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { facilitiesApi, analyticsApi } from '../services/api';
import { Facility, FacilityType } from '../types';

const StatCard = ({ title, value, icon: Icon, color, trend }: any) => (
  <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-xl bg-${color}-50 text-${color}-600`}>
        <Icon size={24} />
      </div>
      {trend && (
        <span className="flex items-center gap-1 text-emerald-600 text-sm font-medium">
          {trend} <ArrowUpRight size={14} />
        </span>
      )}
    </div>
    <h3 className="text-slate-500 text-sm font-medium">{title}</h3>
    <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
  </div>
);

const Dashboard: React.FC = () => {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [stateData, setStateData] = useState<Array<{ name: string; facilities: number }>>([]);
  const [activeUsers, setActiveUsers] = useState<number>(0);
  const [facilityStats, setFacilityStats] = useState<{ total: number; hospitals: number; clinics: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch analytics (includes active users and facility stats)
        const analyticsData = await analyticsApi.getAnalytics();
        setActiveUsers(analyticsData.active_users || 0);
        setFacilityStats(analyticsData.facilities || null);
        
        // Fetch facilities for type chart
        const data = await facilitiesApi.getAll();
        setFacilities(data);
        
        // Fetch state data from API
        const states = await facilitiesApi.getByState();
        setStateData(states);
      } catch (err: any) {
        console.error('Error loading dashboard stats:', err);
        // Show user-friendly error message
        const errorMessage = err?.message || 'Failed to load facilities';
        setError(errorMessage);
        // If it's a 503 error (service unavailable), show a helpful message
        if (err?.response?.status === 503 || errorMessage.includes('temporarily unavailable')) {
          setError('Overpass API is temporarily unavailable. Please try again in a few moments.');
        }
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  // Use analytics stats for total count (correct), fallback to array length if stats not available
  const totalFacilities = facilityStats?.total ?? facilities.length;
  const duplicates = facilities.filter(f => f.isDuplicate).length;
  
  const typeData = facilities.reduce((acc, facility) => {
    const type = facility.type;
    // Use enum comparison instead of string
    if (type === FacilityType.HOSPITAL || type === FacilityType.CLINIC) {
      const existing = acc.find(item => item.name === type);
      if (existing) {
        existing.value += 1;
      } else {
        acc.push({ name: type, value: 1 });
      }
    }
    return acc;
  }, [] as { name: string; value: number }[]);


  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <h2 className="text-3xl font-bold text-slate-900">Registry Analytics</h2>
        <p className="text-slate-500 mt-1">Real-time health facility distribution and quality metrics.</p>
      </header>

      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="text-amber-600" size={20} />
          <div>
            <p className="text-amber-800 font-medium">{error}</p>
            <p className="text-amber-700 text-sm mt-1">The data service may be temporarily busy. Please refresh the page to try again.</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Facilities" value={loading ? '...' : totalFacilities.toLocaleString()} icon={MapPin} color="blue" />
        <StatCard title="Cleaned Records" value={loading ? '...' : (totalFacilities - duplicates).toLocaleString()} icon={CheckCircle2} color="emerald" />
        <StatCard title="Potential Duplicates" value={loading ? '...' : duplicates.toLocaleString()} icon={AlertTriangle} color="amber" />
        <StatCard title="Active Users" value={loading ? '...' : activeUsers.toString()} icon={Users} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold mb-6">Facilities by State</h3>
          <div className="h-80">
            {loading ? <div className="text-center p-10">Loading...</div> :
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                <Tooltip 
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="facilities" fill="#3b82f6" radius={[6, 6, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
            }
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold mb-6">Infrastructure Mix</h3>
          <div className="h-80 relative">
          {loading ? <div className="text-center p-10">Loading...</div> :
            <>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold text-slate-900">{typeData.length}</span>
              <span className="text-xs text-slate-500">Categories</span>
            </div>
            </>
          }
          </div>
          <div className="space-y-3 mt-4">
            {typeData.map((item, idx) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[idx] }}></div>
                  <span className="text-slate-600">{item.name}</span>
                </div>
                <span className="font-semibold text-slate-900">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
