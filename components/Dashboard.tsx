import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Users, MapPin, CheckCircle2, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { facilitiesApi } from '../services/api';
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const data = await facilitiesApi.getAll();
        setFacilities(data);
      } catch (err) {
        console.error('Error loading dashboard stats:', err);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  const totalFacilities = facilities.length;
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

  const regionData = facilities.reduce((acc, facility) => {
    // This is a placeholder for region, as it's not in the Facility type.
    // We'll simulate it based on the address for demonstration.
    const region = facility.address.split(',').pop()?.trim() || 'Unknown';
    const existing = acc.find(item => item.name === region);
    if (existing) {
      existing.facilities += 1;
    } else {
      acc.push({ name: region, facilities: 1 });
    }
    return acc;
  }, [] as { name: string; facilities: number }[]);


  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <h2 className="text-3xl font-bold text-slate-900">Registry Analytics</h2>
        <p className="text-slate-500 mt-1">Real-time health facility distribution and quality metrics.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Facilities" value={loading ? '...' : totalFacilities.toLocaleString()} icon={MapPin} color="blue" />
        <StatCard title="Cleaned Records" value={loading ? '...' : (totalFacilities - duplicates).toLocaleString()} icon={CheckCircle2} color="emerald" />
        <StatCard title="Potential Duplicates" value={loading ? '...' : duplicates.toLocaleString()} icon={AlertTriangle} color="amber" />
        <StatCard title="Active Users" value="24" icon={Users} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold mb-6">Facilities by Region</h3>
          <div className="h-80">
            {loading ? <div className="text-center p-10">Loading...</div> :
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regionData}>
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
