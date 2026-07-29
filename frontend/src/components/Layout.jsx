import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  ChartBar, MapTrifold, Path, Brain, ChartLine, FileText, Gear, Train,
  ArrowsClockwise,
} from "@phosphor-icons/react";
import { API, endpoints } from "@/lib/api";

const NAV = [
  { to: "/", label: "Dashboard", icon: ChartBar, testId: "nav-dashboard" },
  { to: "/map", label: "Live Map", icon: MapTrifold, testId: "nav-map" },
  { to: "/simulation", label: "Simulation", icon: Path, testId: "nav-simulation" },
  { to: "/ai-prediction", label: "AI Prediction", icon: Brain, testId: "nav-ai" },
  { to: "/analytics", label: "Analytics", icon: ChartLine, testId: "nav-analytics" },
  { to: "/reports", label: "Reports", icon: FileText, testId: "nav-reports" },
  { to: "/settings", label: "Settings", icon: Gear, testId: "nav-settings" },
];

export default function Layout({ children }) {
  const location = useLocation();
  const [refreshing, setRefreshing] = React.useState(false);
  const [health, setHealth] = React.useState(null);

  React.useEffect(() => {
    endpoints.stations().catch(() => {});
    fetch(`${API}/`).then(r => r.json()).then(setHealth).catch(() => {});
  }, []);

  const refresh = async () => {
    setRefreshing(true);
    try { await endpoints.refreshTrains(); } catch (e) { /* ignore */ }
    setRefreshing(false);
    window.dispatchEvent(new Event("live-refresh"));
  };

  const active = NAV.find((n) => n.to === location.pathname) || NAV[0];

  return (
    <div className="min-h-screen flex bg-[color:var(--bg-base)] text-white">
      <aside className="w-[240px] shrink-0 border-r border-white/10 bg-[color:var(--bg-surface)] flex flex-col" data-testid="sidebar">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Train size={22} weight="duotone" className="text-[color:var(--accent-blue)]" />
            <div>
              <div className="font-heading text-[15px] font-semibold tracking-tight leading-none">RAILNET</div>
              <div className="overline mt-1">Digital Twin · FY 25-26</div>
            </div>
          </div>
        </div>
        <nav className="py-3 flex-1 scroll-thin overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon, testId }) => (
            <NavLink key={to} to={to} end className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} data-testid={testId}>
              <Icon size={16} weight="bold" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-white/10 text-[11px] text-white/50 font-mono">
          {health ? (
            <>
              <div className="flex justify-between"><span>records</span><span className="text-white/80">{health.records?.toLocaleString?.() ?? "-"}</span></div>
              <div className="flex justify-between"><span>stations</span><span className="text-white/80">{health.stations?.toLocaleString?.() ?? "-"}</span></div>
              <div className="flex justify-between"><span>zones</span><span className="text-white/80">{health.zones ?? "-"}</span></div>
            </>
          ) : "loading…"}
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-white/10 bg-[color:var(--bg-surface)] flex items-center justify-between px-6" data-testid="app-header">
          <div>
            <div className="overline">Sector · {active.label.toUpperCase()}</div>
            <div className="font-heading text-[15px] leading-none mt-1">{active.label}</div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-mono text-white/60">
              <span className="status-dot status-on_time" /> live · updated {new Date().toLocaleTimeString()}
            </div>
            <button
              onClick={refresh}
              disabled={refreshing}
              data-testid="refresh-btn"
              className="text-xs font-mono uppercase tracking-widest px-3 py-2 border border-white/15 hover:border-white/40 hover:bg-white/5 flex items-center gap-2 disabled:opacity-40"
            >
              <ArrowsClockwise size={14} className={refreshing ? "animate-spin" : ""} /> Refresh
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-auto scroll-thin">{children}</div>
      </main>
    </div>
  );
}
