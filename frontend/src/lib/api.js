import axios from "axios";

const configuredApiUrl = import.meta.env.VITE_API_URL?.replace(/\/+$/, "");
export const API = configuredApiUrl || "/api";

export const api = axios.create({
  baseURL: API,
  timeout: 30000,
});

export const endpoints = {
  zones: () => api.get("/zones"),
  stations: (zone) => api.get("/stations", { params: zone ? { zone } : {} }),
  routes: () => api.get("/routes"),
  trains: (params = {}) => api.get("/trains", { params }),
  refreshTrains: () => api.post("/trains/refresh"),
  congestion: () => api.get("/congestion"),
  kpis: () => api.get("/dashboard/kpis"),
  zoneStats: () => api.get("/dashboard/zone-stats"),
  commodityMix: () => api.get("/dashboard/commodity-mix"),
  routeAnalytics: () => api.get("/dashboard/route-analytics"),
  outgoingStations: (top = 12) => api.get("/dashboard/outgoing-stations", { params: { top } }),
  incomingStations: (top = 12) => api.get("/dashboard/incoming-stations", { params: { top } }),
  loadingZoneDispatch: () => api.get("/dashboard/loading-zone-dispatch"),
  destinationZoneArrival: () => api.get("/dashboard/destination-zone-arrival"),
  dailyDispatchTrend: (days = 30) => api.get("/dashboard/daily-dispatch-trend", { params: { days } }),
  dailyArrivalTrend: (days = 30) => api.get("/dashboard/daily-arrival-trend", { params: { days } }),
  topLoadingStations: (top = 10) => api.get("/dashboard/top-loading-stations", { params: { top } }),
  topDestinationStations: (top = 10) => api.get("/dashboard/top-destination-stations", { params: { top } }),
  heatmap: () => api.get("/analytics/heatmap"),
  assetUtil: () => api.get("/analytics/asset-utilization"),
  simulate: (data) => api.post("/simulation/plan", data),
  conflicts: () => api.get("/simulation/conflicts"),
  predictEta: (d) => api.post("/predict/eta", d),
  predictCircuit: (d) => api.post("/predict/circuit-time", d),
  predictUtil: (d) => api.post("/predict/utilization", d),
  predictCong: (d) => api.post("/predict/congestion", d),
  predictDemand: (d) => api.post("/predict/demand", d),
  reports: () => api.get("/reports"),
  createReport: (d) => api.post("/reports", d),
  deleteReport: (id) => api.delete(`/reports/${id}`),
  settings: () => api.get("/settings"),
  saveSettings: (d) => api.post("/settings", d),
  sampleOdPairs: () => api.get("/meta/sample-od-pairs"),
};
