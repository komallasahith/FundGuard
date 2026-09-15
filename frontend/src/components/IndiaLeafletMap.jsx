import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import indiaGeojson from '../data/india_states_real.js';

function normalizeName(str) {
  return String(str || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]/g, '');
}

export default function IndiaLeafletMap({
  statesData = [],
  selectedState,
  onSelectState
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const geojsonLayerRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    // Initialize Leaflet map centered over India
    const map = L.map(mapContainerRef.current, {
      center: [22.5937, 78.9629],
      zoom: 4.6,
      minZoom: 4,
      maxZoom: 9,
      zoomControl: true,
      attributionControl: false
    });

    // Clean CartoDB Positron tiles for GovTech light aesthetics
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd'
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update GeoJSON layer when statesData or selectedState changes
  useEffect(() => {
    if (!mapInstanceRef.current || !indiaGeojson) return;

    if (geojsonLayerRef.current) {
      mapInstanceRef.current.removeLayer(geojsonLayerRef.current);
    }

    const stateMap = new Map();
    for (const item of statesData) {
      const key = normalizeName(item.state_name || item.state);
      if (key) stateMap.set(key, item);
    }

    const getColor = (name, isSelected) => {
      if (isSelected) return '#1d4ed8';
      const key = normalizeName(name);
      const data = stateMap.get(key);
      const candidates = Number(data?.candidates || 0);
      if (candidates > 500) return '#dc2626';
      if (candidates > 200) return '#ea580c';
      if (candidates > 50) return '#d97706';
      if (candidates > 0) return '#3b82f6';
      return '#94a3b8';
    };

    const layer = L.geoJSON(indiaGeojson, {
      style: (feature) => {
        const name = feature.properties.NAME_1;
        const isSelected = selectedState && normalizeName(selectedState) === normalizeName(name);
        return {
          fillColor: getColor(name, isSelected),
          weight: isSelected ? 3 : 1.5,
          opacity: 1,
          color: isSelected ? '#1e293b' : '#ffffff',
          fillOpacity: isSelected ? 0.85 : 0.65
        };
      },
      onEachFeature: (feature, featureLayer) => {
        const name = feature.properties.NAME_1;
        const key = normalizeName(name);
        const data = stateMap.get(key);
        const candidates = Number(data?.candidates || 0);
        const total = Number(data?.analyzed_works || data?.total_works || 0);

        featureLayer.bindTooltip(`
          <div style="font-family: sans-serif; padding: 4px 6px;">
            <strong style="font-size: 13px; color: #0f172a;">${name}</strong><br/>
            <span style="font-size: 11px; color: #64748b;">Flagged Candidates: <b style="color: #dc2626;">${candidates.toLocaleString()}</b></span><br/>
            <span style="font-size: 11px; color: #64748b;">Total Works: <b>${total.toLocaleString()}</b></span>
          </div>
        `, { sticky: true, className: 'leaflet-gov-tooltip' });

        featureLayer.on({
          mouseover: (e) => {
            const l = e.target;
            l.setStyle({
              weight: 2.5,
              color: '#0f172a',
              fillOpacity: 0.85
            });
            l.bringToFront();
          },
          mouseout: (e) => {
            layer.resetStyle(e.target);
          },
          click: () => {
            onSelectState && onSelectState(name);
          }
        });
      }
    }).addTo(mapInstanceRef.current);

    geojsonLayerRef.current = layer;
  }, [statesData, selectedState, onSelectState]);

  return (
    <div style={{ width: '100%', height: '580px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #cbd5e1' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
}
