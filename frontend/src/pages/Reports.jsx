import React from "react";
import { endpoints } from "@/lib/api";
import { toast } from "sonner";
import { Trash, FloppyDisk, DownloadSimple } from "@phosphor-icons/react";

export default function Reports() {
  const [reports, setReports] = React.useState([]);
  const [title, setTitle] = React.useState("");
  const [kind, setKind] = React.useState("kpi-snapshot");
  const [kpis, setKpis] = React.useState(null);

  const load = React.useCallback(async () => {
    const [r, k] = await Promise.all([endpoints.reports(), endpoints.kpis()]);
    setReports(r.data.reports);
    setKpis(k.data);
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!title) { toast.error("Please provide a title"); return; }
    const payload = kind === "kpi-snapshot" ? kpis : { note: `Custom ${kind} report` };
    await endpoints.createReport({ title, kind, payload });
    toast.success("Report saved");
    setTitle("");
    load();
  };

  const del = async (id) => {
    await endpoints.deleteReport(id);
    toast.success("Deleted");
    load();
  };

  const downloadJson = (r) => {
    const blob = new Blob([JSON.stringify(r, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${r.title.replace(/\s+/g, "_")}.json`;
    a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4" data-testid="reports-page">
      <div className="card-flat p-5 space-y-4">
        <div>
          <div className="overline">Create Report</div>
          <div className="font-heading text-lg mt-1">Snapshot current operations</div>
        </div>
        <div>
          <label className="overline">Title</label>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Weekly Freight Ops"
            data-testid="report-title-input"
            className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm" />
        </div>
        <div>
          <label className="overline">Type</label>
          <select value={kind} onChange={e => setKind(e.target.value)} data-testid="report-kind"
            className="w-full bg-black/40 border border-white/10 px-3 py-2 mt-1 text-sm font-mono">
            <option value="kpi-snapshot">KPI Snapshot</option>
            <option value="incident">Incident</option>
            <option value="performance">Performance Review</option>
            <option value="planning">Planning Note</option>
          </select>
        </div>
        <button onClick={create} data-testid="save-report-btn"
          className="w-full bg-[color:var(--accent-blue)] hover:brightness-110 py-3 text-sm uppercase tracking-widest font-mono flex items-center justify-center gap-2">
          <FloppyDisk size={14} /> Save Report
        </button>
      </div>

      <div className="card-flat p-5" data-testid="report-list">
        <div className="flex justify-between items-center mb-3">
          <div>
            <div className="overline">Saved Reports · {reports.length}</div>
            <div className="font-heading text-[15px] mt-1">History (most recent first)</div>
          </div>
        </div>
        {reports.length === 0 ? (
          <div className="text-white/50 text-sm font-mono py-8 text-center border border-dashed border-white/10">
            No reports yet. Create one from the left panel.
          </div>
        ) : (
          <div className="divide-y divide-white/10">
            {reports.map(r => (
              <div key={r.id} className="py-3 flex items-center gap-3" data-testid={`report-row-${r.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="text-sm">{r.title}</div>
                  <div className="text-[10px] font-mono text-white/50 uppercase tracking-widest">{r.kind} · {new Date(r.created_at).toLocaleString()}</div>
                </div>
                <button onClick={() => downloadJson(r)} className="p-2 border border-white/10 hover:border-white/40" title="Download">
                  <DownloadSimple size={14} />
                </button>
                <button onClick={() => del(r.id)} className="p-2 border border-white/10 hover:border-[color:var(--accent-crit)] text-white/70 hover:text-[color:var(--accent-crit)]" title="Delete">
                  <Trash size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
