import React, { useEffect, useRef, useState, useMemo } from 'react';
import { facilitiesApi } from '../services/api';
import { analyzeSpatialDensity } from '../services/geminiService';
import { Sparkles, MapPin, Navigation } from 'lucide-react';
import { Facility, Coordinates } from '../types';

// Haversine formula to calculate distance between two coordinates in kilometers
const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

// Format distance for display
const formatDistance = (distanceKm: number): string => {
  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)}m`;
  }
  return `${distanceKm.toFixed(1)}km`;
};

const MapView: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const leafletMap = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const selectedLocationMarkerRef = useRef<any>(null);
  // Default to Kuala Lumpur center
  const [selectedLocation, setSelectedLocation] = useState<Coordinates>({ lat: 3.1390, lng: 101.6869 });
  const [proximityRadius, setProximityRadius] = useState<number>(50); // Default 50km radius

  // Calculate distances and filter facilities by proximity
  const nearbyFacilities = useMemo(() => {
    const facilitiesWithDistance = facilities.map(facility => {
      const distance = calculateDistance(
        selectedLocation.lat,
        selectedLocation.lng,
        facility.location.lat,
        facility.location.lng
      );
      return { facility, distance };
    });

    // Filter by radius and sort by distance
    const filtered = facilitiesWithDistance
      .filter(item => item.distance <= proximityRadius)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 10); // Limit to top 10 nearest

    return filtered;
  }, [facilities, selectedLocation, proximityRadius]);

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

  // Use callback ref to initialize map when element is available
  const mapContainerRef = React.useCallback((node: HTMLDivElement | null) => {
    // Always update the ref
    if (mapRef.current !== node) {
      (mapRef as any).current = node;
    }
    
    // Initialize map if node is available and map doesn't exist
    // Note: If this callback is called, the div is rendered, which means loading is false
    if (node && !leafletMap.current && typeof window !== 'undefined') {
      const L = (window as any).L;
      
      if (L) {
        try {
          // Set default view to Malaysia (Kuala Lumpur area)
          leafletMap.current = L.map(node).setView([selectedLocation.lat, selectedLocation.lng], 7);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
          }).addTo(leafletMap.current);

          // Add click handler to select location
          leafletMap.current.on('click', (e: any) => {
            const { lat, lng } = e.latlng;
            setSelectedLocation({ lat, lng });
          });
        } catch (error: any) {
          console.error('Failed to create map:', error);
        }
      } else {
        // Dynamically load Leaflet JS (fallback - should already be loaded from index.html)
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.crossOrigin = 'anonymous';
        script.onload = () => {
          // Retry map initialization after script loads
          if (node && !leafletMap.current) {
            const L = (window as any).L;
            if (L) {
              try {
                leafletMap.current = L.map(node).setView([selectedLocation.lat, selectedLocation.lng], 7);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                  attribution: '&copy; OpenStreetMap contributors'
                }).addTo(leafletMap.current);

                leafletMap.current.on('click', (e: any) => {
                  const { lat, lng } = e.latlng;
                  setSelectedLocation({ lat, lng });
                });
              } catch (error: any) {
                console.error('Failed to create map after script load:', error);
              }
            }
          }
        };
        script.onerror = () => {
          console.error('Failed to load Leaflet script');
        };
        document.head.appendChild(script);
      }
    }
  }, [selectedLocation]);

  // Fallback useEffect for cases where callback ref doesn't work
  useEffect(() => {
    // Don't initialize if still loading (mapRef div not rendered yet)
    if (loading || leafletMap.current) {
      return;
    }
    
    // Wait for mapRef to be available (React may not have attached it yet)
    const initMap = () => {
      if (typeof window !== 'undefined' && !leafletMap.current && mapRef.current) {
        const L = (window as any).L;
        
        if (L) {
          try {
            // Set default view to Malaysia (Kuala Lumpur area)
            leafletMap.current = L.map(mapRef.current).setView([selectedLocation.lat, selectedLocation.lng], 7);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '&copy; OpenStreetMap contributors'
            }).addTo(leafletMap.current);

            // Add click handler to select location
            leafletMap.current.on('click', (e: any) => {
              const { lat, lng } = e.latlng;
              setSelectedLocation({ lat, lng });
            });
          } catch (error: any) {
            console.error('Failed to create map:', error);
          }
        }
      }
    };

    // Try immediately
    initMap();
    
    // If ref not available, wait a bit and retry (React may not have attached ref yet)
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    if (!mapRef.current) {
      timeoutId = setTimeout(() => {
        initMap();
      }, 100);
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (leafletMap.current) {
        if (selectedLocationMarkerRef.current) {
          selectedLocationMarkerRef.current.remove();
          selectedLocationMarkerRef.current = null;
        }
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, [loading, selectedLocation]);

  // Update selected location marker when location changes
  useEffect(() => {
    if (leafletMap.current && typeof window !== 'undefined') {
      const L = (window as any).L;
      if (L) {
        if (selectedLocationMarkerRef.current) {
          selectedLocationMarkerRef.current.setLatLng([selectedLocation.lat, selectedLocation.lng]);
        } else {
          const selectedIcon = L.divIcon({
            className: 'selected-location-marker',
            html: '<div style="width: 20px; height: 20px; border-radius: 50%; background: #3b82f6; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          });
          selectedLocationMarkerRef.current = L.marker([selectedLocation.lat, selectedLocation.lng], { icon: selectedIcon, zIndexOffset: 1000 })
            .addTo(leafletMap.current)
            .bindPopup('Selected Location<br/>Click map to change');
        }
      }
    }
  }, [selectedLocation]);

  // Add facility markers when facilities change
  useEffect(() => {
    if (facilities.length > 0 && leafletMap.current && typeof window !== 'undefined') {
      const L = (window as any).L;
      if (L) {
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
            <div 
              ref={(node) => {
                // Update both refs
                (mapRef as any).current = node;
                if (node) {
                  mapContainerRef(node);
                }
              }} 
              className="z-10 h-full" 
            />
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
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-bold flex items-center gap-2">
                <Navigation className="text-blue-500" size={18} />
                Nearby Facilities
              </h4>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-500">Radius:</label>
                <select
                  value={proximityRadius}
                  onChange={(e) => {
                    setProximityRadius(Number(e.target.value));
                  }}
                  className="text-xs border border-slate-200 rounded px-2 py-1"
                >
                  <option value={10}>10km</option>
                  <option value={25}>25km</option>
                  <option value={50}>50km</option>
                  <option value={100}>100km</option>
                </select>
              </div>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Click on the map to select a location
            </p>
            {loading ? (
              <div className="text-center py-8 text-slate-500">
                <div className="inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : nearbyFacilities.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                No facilities found within {proximityRadius}km.
              </div>
            ) : (
              <div className="space-y-3">
                {nearbyFacilities.map(({ facility, distance }) => (
                  <div 
                    key={facility.id} 
                    className="p-3 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-100 transition-all cursor-pointer group"
                    onClick={() => {
                      if (leafletMap.current) {
                        leafletMap.current.setView([facility.location.lat, facility.location.lng], 13);
                      }
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{facility.type}</span>
                      <span className="text-[10px] text-slate-400 font-medium">{formatDistance(distance)}</span>
                    </div>
                    <h5 className="font-medium text-slate-900 mt-2 group-hover:text-blue-600 transition-colors">{facility.name}</h5>
                    <p className="text-xs text-slate-500 mt-1 truncate">{facility.address}</p>
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