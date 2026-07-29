import React from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap } from "react-leaflet";
import { endpoints } from "@/lib/api";

const RouteViewport = ({ points }) => {
  const map = useMap();

  React.useEffect(() => {
    if (!points.length) return;
    const bounds = points.map(point => [point.lat, point.lng]);
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
  }, [map, points]);

  return null;
};

export default function Simulation() {
  const [pairs, setPairs] = React.useState([]);
  const [origin, setOrigin] = React.useState("");
  const [destination, setDestination] = React.useState("");
  const [commodity, setCommodity] = React.useState("Coal");
  const [tonnes, setTonnes] = React.useState(3500);
  const [priority, setPriority] = React.useState(2);
  const [result, setResult] = React.useState(null);
  const [conflicts, setConflicts] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    endpoints.sampleOdPairs().then(r => {
      const d = r.data;
      setPairs(d.pairs || []);
      if (d.pairs?.[0]) {
        setOrigin(d.pairs[0].origin); setDestination(d.pairs[0].destination); setCommodity(d.pairs[0].commodity);
      }
    }).catch(() => setErr("Unable to load route presets"));
    endpoints.conflicts().then(r => setConflicts(r.data.conflicts));
  }, []);

  const runSim = async () => {
    setLoading(true); setErr(""); setResult(null);
    try {
      const r = await endpoints.simulate({ origin, destination, commodity, tonnes: Number(tonnes), priority: Number(priority) });
      setResult(r.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "Simulation failed");
    } finally { setLoading(false); }
  };

  const { displayPath, isSchematic } = React.useMemo(() => {
    const path = result?.path?.coordinates || [];
    const routeCodes = result?.path?.path || [];
    const hasGeographicRoute = path.length > 1 && path.some((point, index) => {
      if (index === 0) return false;
      return Math.abs(point.lat - path[0].lat) > 0.001
        || Math.abs(point.lng - path[0].lng) > 0.001;
    });
    const schematic = Boolean(result) && !hasGeographicRoute && path.length > 0;
    if (!schematic) return { displayPath: path, isSchematic: false };
    const start = path[0];
    const pointCount = Math.max(routeCodes.length, 2);
    const distanceDegrees = Math.min(
      Math.max((result?.path?.distance_km || 5) / 111, 0.025),
      0.35,
    );
    const points = Array.from({ length: pointCount }, (_, index) => {
      const progress = index / (pointCount - 1);
      const code = routeCodes[index] || (index === pointCount - 1 ? result.path.destination : start.code);
      return {
        code,
        name: code,
        lat: start.lat + Math.sin(Math.PI * progress) * distanceDegrees * 0.35,
        lng: start.lng + progress * distanceDegrees,
      };
    });
    return { displayPath: points, isSchematic: true };
  }, [result]);

  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4" data-testid="simulation-page">
      <div className="card-flat p-5 space-y-4">
        <div>
          <div className="overline">Freight Simulation</div>
          <div className="font-heading text-lg mt-1">Rake allocation & path planning</div>
        </div>

        <div>
          <label className="overline">Preset OD pair</label>
          <select value={`${origin}|${destination}`} data-testid="preset-od"
            onChange={e => { const [o, d] = e.target.value.split("|"); setOrigin(o); setDestination(d); }}
            className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono">
            {pairs.map(p => (
              <option key={`${p.origin}-${p.destination}-${p.commodity_code}`} value={`${p.origin}|${p.destination}`}>
                {p.origin} → {p.destination} · {p.commodity} · {p.rakes} rakes/yr
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="overline">Origin</label>
            <input value={origin} onChange={e => setOrigin(e.target.value.toUpperCase())} data-testid="origin-input"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono" />
          </div>
          <div>
            <label className="overline">Destination</label>
            <input value={destination} onChange={e => setDestination(e.target.value.toUpperCase())} data-testid="destination-input"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="overline">Commodity</label>
            <input value={commodity} onChange={e => setCommodity(e.target.value)} data-testid="commodity-input"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm" />
          </div>
          <div>
            <label className="overline">Tonnes</label>
            <input type="number" value={tonnes} onChange={e => setTonnes(e.target.value)} data-testid="tonnes-input"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono" />
          </div>
        </div>

        <div>
          <label className="overline">Priority (1=high, 3=low)</label>
          <div className="flex gap-2 mt-1">
            {[1, 2, 3].map(p => (
              <button key={p} onClick={() => setPriority(p)} data-testid={`priority-${p}`}
                className={`flex-1 py-2 text-sm font-mono border ${priority === p ? "border-[color:var(--accent-blue)] bg-[color:var(--accent-blue)]/10 text-white" : "border-white/10 text-white/60"}`}>P{p}</button>
            ))}
          </div>
        </div>

        <button onClick={runSim} disabled={loading || !origin || !destination} data-testid="run-sim-btn"
          className="w-full bg-[color:var(--accent-blue)] hover:brightness-110 py-3 text-sm uppercase tracking-widest font-mono disabled:opacity-40">
          {loading ? "Simulating…" : "Run Simulation"}
        </button>

        {err && <div className="text-[color:var(--accent-crit)] text-xs font-mono" data-testid="sim-error">{err}</div>}

        {result && (
          <div className="border-t border-white/10 pt-4 space-y-3 text-sm" data-testid="sim-result">
            <div>
              <div className="overline">Optimal Path</div>
              <div className="font-mono text-xs mt-1 border border-white/10 p-2 max-h-24 overflow-auto scroll-thin">{result.path.path.join(" → ")}</div>
            </div>
            <div className="grid grid-cols-2 gap-2 font-mono text-xs">
              <div className="border border-white/10 p-2"><div className="overline">distance</div><div>{result.path.distance_km} km</div></div>
              <div className="border border-white/10 p-2"><div className="overline">hops</div><div>{result.path.hops}</div></div>
              <div className="border border-white/10 p-2"><div className="overline">ML ETA</div><div>{result.eta.eta_hours} h</div></div>
              <div className="border border-white/10 p-2"><div className="overline">circuit</div><div>{result.circuit.circuit_hours} h</div></div>
              <div className="border border-white/10 p-2 col-span-2"><div className="overline">Rakes allocated</div><div>{result.allocation.rakes_needed} × 58 wagons · {result.allocation.total_capacity.toLocaleString()}t cap</div></div>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4 min-w-0">
        <div className="card-flat overflow-hidden h-[420px] relative" data-testid="sim-map">
          <MapContainer center={[22.5, 79]} zoom={5} className="h-full w-full">
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
            {displayPath.length > 0 && (
              <>
                <RouteViewport points={displayPath} />
                <Polyline positions={displayPath.map(p => [p.lat, p.lng])}
                  pathOptions={{
                    color: isSchematic ? "#FF9500" : "#007AFF",
                    weight: 4,
                    opacity: 0.9,
                    dashArray: isSchematic ? "8 8" : undefined,
                  }} />
                {displayPath.map((p, i) => (
                  <CircleMarker key={p.code + i} center={[p.lat, p.lng]}
                    radius={i === 0 || i === displayPath.length - 1 ? 8 : 4}
                    pathOptions={{ color: i === 0 ? "#34C759" : (i === displayPath.length - 1 ? "#FF3B30" : "#007AFF"), fillOpacity: 0.9, weight: 2 }}>
                    <Popup><div className="font-mono text-xs">{p.name}<br />{p.code}</div></Popup>
                  </CircleMarker>
                ))}
              </>
            )}
          </MapContainer>
          {isSchematic && (
            <div className="absolute z-[500] top-3 right-3 bg-black/80 border border-[#FF9500]/50 px-3 py-2 text-[10px] font-mono text-[#FFB340]">
              SCHEMATIC ROUTE · SOURCE COORDINATES OVERLAP
            </div>
          )}
        </div>

        <div className="card-flat p-5" data-testid="conflict-panel">
          <div className="flex justify-between items-center mb-3">
            <div>
              <div className="overline">Conflict Detection</div>
              <div className="font-heading text-[15px] mt-1">Section-level conflicts in live network</div>
            </div>
            <span className="text-xs font-mono text-white/60">{conflicts.length} detected</span>
          </div>
          {conflicts.length === 0 ? (
            <div className="text-white/50 text-sm font-mono">No conflicts detected — network is clear.</div>
          ) : (
            <div className="max-h-56 overflow-auto scroll-thin border border-white/10 divide-y divide-white/10">
              {conflicts.slice(0, 20).map((c, i) => (
                <div key={i} className="p-3 flex items-center gap-3 text-xs font-mono" data-testid={`conflict-${i}`}>
                  <span className={`status-dot ${c.severity === "high" ? "status-critical" : "status-delayed"}`} />
                  <div className="flex-1">
                    <div>{c.section} · Rake {c.train_a} vs {c.train_b}</div>
                    <div className="text-white/50 text-[10px]">{c.recommendation}</div>
                  </div>
                  <div className="text-white/60">{c.gap_minutes}m gap</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
