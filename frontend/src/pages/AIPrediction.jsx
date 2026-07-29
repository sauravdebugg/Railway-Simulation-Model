import React from "react";
import { endpoints } from "@/lib/api";
import { Line } from "react-chartjs-2";

const FIELDS = [
  { k: "distance_km", label: "Distance (km)", type: "number", min: 10, max: 3000, step: 10 },
  { k: "wagons", label: "Wagons", type: "number", min: 40, max: 60, step: 1 },
  { k: "loaded_pct", label: "Load %", type: "number", min: 40, max: 100, step: 1 },
  { k: "priority", label: "Priority (1-3)", type: "number", min: 1, max: 3, step: 1 },
  { k: "congestion", label: "Congestion (0-1)", type: "number", min: 0, max: 1, step: 0.05 },
  { k: "weather", label: "Weather (0-1)", type: "number", min: 0, max: 1, step: 0.05 },
  { k: "is_dfc", label: "DFC (0/1)", type: "number", min: 0, max: 1, step: 1 },
];

export default function AIPrediction() {
  const [input, setInput] = React.useState({
    distance_km: 800, wagons: 58, loaded_pct: 90, priority: 2, congestion: 0.4, weather: 0.2, is_dfc: 1,
  });
  const [eta, setEta] = React.useState(null);
  const [circuit, setCircuit] = React.useState(null);
  const [util, setUtil] = React.useState(null);
  const [cong, setCong] = React.useState(null);
  const [demand, setDemand] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  const upd = (k, v) => setInput(s => ({ ...s, [k]: k === "loaded_pct" || k === "distance_km" ? Number(v) : (k === "congestion" || k === "weather" ? Number(v) : parseInt(v || 0)) }));

  const run = async () => {
    setLoading(true);
    try {
      const [e, c, u, cn, d] = await Promise.all([
        endpoints.predictEta(input), endpoints.predictCircuit(input),
        endpoints.predictUtil(input), endpoints.predictCong(input),
        endpoints.predictDemand({ current_tonnes: 15000, growth_pct: 6, seasonality: 0.1, horizon_days: 30 }),
      ]);
      setEta(e.data); setCircuit(c.data); setUtil(u.data); setCong(cn.data); setDemand(d.data);
    } finally { setLoading(false); }
  };

  // Run once on mount; subsequent predictions are user-triggered.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  React.useEffect(() => { run(); }, []);

  const demandChart = demand && {
    labels: demand.forecast.map((_, i) => `D${i + 1}`),
    datasets: [{
      label: "Forecast (tonnes)",
      data: demand.forecast,
      borderColor: "#007AFF", backgroundColor: "rgba(0,122,255,0.15)",
      fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2,
    }],
  };

  const Contribs = ({ list }) => (
    <div className="mt-2 space-y-1">
      {list.map(c => (
        <div key={c.feature} className="flex items-center gap-2">
          <div className="text-[10px] font-mono text-white/60 w-24">{c.feature}</div>
          <div className="flex-1 h-1 bg-white/10">
            <div className="h-full bg-[color:var(--accent-blue)]" style={{ width: `${c.importance * 100}%` }} />
          </div>
          <div className="text-[10px] font-mono w-10 text-right text-white/70">{(c.importance * 100).toFixed(0)}%</div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4" data-testid="ai-page">
      <div className="card-flat p-5 space-y-3" data-testid="ai-inputs">
        <div>
          <div className="overline">Model inputs</div>
          <div className="font-heading text-lg mt-1">Freight ML Features</div>
        </div>
        {FIELDS.map(f => (
          <div key={f.k}>
            <label className="overline">{f.label}</label>
            <input type={f.type} value={input[f.k]} min={f.min} max={f.max} step={f.step}
              onChange={e => upd(f.k, e.target.value)} data-testid={`inp-${f.k}`}
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono" />
          </div>
        ))}
        <button onClick={run} disabled={loading} data-testid="run-predict-btn"
          className="w-full bg-[color:var(--accent-blue)] hover:brightness-110 py-3 text-sm uppercase tracking-widest font-mono disabled:opacity-40">
          {loading ? "Predicting…" : "Run Predictions"}
        </button>
        {eta && <div className="text-[10px] font-mono text-white/50 border-t border-white/10 pt-3">Model: {eta.model} · R²={eta.r2}</div>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 min-w-0">
        <div className="card-flat p-5" data-testid="eta-card">
          <div className="overline">ETA Prediction</div>
          <div className="kpi-value mt-2 text-[color:var(--accent-blue)]">{eta?.eta_hours ?? "—"} h</div>
          <div className="text-xs text-white/60 font-mono">RandomForest · trained on real OD data</div>
          {eta && <Contribs list={eta.contributions} />}
        </div>

        <div className="card-flat p-5" data-testid="circuit-card">
          <div className="overline">Circuit Time</div>
          <div className="kpi-value mt-2 text-[color:var(--accent-warn)]">{circuit?.circuit_hours ?? "—"} h</div>
          <div className="text-xs text-white/60 font-mono">Turnaround time · GradientBoosting</div>
          {circuit && <Contribs list={circuit.contributions} />}
        </div>

        <div className="card-flat p-5" data-testid="util-card">
          <div className="overline">Wagon Utilization</div>
          <div className="kpi-value mt-2" style={{ color: util?.band === "optimal" ? "#34C759" : (util?.band === "moderate" ? "#FFD60A" : "#FF3B30") }}>
            {util?.utilization_pct ?? "—"}%
          </div>
          <div className="text-xs text-white/60 font-mono uppercase">{util?.band}</div>
        </div>

        <div className="card-flat p-5" data-testid="cong-card">
          <div className="overline">Congestion Forecast</div>
          <div className="kpi-value mt-2" style={{ color: cong?.level === "critical" ? "#FF3B30" : (cong?.level === "high" ? "#FFD60A" : "#34C759") }}>
            {cong ? `${(cong.congestion_forecast * 100).toFixed(1)}%` : "—"}
          </div>
          <div className="text-xs text-white/60 font-mono uppercase">{cong?.level}</div>
        </div>

        <div className="card-flat p-5 md:col-span-2" data-testid="demand-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="overline">Demand Forecast · 30-day horizon</div>
              <div className="font-heading text-[15px] mt-1">Freight tonnes / day</div>
            </div>
            <div className="text-right">
              <div className="kpi-value text-white">{demand ? (demand.total_tonnes / 1e6).toFixed(2) : "—"}M</div>
              <div className="text-[10px] font-mono text-white/50">total tonnes · peak day {demand?.peak_day}</div>
            </div>
          </div>
          <div className="h-40 mt-3">
            {demand && <Line data={demandChart} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { grid: { color: "rgba(255,255,255,0.05)" } } } }} />}
          </div>
        </div>
      </div>
    </div>
  );
}
