import React from "react";
import { endpoints } from "@/lib/api";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Tooltip, Legend, Title, Filler,
} from "chart.js";
import { Truck, Path, Package, ClockCounterClockwise } from "@phosphor-icons/react";

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend, Title, Filler);
ChartJS.defaults.color = "rgba(255,255,255,0.65)";
ChartJS.defaults.font.family = "IBM Plex Sans";
ChartJS.defaults.borderColor = "rgba(255,255,255,0.06)";

const KPI = ({ label, value, hint, icon: Icon, accent, testId }) => (
  <div className="card-flat p-5 flex flex-col justify-between h-full" data-testid={testId}>
    <div className="flex items-center justify-between">
      <div className="overline">{label}</div>
      {Icon ? <Icon size={16} weight="bold" style={{ color: accent }} /> : null}
    </div>
    <div className="mt-3">
      <div className="kpi-value" style={{ color: accent || "#fff" }}>{value}</div>
      {hint ? <div className="text-xs text-white/50 mt-1 font-mono">{hint}</div> : null}
    </div>
  </div>
);

const ChartCard = ({ testId, overline, title, meta, height = 300, chartHeight = 220, children }) => (
  <div className="card-flat p-5" style={{ height }} data-testid={testId}>
    <div className="flex items-center justify-between mb-3">
      <div>
        <div className="overline">{overline}</div>
        <div className="font-heading text-[15px] mt-1">{title}</div>
      </div>
      {meta ? <div className="text-xs text-white/50 font-mono">{meta}</div> : null}
    </div>
    <div style={{ height: chartHeight }}>{children}</div>
  </div>
);

const SummaryRow = ({ label, value }) => (
  <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
    <div className="text-[11px] uppercase tracking-widest text-white/50 font-mono">{label}</div>
    <div className="text-[13px] font-mono text-white/90 text-right">{value}</div>
  </div>
);

export default function Dashboard() {
  const [kpis, setKpis] = React.useState(null);
  const [outgoing, setOutgoing] = React.useState([]);
  const [incoming, setIncoming] = React.useState([]);
  const [loadZone, setLoadZone] = React.useState([]);
  const [destZone, setDestZone] = React.useState([]);
  const [mix, setMix] = React.useState([]);
  const [dispatchTrend, setDispatchTrend] = React.useState([]);
  const [arrivalTrend, setArrivalTrend] = React.useState([]);
  const [topLoading, setTopLoading] = React.useState([]);
  const [topDest, setTopDest] = React.useState([]);
  const [routes, setRoutes] = React.useState([]);

  const load = React.useCallback(async () => {
    const [k, out, inc, lz, dz, m, dt, at, tl, td, r] = await Promise.all([
      endpoints.kpis(),
      endpoints.outgoingStations(10),
      endpoints.incomingStations(10),
      endpoints.loadingZoneDispatch(),
      endpoints.destinationZoneArrival(),
      endpoints.commodityMix(),
      endpoints.dailyDispatchTrend(30),
      endpoints.dailyArrivalTrend(30),
      endpoints.topLoadingStations(10),
      endpoints.topDestinationStations(10),
      endpoints.routeAnalytics(),
    ]);
    setKpis(k.data);
    setOutgoing(out.data.stations);
    setIncoming(inc.data.stations);
    setLoadZone(lz.data.zones);
    setDestZone(dz.data.zones);
    setMix(m.data.mix);
    setDispatchTrend(dt.data.trend);
    setArrivalTrend(at.data.trend);
    setTopLoading(tl.data.stations);
    setTopDest(td.data.stations);
    setRoutes(r.data.routes);
  }, []);

  React.useEffect(() => {
    load();
    const h = () => load();
    window.addEventListener("live-refresh", h);
    return () => window.removeEventListener("live-refresh", h);
  }, [load]);

  const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 10 } } },
      y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { font: { size: 10 } } },
    },
  };

  const horizontalOpts = {
    ...chartOpts,
    indexAxis: "y",
    scales: {
      x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { font: { size: 10 } } },
      y: { grid: { display: false }, ticks: { font: { size: 10 } } },
    },
  };

  const outgoingChart = {
    labels: outgoing.map(s => s.station),
    datasets: [{ label: "Rakes Dispatched", data: outgoing.map(s => s.rakes), backgroundColor: "rgba(0,122,255,0.7)", borderRadius: 0 }],
  };
  const incomingChart = {
    labels: incoming.map(s => s.station),
    datasets: [{ label: "Rakes Received", data: incoming.map(s => s.rakes), backgroundColor: "rgba(52,199,89,0.7)", borderRadius: 0 }],
  };
  const loadZoneChart = {
    labels: loadZone.map(z => z.zone),
    datasets: [{ label: "Rakes", data: loadZone.map(z => z.rakes), backgroundColor: loadZone.map(z => z.color), borderRadius: 0 }],
  };
  const destZoneChart = {
    labels: destZone.map(z => z.zone),
    datasets: [{ label: "Rakes", data: destZone.map(z => z.rakes), backgroundColor: destZone.map(z => z.color), borderRadius: 0 }],
  };
  const mixChart = {
    labels: mix.slice(0, 8).map(m => m.commodity),
    datasets: [{
      data: mix.slice(0, 8).map(m => m.tonnes),
      backgroundColor: ["#007AFF", "#34C759", "#FFD60A", "#FF9500", "#FF3B30", "#AF52DE", "#5AC8FA", "#FF2D55"],
      borderColor: "#0a0a0b", borderWidth: 2,
    }],
  };
  const dispatchTrendChart = {
    labels: dispatchTrend.map(d => d.date),
    datasets: [{
      label: "Rakes Dispatched", data: dispatchTrend.map(d => d.rakes),
      borderColor: "#007AFF", backgroundColor: "rgba(0,122,255,0.12)",
      fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2,
    }],
  };
  const arrivalTrendChart = {
    labels: arrivalTrend.map(d => d.date),
    datasets: [{
      label: "Rakes Received", data: arrivalTrend.map(d => d.rakes),
      borderColor: "#34C759", backgroundColor: "rgba(52,199,89,0.12)",
      fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2,
    }],
  };
  const topLoadingChart = {
    labels: topLoading.map(s => s.station),
    datasets: [{ label: "Load (t)", data: topLoading.map(s => s.load), backgroundColor: "rgba(255,149,0,0.75)", borderRadius: 0 }],
  };
  const topDestChart = {
    labels: topDest.map(s => s.station),
    datasets: [{ label: "Load (t)", data: topDest.map(s => s.load), backgroundColor: "rgba(175,82,222,0.75)", borderRadius: 0 }],
  };

  if (!kpis) return <div className="p-8 text-white/60" data-testid="dashboard-loading">Loading freight analytics…</div>;

  const topCommodity = mix[0];
  const highestLoadZone = loadZone[0];
  const highestDestZone = destZone[0];
  const topCorridor = routes[0];

  return (
    <div className="p-6 tactical-grid" data-testid="dashboard-page">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPI label="Live Rakes" value={kpis.total_freight_trains.toLocaleString()} icon={Truck} accent="#007AFF" testId="kpi-live" />
        <KPI label="Total Rakes FY" value={kpis.total_rakes_fy.toLocaleString()} icon={Path} accent="#5AC8FA" testId="kpi-total" />
        <KPI label="Avg Transit" value={`${kpis.avg_transit_hrs} h`} hint={`avg ${kpis.avg_km} km`} icon={ClockCounterClockwise} accent="#FF9500" testId="kpi-transit" />
        <KPI label="Total FY Load" value={`${(kpis.total_load_tonnes_fy / 1e6).toFixed(1)}M t`} hint={`${kpis.unique_commodities} commodities`} icon={Package} accent="#AF52DE" testId="kpi-load" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <ChartCard testId="chart-outgoing" overline="Loading Stations" title="Outgoing Rakes by Loading Station" meta={`top ${outgoing.length}`}>
          <Bar data={outgoingChart} options={chartOpts} />
        </ChartCard>
        <ChartCard testId="chart-incoming" overline="Destination Stations" title="Incoming Rakes by Destination Station" meta={`top ${incoming.length}`}>
          <Bar data={incomingChart} options={chartOpts} />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <ChartCard testId="chart-load-zone" overline="Loading Zone" title="Loading Zone Wise Dispatch" meta={`${loadZone.length} zones`}>
          <Bar data={loadZoneChart} options={chartOpts} />
        </ChartCard>
        <ChartCard testId="chart-dest-zone" overline="Destination Zone" title="Destination Zone Wise Arrival" meta={`${destZone.length} zones`}>
          <Bar data={destZoneChart} options={chartOpts} />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <ChartCard testId="chart-commodity" overline="Commodity Mix" title="Commodity Distribution" meta="tonnage share">
          <Doughnut data={mixChart} options={{ ...chartOpts, plugins: { legend: { display: true, position: "right", labels: { boxWidth: 10, font: { size: 10 } } } }, cutout: "60%" }} />
        </ChartCard>

        <ChartCard testId="chart-dispatch-trend" overline="Daily Trend" title="Daily Dispatch Trend" meta={`${dispatchTrend.length} days`}>
          <Line data={dispatchTrendChart} options={chartOpts} />
        </ChartCard>

        <div className="card-flat p-5 h-[300px] flex flex-col" data-testid="operational-summary-panel">
          <div className="overline">Operational Summary</div>
          <div className="font-heading text-[15px] mt-1 mb-1">Freight snapshot</div>
          <div className="mt-1 flex-1 overflow-y-auto scroll-thin">
            <SummaryRow label="Total Live Rakes" value={kpis.total_freight_trains.toLocaleString()} />
            <SummaryRow label="Highest Loading Zone" value={highestLoadZone ? `${highestLoadZone.name} (${highestLoadZone.rakes.toLocaleString()})` : "—"} />
            <SummaryRow label="Highest Destination Zone" value={highestDestZone ? `${highestDestZone.name} (${highestDestZone.rakes.toLocaleString()})` : "—"} />
            <SummaryRow label="Top Commodity" value={topCommodity ? topCommodity.commodity : "—"} />
            <SummaryRow label="Total Freight Handled" value={`${(kpis.total_load_tonnes_fy / 1e6).toFixed(1)}M t`} />
            <SummaryRow label="Average Transit Time" value={`${kpis.avg_transit_hrs} h`} />
            <SummaryRow label="Highest Traffic Corridor" value={topCorridor ? topCorridor.route : "—"} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        <ChartCard testId="chart-arrival-trend" overline="Daily Trend" title="Daily Arrival Trend" meta={`${arrivalTrend.length} days`}>
          <Line data={arrivalTrendChart} options={chartOpts} />
        </ChartCard>
        <ChartCard testId="chart-top-loading" overline="Top Stations" title="Top Loading Stations" meta="by tonnage" chartHeight={220}>
          <Bar data={topLoadingChart} options={horizontalOpts} />
        </ChartCard>
        <ChartCard testId="chart-top-destination" overline="Top Stations" title="Top Destination Stations" meta="by tonnage" chartHeight={220}>
          <Bar data={topDestChart} options={horizontalOpts} />
        </ChartCard>
      </div>
    </div>
  );
}
