import React from "react";
import { endpoints } from "@/lib/api";
import { toast } from "sonner";

export default function Settings() {
  const [s, setS] = React.useState(null);

  const load = React.useCallback(async () => {
    const r = await endpoints.settings();
    setS(r.data);
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const save = async () => {
    await endpoints.saveSettings(s);
    toast.success("Settings saved");
  };

  if (!s) return <div className="p-8 text-white/50" data-testid="settings-loading">Loading…</div>;

  const upd = (k, v) => setS(prev => ({ ...prev, [k]: v }));

  return (
    <div className="p-6" data-testid="settings-page">
      <div className="card-flat p-6 max-w-2xl">
        <div className="overline">Platform</div>
        <div className="font-heading text-lg mt-1 mb-6">System Preferences</div>

        <div className="space-y-5">
          <div>
            <label className="overline">Theme</label>
            <div className="flex gap-2 mt-1">
              {["dark", "system"].map(t => (
                <button key={t} onClick={() => upd("theme", t)} data-testid={`theme-${t}`}
                  className={`px-4 py-2 text-sm font-mono border ${s.theme === t ? "border-[color:var(--accent-blue)] bg-[color:var(--accent-blue)]/10" : "border-white/10 text-white/60"}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="overline">Map Provider</label>
            <select value={s.map_provider} onChange={e => upd("map_provider", e.target.value)} data-testid="map-provider"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono">
              <option value="osm">OpenStreetMap (default)</option>
              <option value="carto">CartoDB Dark</option>
            </select>
          </div>

          <div>
            <label className="overline">Refresh Interval (seconds)</label>
            <input type="number" value={s.refresh_interval_sec} min={5} max={300}
              onChange={e => upd("refresh_interval_sec", parseInt(e.target.value || 0))}
              data-testid="refresh-interval"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono" />
          </div>

          <div>
            <label className="overline">Default Zone</label>
            <input value={s.default_zone} onChange={e => upd("default_zone", e.target.value.toUpperCase())}
              data-testid="default-zone"
              className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono" />
          </div>

          <div className="flex items-center gap-3">
            <input id="alerts" type="checkbox" checked={s.alerts_enabled}
              onChange={e => upd("alerts_enabled", e.target.checked)} data-testid="alerts-toggle"
              className="w-4 h-4 accent-[color:var(--accent-blue)]" />
            <label htmlFor="alerts" className="text-sm">Enable congestion & conflict alerts</label>
          </div>

          <button onClick={save} data-testid="save-settings-btn"
            className="bg-[color:var(--accent-blue)] hover:brightness-110 px-6 py-2.5 text-sm uppercase tracking-widest font-mono">
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
