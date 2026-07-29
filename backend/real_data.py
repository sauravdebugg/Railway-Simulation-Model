"""
Real Indian Railway freight OD dataset loader (FY 2025-26).
Source: OD_FY2526_VIA_LIST.xlsx → cleaned to od_clean.parquet
Provides:
  STATIONS_REAL, ZONES_REAL, COMMODITIES_REAL, LOADTYPES_REAL
  build_live_trains(n) → list of live train dicts (sampled from real OD pairs)
  build_congestion() → aggregated section congestion from real rake volumes
  aggregate_kpis(), aggregate_zone_stats(), aggregate_commodity_mix()
  aggregate_route_analytics(), heatmap_points()
  full training DataFrame for ML models.
"""
from __future__ import annotations
from pathlib import Path
import random
import pandas as pd
import numpy as np

DATA_PATH = Path(__file__).parent / "data" / "od_clean.parquet"

# --- Zone metadata (colors + full names). Any zone present in data but missing
# here still shows using its code.
ZONE_META = {
    "NR": {"name": "Northern Railway", "color": "#007AFF"},
    "SR": {"name": "Southern Railway", "color": "#34C759"},
    "CR": {"name": "Central Railway", "color": "#FFD60A"},
    "WR": {"name": "Western Railway", "color": "#FF9500"},
    "ER": {"name": "Eastern Railway", "color": "#FF3B30"},
    "NER": {"name": "North Eastern Railway", "color": "#AF52DE"},
    "NE": {"name": "North Eastern Railway", "color": "#AF52DE"},
    "SE": {"name": "South Eastern Railway", "color": "#5AC8FA"},
    "SCR": {"name": "South Central Railway", "color": "#FF2D55"},
    "SC": {"name": "South Central Railway", "color": "#FF2D55"},
    "NCR": {"name": "North Central Railway", "color": "#64D2FF"},
    "NC": {"name": "North Central Railway", "color": "#64D2FF"},
    "ECR": {"name": "East Central Railway", "color": "#BF5AF2"},
    "EC": {"name": "East Central Railway", "color": "#BF5AF2"},
    "ECO": {"name": "East Coast Railway", "color": "#00C7BE"},
    "ECOR": {"name": "East Coast Railway", "color": "#00C7BE"},
    "SEC": {"name": "South East Central Railway", "color": "#FF9F0A"},
    "SCOR": {"name": "South Coast Railway", "color": "#5E5CE6"},
    "SW": {"name": "South Western Railway", "color": "#30D158"},
    "SWR": {"name": "South Western Railway", "color": "#30D158"},
    "NF": {"name": "Northeast Frontier Railway", "color": "#FF375F"},
    "NFR": {"name": "Northeast Frontier Railway", "color": "#FF375F"},
    "NW": {"name": "North Western Railway", "color": "#FFD60A"},
    "NWR": {"name": "North Western Railway", "color": "#FFD60A"},
    "WC": {"name": "West Central Railway", "color": "#0A84FF"},
    "WCR": {"name": "West Central Railway", "color": "#0A84FF"},
    "KR": {"name": "Konkan Railway", "color": "#64D2FF"},
    "DFCR": {"name": "Dedicated Freight Corridor", "color": "#FF9500"},
}

COMMODITY_LABELS = {
    "COAL": "Coal", "CEMT": "Cement", "CLKR": "Clinker", "RMSP": "Raw Material (Steel Plant)",
    "IOST": "Iron Ore (Steel Plants)", "ORES": "Iron Ore (Export)", "IMCL": "Imported Coal",
    "ASH": "Fly Ash", "FERT": "Fertiliser", "CONT": "Containers", "FG": "Finished Goods",
    "MIXD": "Mixed Cargo", "POL": "Petroleum, Oil, Lubricants", "AUTO": "Automobiles",
    "BALT": "Ballast", "IS": "Iron & Steel", "EXOR": "Iron Ore (Export)", "SAND": "Sand",
    "METL": "Metals", "SALT": "Salt", "SLPR": "Sleepers", "RMC": "Ready Mix Concrete",
    "STON": "Stone", "IMFT": "Imported Fertiliser", "DOC": "De-Oiled Cakes",
    "EOIL": "Edible Oil", "WOOD": "Wood", "OTHR": "Other", "SUG": "Sugar",
    "RORO": "Roll-On Roll-Off", "OIL": "Oil", "MISC": "Miscellaneous", "JUTM": "Jute",
    "PERI": "Perishables", "TAR": "Tar", "MILY": "Military", "GAS": "Gas",
    "CHAR": "Charcoal", "FODR": "Fodder", "IMOR": "Imported Ore", "SOAP": "Soap",
    "HUSK": "Husk", "PRCL": "Parcel", "COTN": "Cotton", "SEED": "Seed",
}


def _load() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_PATH}")
    df = pd.read_parquet(DATA_PATH)
    # coerce
    df["fromlttd"] = pd.to_numeric(df["fromlttd"], errors="coerce")
    df["fromlgtd"] = pd.to_numeric(df["fromlgtd"], errors="coerce")
    df["tolttd"] = pd.to_numeric(df["tolttd"], errors="coerce")
    df["tolgtd"] = pd.to_numeric(df["tolgtd"], errors="coerce")
    df = df.dropna(subset=["fromlttd", "fromlgtd", "tolttd", "tolgtd"])
    # Bounds within India
    df = df[df["fromlttd"].between(6, 38) & df["fromlgtd"].between(68, 98)]
    df = df[df["tolttd"].between(6, 38) & df["tolgtd"].between(68, 98)]
    return df.reset_index(drop=True)


print("[real_data] loading OD parquet...", flush=True)
_DF = _load()
print(f"[real_data] loaded {len(_DF):,} freight OD records", flush=True)


# --- Stations (union of load + destination) ---
def _stations() -> list[dict]:
    src = _DF[["ldngsttn", "ssfullname", "fromlttd", "fromlgtd", "zone", "dvsn", "state1"]].rename(
        columns={"ldngsttn": "code", "ssfullname": "name", "fromlttd": "lat", "fromlgtd": "lng",
                 "dvsn": "division", "state1": "state"}
    )
    dst = _DF[["destination", "dname", "tolttd", "tolgtd", "zoneto", "dvsnto", "state2"]].rename(
        columns={"destination": "code", "dname": "name", "tolttd": "lat", "tolgtd": "lng",
                 "zoneto": "zone", "dvsnto": "division", "state2": "state"}
    )
    all_s = pd.concat([src, dst], ignore_index=True)
    # aggregate by code — take first non-null
    grp = all_s.groupby("code").agg({
        "name": "first", "lat": "mean", "lng": "mean",
        "zone": "first", "division": "first", "state": "first",
    }).reset_index()
    grp["lat"] = grp["lat"].round(4)
    grp["lng"] = grp["lng"].round(4)
    return grp.to_dict(orient="records")


STATIONS_REAL = _stations()
STATION_BY_CODE = {s["code"]: s for s in STATIONS_REAL}
print(f"[real_data] {len(STATIONS_REAL):,} unique stations extracted", flush=True)

ZONES_REAL = sorted(set(list(_DF["zone"].dropna().unique()) + list(_DF["zoneto"].dropna().unique())))
COMMODITIES_REAL = sorted(_DF["grupcmdt"].dropna().unique().tolist())
LOADTYPES_REAL = sorted(_DF["loadtype"].dropna().unique().tolist())


def zones_list():
    out = []
    for z in ZONES_REAL:
        meta = ZONE_META.get(z, {"name": z, "color": "#8E8E93"})
        # count stations & trains for zone
        cnt_stn = sum(1 for s in STATIONS_REAL if s.get("zone") == z)
        cnt_rakes = int((_DF["zone"] == z).sum())
        out.append({"code": z, "name": meta["name"], "color": meta["color"],
                    "stations": cnt_stn, "rakes_dispatched": cnt_rakes})
    return sorted(out, key=lambda x: -x["rakes_dispatched"])


def _parse_route(via: str) -> list[str]:
    if not isinstance(via, str):
        return []
    return [c.strip() for c in via.split(",") if c.strip()]


# --- Live trains (sampled from most recent OD records) ---
def build_live_trains(n: int = 48) -> list[dict]:
    """Sample real recent rakes and simulate their current position along the via-list."""
    # Use most recent rakes for realism, wide enough to cover the requested fleet size
    recent = _DF.sort_values("rdate", ascending=False).head(max(4000, n * 2))
    sample = recent.sample(n=min(n, len(recent)), random_state=random.randint(0, 999999))
    trains = []
    for i, r in enumerate(sample.itertuples(index=False)):
        via = _parse_route(getattr(r, "travl_route_part", ""))
        # if via missing, fall back to origin→destination two-point path
        if len(via) < 2:
            via = [r.ldngsttn, r.destination]
        # progress along via list
        progress = round(random.uniform(0.05, 0.95), 3)
        seg_count = len(via) - 1
        idx_f = progress * seg_count
        idx = min(seg_count - 1, int(idx_f))
        frac = idx_f - idx
        a = STATION_BY_CODE.get(via[idx])
        b = STATION_BY_CODE.get(via[idx + 1] if idx + 1 < len(via) else via[-1])
        # Fallback to straight-line origin/destination
        a_lat, a_lng = r.fromlttd, r.fromlgtd
        b_lat, b_lng = r.tolttd, r.tolgtd
        if a: a_lat, a_lng = a["lat"], a["lng"]
        if b: b_lat, b_lng = b["lat"], b["lng"]
        cur_lat = a_lat + (b_lat - a_lat) * frac
        cur_lng = a_lng + (b_lng - a_lng) * frac
        # Speed estimate
        avg_speed = float(r.km) / max(float(r.avgtime_hrs), 0.5)
        avg_speed = max(15.0, min(85.0, avg_speed))
        # Simulated live delay
        delay_min = int(random.choice([0, 0, 0, 15, 20, 30, 45, 60, 90, 120]))
        status = "on_time" if delay_min <= 15 else ("delayed" if delay_min < 90 else "critical")
        cmdt_code = str(r.grupcmdt)
        trains.append({
            "id": str(r.rakeid),
            "number": str(r.rakeid)[-6:],
            "name": f"{r.ldngsttn}→{r.destination} · {COMMODITY_LABELS.get(cmdt_code, cmdt_code)}",
            "commodity_code": cmdt_code,
            "commodity": COMMODITY_LABELS.get(cmdt_code, cmdt_code),
            "loadtype": str(r.loadtype),
            "origin": str(r.ldngsttn),
            "origin_name": str(r.ssfullname)[:40],
            "destination": str(r.destination),
            "destination_name": str(r.dname)[:40],
            "current_station": via[idx],
            "next_station": via[min(idx + 1, len(via) - 1)],
            "current_lat": round(cur_lat, 4),
            "current_lng": round(cur_lng, 4),
            "origin_lat": round(float(r.fromlttd), 4),
            "origin_lng": round(float(r.fromlgtd), 4),
            "dest_lat": round(float(r.tolttd), 4),
            "dest_lng": round(float(r.tolgtd), 4),
            "wagons": int(r.avgunits) if r.avgunits and not pd.isna(r.avgunits) else 58,
            "load_tonnes": round(float(r.total_wght), 1),
            "distance_total_km": round(float(r.km), 1),
            "distance_covered_km": round(float(r.km) * progress, 1),
            "avgtime_hrs": round(float(r.avgtime_hrs), 2),
            "speed_kmph": round(avg_speed, 1),
            "progress": progress,
            "delay_min": delay_min,
            "status": status,
            "zone": str(r.zone),
            "zone_to": str(r.zoneto),
            "division": str(r.dvsn),
            "consignor": str(r.cnsr),
            "consignee": str(r.cnsg) if r.cnsg and not pd.isna(r.cnsg) else "",
            "state_from": str(r.state1),
            "state_to": str(r.state2),
            "via": via,
            "eta_minutes": max(30, int(float(r.km) * (1 - progress) / max(avg_speed, 20) * 60)) + delay_min,
            "circuit_time_hrs": round(float(r.avgtime_hrs) * 2, 1),
        })
    return trains


# --- Aggregated dashboard KPIs (from full dataset) ---
def aggregate_kpis(live_trains: list[dict]) -> dict:
    total_live = len(live_trains)
    on_time = sum(1 for t in live_trains if t["status"] == "on_time")
    delayed = sum(1 for t in live_trains if t["status"] == "delayed")
    critical = sum(1 for t in live_trains if t["status"] == "critical")
    return {
        "total_rakes_fy": int(len(_DF)),
        "total_freight_trains": total_live,
        "on_time": on_time,
        "delayed": delayed,
        "critical": critical,
        "punctuality_pct": round(on_time / max(total_live, 1) * 100, 1),
        "total_load_tonnes_fy": round(float(_DF["total_wght"].sum()), 1),
        "avg_load_tonnes": round(float(_DF["total_wght"].mean()), 1),
        "avg_km": round(float(_DF["km"].mean()), 1),
        "avg_transit_hrs": round(float(_DF["avgtime_hrs"].mean()), 2),
        "active_zones": len(ZONES_REAL),
        "unique_stations": len(STATIONS_REAL),
        "unique_commodities": len(COMMODITIES_REAL),
        "unique_rake_types": len(LOADTYPES_REAL),
    }


def aggregate_zone_stats() -> list[dict]:
    grp = _DF.groupby("zone").agg(
        rakes=("rakeid", "count"),
        load=("total_wght", "sum"),
        avg_km=("km", "mean"),
        avg_time=("avgtime_hrs", "mean"),
    ).reset_index()
    out = []
    for r in grp.itertuples(index=False):
        meta = ZONE_META.get(r.zone, {"name": r.zone, "color": "#8E8E93"})
        out.append({
            "zone": r.zone,
            "name": meta["name"],
            "color": meta["color"],
            "rakes": int(r.rakes),
            "load": round(float(r.load), 1),
            "avg_km": round(float(r.avg_km), 1),
            "avg_time": round(float(r.avg_time), 2),
        })
    return sorted(out, key=lambda x: -x["rakes"])


def aggregate_commodity_mix(top: int = 15) -> list[dict]:
    grp = _DF.groupby("grupcmdt").agg(
        rakes=("rakeid", "count"),
        tonnes=("total_wght", "sum"),
    ).reset_index()
    grp = grp.sort_values("tonnes", ascending=False).head(top)
    out = []
    for r in grp.itertuples(index=False):
        code = str(r.grupcmdt)
        out.append({
            "commodity_code": code,
            "commodity": COMMODITY_LABELS.get(code, code),
            "rakes": int(r.rakes),
            "tonnes": round(float(r.tonnes), 1),
        })
    return out


def aggregate_route_analytics(top: int = 20) -> list[dict]:
    grp = _DF.groupby(["ldngsttn", "destination"]).agg(
        rakes=("rakeid", "count"),
        load=("total_wght", "sum"),
        avg_km=("km", "mean"),
        avg_time=("avgtime_hrs", "mean"),
    ).reset_index()
    grp = grp.sort_values("load", ascending=False).head(top)
    out = []
    for r in grp.itertuples(index=False):
        out.append({
            "origin": r.ldngsttn,
            "destination": r.destination,
            "route": f"{r.ldngsttn} → {r.destination}",
            "rakes": int(r.rakes),
            "load": round(float(r.load), 1),
            "avg_km": round(float(r.avg_km), 1),
            "avg_time": round(float(r.avg_time), 2),
        })
    return out


def aggregate_outgoing_stations(top: int = 12) -> list[dict]:
    """Rakes dispatched per loading station (non-sensitive demo analytic)."""
    grp = _DF.groupby(["ldngsttn", "ssfullname"]).agg(
        rakes=("rakeid", "count"),
        load=("total_wght", "sum"),
    ).reset_index()
    grp = grp.sort_values("rakes", ascending=False).head(top)
    return [
        {
            "station": r.ldngsttn,
            "station_name": str(r.ssfullname)[:40],
            "rakes": int(r.rakes),
            "load": round(float(r.load), 1),
        }
        for r in grp.itertuples(index=False)
    ]


def aggregate_incoming_stations(top: int = 12) -> list[dict]:
    """Rakes received per destination station (non-sensitive demo analytic)."""
    grp = _DF.groupby(["destination", "dname"]).agg(
        rakes=("rakeid", "count"),
        load=("total_wght", "sum"),
    ).reset_index()
    grp = grp.sort_values("rakes", ascending=False).head(top)
    return [
        {
            "station": r.destination,
            "station_name": str(r.dname)[:40],
            "rakes": int(r.rakes),
            "load": round(float(r.load), 1),
        }
        for r in grp.itertuples(index=False)
    ]


def aggregate_loading_zone_dispatch() -> list[dict]:
    """Rakes dispatched per loading zone."""
    grp = _DF.groupby("zone").agg(rakes=("rakeid", "count")).reset_index()
    grp = grp.sort_values("rakes", ascending=False)
    out = []
    for r in grp.itertuples(index=False):
        meta = ZONE_META.get(r.zone, {"name": r.zone, "color": "#8E8E93"})
        out.append({"zone": r.zone, "name": meta["name"], "color": meta["color"], "rakes": int(r.rakes)})
    return out


def aggregate_destination_zone_arrival() -> list[dict]:
    """Rakes arriving per destination zone."""
    grp = _DF.groupby("zoneto").agg(rakes=("rakeid", "count")).reset_index()
    grp = grp.sort_values("rakes", ascending=False)
    out = []
    for r in grp.itertuples(index=False):
        meta = ZONE_META.get(r.zoneto, {"name": r.zoneto, "color": "#8E8E93"})
        out.append({"zone": r.zoneto, "name": meta["name"], "color": meta["color"], "rakes": int(r.rakes)})
    return out


def aggregate_daily_dispatch_trend(days: int = 30) -> list[dict]:
    """Daily count of dispatches (by rdate), most recent `days` days with data."""
    grp = _DF.groupby(_DF["rdate"].dt.date).agg(rakes=("rakeid", "count")).reset_index()
    grp = grp.rename(columns={"rdate": "date"}).sort_values("date")
    grp = grp.tail(days)
    return [{"date": str(r.date), "rakes": int(r.rakes)} for r in grp.itertuples(index=False)]


def aggregate_daily_arrival_trend(days: int = 30) -> list[dict]:
    """Daily count of arrivals, derived from dispatch date + avg transit time (no fake columns)."""
    arrival_date = (_DF["rdate"] + pd.to_timedelta(_DF["avgtime_hrs"], unit="h")).dt.date
    tmp = pd.DataFrame({"arrival_date": arrival_date, "rakeid": _DF["rakeid"]})
    grp = tmp.groupby("arrival_date").agg(rakes=("rakeid", "count")).reset_index()
    grp = grp.rename(columns={"arrival_date": "date"}).sort_values("date")
    grp = grp.tail(days)
    return [{"date": str(r.date), "rakes": int(r.rakes)} for r in grp.itertuples(index=False)]


def aggregate_top_loading_stations(top: int = 10) -> list[dict]:
    """Top loading stations ranked by total tonnage dispatched."""
    grp = _DF.groupby(["ldngsttn", "ssfullname"]).agg(
        load=("total_wght", "sum"),
        rakes=("rakeid", "count"),
    ).reset_index()
    grp = grp.sort_values("load", ascending=False).head(top)
    return [
        {
            "station": r.ldngsttn,
            "station_name": str(r.ssfullname)[:40],
            "load": round(float(r.load), 1),
            "rakes": int(r.rakes),
        }
        for r in grp.itertuples(index=False)
    ]


def aggregate_top_destination_stations(top: int = 10) -> list[dict]:
    """Top destination stations ranked by total tonnage received."""
    grp = _DF.groupby(["destination", "dname"]).agg(
        load=("total_wght", "sum"),
        rakes=("rakeid", "count"),
    ).reset_index()
    grp = grp.sort_values("load", ascending=False).head(top)
    return [
        {
            "station": r.destination,
            "station_name": str(r.dname)[:40],
            "load": round(float(r.load), 1),
            "rakes": int(r.rakes),
        }
        for r in grp.itertuples(index=False)
    ]


def aggregate_asset_utilization() -> list[dict]:
    grp = _DF.groupby("loadtype").agg(
        rakes=("rakeid", "count"),
        avg_wagons=("avgunits", "mean"),
        avg_load=("total_wght", "mean"),
    ).reset_index()
    grp = grp.sort_values("rakes", ascending=False).head(15)
    out = []
    for r in grp.itertuples(index=False):
        out.append({
            "rake_type": r.loadtype,
            "count": int(r.rakes),
            "avg_wagons": round(float(r.avg_wagons), 1),
            "avg_load": round(float(r.avg_load), 1),
        })
    return out


def build_congestion_from_data(top: int = 60) -> list[dict]:
    """Estimate section-level congestion from busiest OD pairs (rake count)."""
    grp = _DF.groupby(["ldngsttn", "destination"]).agg(
        rakes=("rakeid", "count"),
        avg_time=("avgtime_hrs", "mean"),
        avg_km=("km", "mean"),
    ).reset_index()
    grp = grp.sort_values("rakes", ascending=False).head(top)
    max_r = grp["rakes"].max() or 1
    out = []
    for r in grp.itertuples(index=False):
        a = STATION_BY_CODE.get(r.ldngsttn)
        b = STATION_BY_CODE.get(r.destination)
        if not a or not b:
            continue
        cong = float(r.rakes) / float(max_r)
        avg_speed = float(r.avg_km) / max(float(r.avg_time), 0.5)
        avg_speed = max(15.0, min(85.0, avg_speed))
        out.append({
            "section_id": f"{r.ldngsttn}-{r.destination}",
            "from_station": r.ldngsttn,
            "to_station": r.destination,
            "from_lat": a["lat"], "from_lng": a["lng"],
            "to_lat": b["lat"], "to_lng": b["lng"],
            "congestion": round(cong, 3),
            "rakes_year": int(r.rakes),
            "avg_speed_kmph": round(avg_speed, 1),
        })
    return out


def heatmap_points(top: int = 200) -> list[dict]:
    """Load intensity per loading station."""
    grp = _DF.groupby(["ldngsttn", "ssfullname", "fromlttd", "fromlgtd", "zone"]).agg(
        load=("total_wght", "sum"),
        rakes=("rakeid", "count"),
    ).reset_index()
    grp = grp.sort_values("load", ascending=False).head(top)
    max_l = grp["load"].max() or 1
    out = []
    for r in grp.itertuples(index=False):
        out.append({
            "code": r.ldngsttn,
            "name": str(r.ssfullname)[:60],
            "lat": float(r.fromlttd),
            "lng": float(r.fromlgtd),
            "zone": r.zone,
            "rakes": int(r.rakes),
            "load_tonnes": round(float(r.load), 1),
            "intensity": round(float(r.load) / float(max_l), 3),
        })
    return out


def ml_training_frame() -> pd.DataFrame:
    """Return features/labels frame for ML training on real data."""
    df = _DF.copy()
    df = df[(df["km"] > 5) & (df["avgtime_hrs"] > 0.5)]
    df["distance_km"] = df["km"].astype(float)
    df["wagons"] = df["avgunits"].fillna(58).astype(float)
    df["loaded_pct"] = ((df["total_wght"] / (df["wagons"] * 58)) * 100).clip(40, 100)
    df["eta_hrs"] = df["avgtime_hrs"].astype(float)
    # zone-based priority mapping
    priority_map = {"DFCR": 1, "NR": 2, "CR": 2, "WR": 2, "ER": 2, "SR": 2, "SCR": 2, "ECR": 2, "NCR": 2}
    df["priority"] = df["zone"].map(priority_map).fillna(3).astype(int)
    df["is_dfc"] = (df["zone"] == "DFCR").astype(int)
    # weather & congestion synthetic per row (unavailable in dataset)
    rng = np.random.default_rng(7)
    df["weather"] = rng.uniform(0, 1, len(df))
    df["congestion"] = rng.uniform(0.15, 0.9, len(df))
    df["circuit_hrs"] = df["eta_hrs"] * 2 + rng.normal(0, 4, len(df))
    df["util_pct"] = df["loaded_pct"]
    df["cong_next"] = (df["congestion"] + rng.uniform(-0.1, 0.15, len(df))).clip(0, 1)
    return df[["distance_km", "wagons", "loaded_pct", "priority", "congestion", "weather", "is_dfc",
               "eta_hrs", "circuit_hrs", "util_pct", "cong_next"]].sample(n=min(20000, len(df)), random_state=1)


def sample_od_pairs(n: int = 20) -> list[dict]:
    """Sample OD pairs for the simulation planner dropdown."""
    top_pairs = _DF.groupby(["ldngsttn", "destination", "grupcmdt"]).agg(
        rakes=("rakeid", "count"), avg_km=("km", "mean")
    ).reset_index().sort_values("rakes", ascending=False).head(50)
    return [
        {
            "origin": r.ldngsttn,
            "destination": r.destination,
            "commodity": COMMODITY_LABELS.get(r.grupcmdt, r.grupcmdt),
            "commodity_code": r.grupcmdt,
            "rakes": int(r.rakes),
            "avg_km": round(float(r.avg_km), 1),
        }
        for r in top_pairs.head(n).itertuples(index=False)
    ]
