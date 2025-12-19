import React, { useEffect, useRef, useState } from 'react';
import { facilitiesApi } from '../services/api';
import { analyzeSpatialDensity } from '../services/geminiService';
import { Sparkles, MapPin, Navigation } from 'lucide-react';
import { Facility } from '../types';

const MapView: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const leafletMap = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  useEffect(() => {
    loadFacilities();
  }, []);

  const loadFacilities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await facilitiesApi.getAll();
      setFacilities(data);
    } catch (err) {
      setError('Failed to load facilities. Please try again.');
      console.error('Error loading facilities:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initialize map when facilities are loaded
    if (facilities.length > 0 && typeof window !== 'undefined' && !leafletMap.current && mapRef.current) {
      const L = (window as any).L;
      if (L) {
        // Set default view to Malaysia (Kuala Lumpur area)
        leafletMap.current = L.map(mapRef.current).setView([3.1390, 101.6869], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(leafletMap.current);

        // Clear existing markers
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];

        // Add markers for each facility
        facilities.forEach(facility => {
          const marker = L.marker([facility.location.lat, facility.location.lng]).addTo(leafletMap.current);
          marker.bindPopup(`
            <div class="p-2">
              <h4 class="font-bold text-blue-600">${facility.name}</h4>
              <p class="text-xs text-slate-500">${facility.type}</p>
              <hr class="my-1"/>
              <p class="text-[10px]">${facility.address}</p>
            </div>
          `);
          markersRef.current.push(marker);
        });
      }
    }

    return () => {
      if (leafletMap.current) {
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, [facilities]);

  const handleAIAnalysis = async () => {
    if (facilities.length === 0) return;
    
    setIsAnalyzing(true);
    try {
      const result = await analyzeSpatialDensity(facilities);
      setAnalysis(result || "Unable to complete analysis.");
    } catch (err) {
      setAnalysis("Error during analysis. Please try again.");
      console.error('Error analyzing spatial density:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Spatial Analysis</h2>
          <p className="text-slate-500 text-sm">Visualizing health infrastructure distribution.</p>
        </div>
        <button
          onClick={handleAIAnalysis}
          disabled={isAnalyzing || facilities.length === 0}
          className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-blue-600 text-white px-5 py-2.5 rounded-xl shadow-lg hover:shadow-indigo-500/20 transition-all disabled:opacity-50"
        >
          {isAnalyzing ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Sparkles size={18} />
          )}
          {isAnalyzing ? "Analyzing Density..." : "Generate AI Insights"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
          {error}
        </div>
      )}

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
        <div className="lg:col-span-3 bg-white p-2 rounded-2xl border border-slate-200 shadow-sm overflow-hidden h-full">
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-500 mt-4">Loading map...</p>
              </div>
            </div>
          ) : (
            <div ref={mapRef} className="z-10 h-full" />
          )}
        </div>

        <div className="lg:col-span-1 space-y-4 overflow-y-auto pr-2">
          {analysis && (
            <div className="bg-indigo-50 border border-indigo-100 p-5 rounded-2xl animate-in slide-in-from-right duration-500">
              <div className="flex items-center gap-2 mb-3 text-indigo-700">
                <Sparkles size={20} />
                <h4 className="font-bold">AI Analysis Result</h4>
              </div>
              <p className="text-sm text-indigo-900 leading-relaxed italic">
                "{analysis}"
              </p>
            </div>
          )}

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <h4 className="font-bold mb-4 flex items-center gap-2">
              <Navigation className="text-blue-500" size={18} />
              Nearby Facilities
            </h4>
            {loading ? (
              <div className="text-center py-8 text-slate-500">
                <div className="inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : facilities.length === 0 ? (
              <div className="text-center py-8 text-slate-500">No facilities found.</div>
            ) : (
              <div className="space-y-3">
                {facilities.slice(0, 10).map(f => (
                  <div key={f.id} className="p-3 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-100 transition-all cursor-pointer group">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{f.type}</span>
                      <span className="text-[10px] text-slate-400">0.8km</span>
                    </div>
                    <h5 className="font-medium text-slate-900 mt-2 group-hover:text-blue-600 transition-colors">{f.name}</h5>
                    <p className="text-xs text-slate-500 mt-1 truncate">{f.address}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;