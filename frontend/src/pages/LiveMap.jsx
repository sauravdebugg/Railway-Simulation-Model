import React from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, LayersControl, LayerGroup } from "react-leaflet";
import L from "leaflet";
import { endpoints } from "@/lib/api";

// Fix default marker icon paths — not required with CircleMarker but safe
delete L.Icon.Default.prototype._getIconUrl;

const RAKE_COLOR = "#5AC8FA";

export default function LiveMap() {
  const [trains, setTrains] = React.useState([]);
  const [stations, setStations] = React.useState([]);
  const [routes, setRoutes] = React.useState([]);
  const [zones, setZones] = React.useState([]);
  const [selected, setSelected] = React.useState(null);
  const [filter, setFilter] = React.useState("all");

  const load = React.useCallback(async () => {
    const [t, s, c, z] = await Promise.all([
      endpoints.trains({ limit: 200 }),
      endpoints.stations(undefined, 400),
      endpoints.congestion(),
      endpoints.zones(),
    ]);
    setTrains(t.data.trains);
    setStations(s.data.stations.slice(0, 250));
    setRoutes(c.data.sections);
    setZones(z.data.zones);
  }, []);

  React.useEffect(() => {
    load();
    const h = () => load();
    window.addEventListener("live-refresh", h);
    return () => window.removeEventListener("live-refresh", h);
  }, [load]);

  const topZones = React.useMemo(() => zones.slice(0, 6).map(z => z.code), [zones]);
  const filtered = filter === "all" ? trains : trains.filter(t => t.zone === filter);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] h-full min-h-[calc(100vh-56px)]" data-testid="live-map-page">
      <div className="relative">
        <MapContainer center={[22.5, 79.0]} zoom={5} className="h-full w-full" style={{ minHeight: "80vh" }} scrollWheelZoom>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap' />
          <LayersControl position="topright">
            <LayersControl.Overlay checked name="Stations">
              <LayerGroup>
                {stations.map(s => (
                  <CircleMarker key={s.code} center={[s.lat, s.lng]} radius={3}
                    pathOptions={{ color: "#5AC8FA", weight: 1, fillOpacity: 0.6 }}>
                    <Popup>
                      <div className="font-mono text-xs">
                        <div className="font-semibold">{s.name || s.code}</div>
                        <div>Code: {s.code}</div>
                        <div>Zone: {s.zone} · Div: {s.division}</div>
                        <div>State: {s.state}</div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>

            <LayersControl.Overlay checked name="Freight Routes">
              <LayerGroup>
                {routes.map(c => (
                  <Polyline key={c.section_id} positions={[[c.from_lat, c.from_lng], [c.to_lat, c.to_lng]]}
                    pathOptions={{ color: "#007AFF", weight: 1 + c.congestion * 3, opacity: 0.5 }}>
                    <Popup>
                      <div className="font-mono text-xs">
                        <div className="font-semibold">{c.section_id}</div>
                        <div>Rakes (FY): {c.rakes_year}</div>
                        <div>Avg Speed: {c.avg_speed_kmph} km/h</div>
                      </div>
                    </Popup>
                  </Polyline>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>

            <LayersControl.Overlay checked name="Live Rakes">
              <LayerGroup>
                {filtered.map(t => (
                  <CircleMarker key={t.id} center={[t.current_lat, t.current_lng]} radius={6}
                    pathOptions={{ color: RAKE_COLOR, fillColor: RAKE_COLOR, fillOpacity: 0.9, weight: 2 }}
                    eventHandlers={{ click: () => setSelected(t) }}>
                    <Popup>
                      <div className="font-mono text-xs">
                        <div className="font-semibold">{t.name}</div>
                        <div>Rake: {t.number}</div>
                        <div>Progress: {Math.round(t.progress * 100)}%</div>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>
          </LayersControl>
        </MapContainer>

        <div className="absolute top-3 left-3 z-[500] flex gap-2 bg-black/60 backdrop-blur border border-white/10 p-1 flex-wrap max-w-[80vw]" data-testid="map-filter">
          <button onClick={() => setFilter("all")} data-testid="filter-all"
            className={`px-3 py-1.5 text-[10px] uppercase tracking-widest font-mono ${filter === "all" ? "bg-white/15 text-white" : "text-white/60 hover:text-white"}`}>
            all
          </button>
          {topZones.map(z => (
            <button key={z} onClick={() => setFilter(z)}
              data-testid={`filter-${z}`}
              className={`px-3 py-1.5 text-[10px] uppercase tracking-widest font-mono ${filter === z ? "bg-white/15 text-white" : "text-white/60 hover:text-white"}`}>
              {z}
            </button>
          ))}
        </div>
      </div>

      <aside className="border-l border-white/10 bg-[color:var(--bg-surface)] flex flex-col min-h-[80vh]" data-testid="train-detail-panel">
        {selected ? (
          <div className="p-5 flex flex-col gap-3">
            <div>
              <div className="overline">Rake · {selected.number}</div>
              <div className="font-heading text-lg mt-1 leading-tight">{selected.name}</div>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="font-mono uppercase tracking-widest text-white/70">Zone {selected.zone}</span>
              <span className="ml-auto font-mono text-white/50">progress {Math.round(selected.progress * 100)}%</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono mt-1">
              <div className="border border-white/10 p-2"><div className="overline">origin</div><div>{selected.origin}</div></div>
              <div className="border border-white/10 p-2"><div className="overline">destination</div><div>{selected.destination}</div></div>
              <div className="border border-white/10 p-2"><div className="overline">commodity</div><div>{selected.commodity}</div></div>
              <div className="border border-white/10 p-2"><div className="overline">loadtype</div><div>{selected.loadtype}</div></div>
              <div className="border border-white/10 p-2"><div className="overline">wagons</div><div>{selected.wagons}</div></div>
              <div className="border border-white/10 p-2"><div className="overline">load</div><div>{selected.load_tonnes}t</div></div>
              <div className="border border-white/10 p-2"><div className="overline">distance</div><div>{selected.distance_total_km} km</div></div>
              <div className="border border-white/10 p-2"><div className="overline">avg speed</div><div>{selected.speed_kmph} km/h</div></div>
              <div className="border border-white/10 p-2 col-span-2"><div className="overline">consignor → consignee</div><div>{selected.consignor} → {selected.consignee || "—"}</div></div>
            </div>
            <div className="mt-2">
              <div className="overline mb-2">Route ({selected.via?.length} nodes)</div>
              <div className="text-[11px] font-mono text-white/70 border border-white/10 p-2 max-h-40 overflow-auto scroll-thin">
                {selected.via?.join(" → ")}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-5">
            <div className="overline">Live Rakes · {filtered.length}</div>
            <div className="font-heading text-[15px] mt-1">Select a rake on the map</div>
            <div className="mt-4 space-y-2 max-h-[70vh] overflow-y-auto scroll-thin">
              {filtered.slice(0, 40).map(t => (
                <button key={t.id} onClick={() => setSelected(t)} data-testid={`rake-row-${t.number}`}
                  className="w-full text-left border border-white/10 hover:border-white/30 p-3 flex items-start gap-3 transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-[11px] text-white/50">#{t.number} · {t.commodity_code}</div>
                    <div className="text-[13px] truncate">{t.origin} → {t.destination}</div>
                    <div className="text-[11px] text-white/50 font-mono">{t.load_tonnes}t · {t.distance_total_km}km</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
