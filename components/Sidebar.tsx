
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Map as MapIcon, Database, Terminal, ShieldPlus } from 'lucide-react';
import { AppView } from '../types';
import { healthApi } from '../services/api';

interface SidebarProps {
  currentView: AppView;
  onViewChange: (view: AppView) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const [dbStatus, setDbStatus] = useState({
    connected: false,
    postgis_enabled: false,
    status: 'unknown',
    message: 'Checking...'
  });

  useEffect(() => {
    const checkDbHealth = async () => {
      try {
        const health = await healthApi.checkDatabaseHealth();
        setDbStatus(health);
      } catch (error) {
        console.error('Error checking database health:', error);
        setDbStatus({
          connected: false,
          postgis_enabled: false,
          status: 'error',
          message: 'Connection check failed'
        });
      }
    };
    
    checkDbHealth();
    const interval = setInterval(checkDbHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const statusColor = dbStatus.status === 'healthy' ? 'bg-emerald-500' : 
                      dbStatus.status === 'warning' ? 'bg-amber-500' : 
                      'bg-red-500';

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'map', label: 'Spatial Viewer', icon: MapIcon },
    { id: 'registry', label: 'Facility Registry', icon: Database },
    { id: 'etl', label: 'ETL Pipeline', icon: Terminal },
  ];

  return (
    <div className="w-64 bg-slate-900 text-slate-300 h-screen flex flex-col fixed left-0 top-0 shadow-xl z-50">
      <div className="p-6 flex items-center gap-3 border-b border-slate-800">
        <div className="bg-blue-600 p-2 rounded-lg">
          <ShieldPlus className="text-white w-6 h-6" />
        </div>
        <div>
          <h1 className="text-white font-bold text-lg leading-none">HealthPulse</h1>
          <p className="text-xs text-slate-500 mt-1">Registry v1.0.4</p>
        </div>
      </div>
      
      <nav className="flex-1 mt-6 px-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id as AppView)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
                  : 'hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-6 border-t border-slate-800">
        <div className="bg-slate-800/50 rounded-xl p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">DB Node Status</p>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${statusColor} ${dbStatus.status === 'healthy' ? 'animate-pulse' : ''}`}></div>
            <span className="text-sm text-slate-300">{dbStatus.message}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
