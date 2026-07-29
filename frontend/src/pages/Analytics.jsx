import React from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { endpoints } from "@/lib/api";
import { Bar } from "react-chartjs-2";

export default function Analytics() {
  const [heat, setHeat] = React.useState([]);
  const [assets, setAssets] = React.useState([]);
  const [routes, setRoutes] = React.useState([]);
  const [zones, setZones] = React.useState([]);

  React.useEffect(() => {
    Promise.all([endpoints.heatmap(), endpoints.assetUtil(), endpoints.routeAnalytics(), endpoints.zoneStats()])
      .then(([h, a, r, z]) => { setHeat(h.data.points); setAssets(a.data.assets); setRoutes(r.data.routes); setZones(z.data.zones); });
  }, []);

  const assetChart = {
    labels: assets.map(a => a.rake_type),
    datasets: [{
      label: "Rakes",
      data: assets.map(a => a.count),
      backgroundColor: "rgba(0,122,255,0.7)", borderRadius: 0,
    }],
  };

  const zoneLoad = {
    labels: zones.map(z => z.zone),
    datasets: [{
      label: "Load (tonnes)",
      data: zones.map(z => z.load),
      backgroundColor: zones.map(z => z.color),
      borderRadius: 0,
    }],
  };

  const chartOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
    scales: { x: { grid: { display: false }, ticks: { font: { size: 10 } } }, y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { font: { size: 10 } } } } };

  return (
    <div className="p-6 space-y-4" data-testid="analytics-page">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card-flat p-5 h-[420px]" data-testid="heatmap-card">
          <div className="flex justify-between items-center mb-3">
            <div>
              <div className="overline">Load Heatmap</div>
              <div className="font-heading text-[15px] mt-1">Top loading stations by tonnage</div>
            </div>
            <span className="text-xs font-mono text-white/50">{heat.length} nodes</span>
          </div>
          <div className="h-[340px]">
            <MapContainer center={[22.5, 79]} zoom={5} className="h-full w-full">
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OSM" />
              {heat.map(p => (
                <CircleMarker key={p.code} center={[p.lat, p.lng]}
                  radius={4 + p.intensity * 22}
                  pathOptions={{
                    color: p.intensity > 0.5 ? "#FF3B30" : (p.intensity > 0.2 ? "#FFD60A" : "#34C759"),
                    fillOpacity: 0.4, weight: 1,
                  }}>
                  <Popup>
                    <div className="font-mono text-xs">
                      <div className="font-semibold">{p.name}</div>
                      <div>Code: {p.code} · Zone: {p.zone}</div>
                      <div>Rakes: {p.rakes.toLocaleString()}</div>
                      <div>Load: {p.load_tonnes.toLocaleString()}t</div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </div>

        <div className="card-flat p-5 h-[420px]" data-testid="asset-card">
          <div className="overline">Asset Utilization</div>
          <div className="font-heading text-[15px] mt-1">Rake types deployed (FY 25-26)</div>
          <div className="h-[340px] mt-3"><Bar data={assetChart} options={chartOpts} /></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card-flat p-5 lg:col-span-2 h-[380px]" data-testid="zone-load-card">
          <div className="overline">Zone Load Distribution</div>
          <div className="font-heading text-[15px] mt-1">Cumulative tonnage per zone</div>
          <div className="h-[300px] mt-2"><Bar data={zoneLoad} options={chartOpts} /></div>
        </div>

        <div className="card-flat p-5 h-[380px] overflow-hidden" data-testid="top-routes-card">
          <div className="overline">Top OD Corridors</div>
          <div className="font-heading text-[15px] mt-1 mb-2">Ranked by load</div>
          <div className="overflow-y-auto scroll-thin h-[300px]">
            <table className="w-full text-xs font-mono">
              <thead className="text-white/50 sticky top-0 bg-[color:var(--bg-surface)]">
                <tr className="border-b border-white/10"><th className="text-left py-2">Route</th><th className="text-right">Rakes</th><th className="text-right">Load</th></tr>
              </thead>
              <tbody>
                {routes.map(r => (
                  <tr key={r.route} className="border-b border-white/5 hover:bg-white/5">
                    <td className="py-2">{r.origin} → {r.destination}</td>
                    <td className="text-right">{r.rakes}</td>
                    <td className="text-right">{(r.load / 1000).toFixed(0)}k</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
