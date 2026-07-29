"""
Freight simulation utilities: path finding over the REAL Indian Railway station
graph (edges built from `travl_route_part`), rake allocation, and conflict detection.
"""
from __future__ import annotations
import heapq
from typing import Dict, List
import pandas as pd

from real_data import _DF, STATION_BY_CODE  # noqa

# --- Build station adjacency graph from via lists ---
GRAPH: Dict[str, Dict[str, dict]] = {}


def _haversine_km(a_lat, a_lng, b_lat, b_lng):
    from math import radians, sin, cos, asin, sqrt
    r = 6371.0
    dlat = radians(b_lat - a_lat)
    dlng = radians(b_lng - a_lng)
    aa = sin(dlat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(dlng / 2) ** 2
    return 2 * r * asin(sqrt(aa))


def _build_graph():
    global GRAPH
    print("[simulation] building station graph from real via-lists...", flush=True)
    route_lists = _DF["travl_route_part"].dropna().drop_duplicates()
    seen_edges = set()
    for via in route_lists:
        parts = [p.strip() for p in str(via).split(",") if p.strip()]
        for i in range(len(parts) - 1):
            a, b = parts[i], parts[i + 1]
            if a == b:
                continue
            key = tuple(sorted([a, b]))
            sa = STATION_BY_CODE.get(a)
            sb = STATION_BY_CODE.get(b)
            if not sa or not sb:
                continue
            d = _haversine_km(sa["lat"], sa["lng"], sb["lat"], sb["lng"])
            if d > 250 or d < 0.5:  # skip huge jumps (bad data)
                continue
            weight = round(d, 1)
            current = GRAPH.get(a, {}).get(b)
            if current is None or weight < current["distance_km"]:
                seen_edges.add(key)
                GRAPH.setdefault(a, {})[b] = {"distance_km": weight}
                GRAPH.setdefault(b, {})[a] = {"distance_km": weight}
    print(f"[simulation] graph built — {len(GRAPH):,} nodes, {len(seen_edges):,} edges", flush=True)


_build_graph()


def _format_path(origin: str, destination: str, path: list[str],
                 distance_km: float, source: str) -> dict:
    coords = []
    for code in path:
        station = STATION_BY_CODE.get(code)
        if station:
            coords.append({
                "code": code,
                "lat": station["lat"],
                "lng": station["lng"],
                "name": station.get("name", code),
            })
    return {
        "origin": origin,
        "destination": destination,
        "path": path,
        "coordinates": coords,
        "distance_km": round(float(distance_km), 1),
        "hops": len(path) - 1,
        "estimated_hours": round(float(distance_km) / 55, 2),
        "route_source": source,
    }


def _historical_od_path(origin: str, destination: str) -> dict | None:
    """Use the shortest valid route actually observed for an exact OD pair."""
    matches = _DF[
        (_DF["ldngsttn"].astype(str) == origin)
        & (_DF["destination"].astype(str) == destination)
    ].sort_values("km")
    candidates = []

    for row in matches[["travl_route_part", "km"]].dropna().drop_duplicates().itertuples(index=False):
        parts = [p.strip() for p in str(row.travl_route_part).split(",") if p.strip()]
        if not parts:
            continue
        if parts[0] != origin:
            parts.insert(0, origin)
        if parts[-1] != destination:
            parts.append(destination)
        known_stations = [STATION_BY_CODE[code] for code in parts if code in STATION_BY_CODE]
        if len(known_stations) < 2:
            continue

        # Some via-only stations do not have coordinates because the source
        # station table is built from OD endpoints. Keep those valid route
        # codes, and validate the geographical shape using coordinates that
        # are available.
        segment_distances = [
            _haversine_km(
                a["lat"], a["lng"], b["lat"], b["lng"],
            )
            for a, b in zip(known_stations, known_stations[1:])
        ]
        if not segment_distances or max(segment_distances) > 250:
            continue
        candidates.append((float(row.km), len(parts), parts))

    if not candidates:
        return None
    distance_km, _, path = min(candidates, key=lambda item: (item[0], item[1]))
    return _format_path(origin, destination, path, distance_km, "historical_od")


def shortest_path(origin: str, destination: str) -> dict:
    historical = _historical_od_path(origin, destination)
    if historical:
        return historical
    if origin not in GRAPH:
        return {"error": f"origin '{origin}' not in graph"}
    if destination not in GRAPH:
        return {"error": f"destination '{destination}' not in graph"}
    dist = {origin: 0}
    prev = {origin: None}
    pq = [(0, origin)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == destination:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, edge in GRAPH[u].items():
            nd = d + edge["distance_km"]
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if destination not in dist:
        return {"error": "no path"}
    path = []
    cur = destination
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return _format_path(
        origin, destination, path, dist[destination], "network_fallback"
    )


def allocate_rakes(commodity: str, tonnes: float, priority: int = 2) -> dict:
    payload_per_rake = 58 * 58
    rakes_needed = max(1, int(-(-tonnes // payload_per_rake)))
    allocated = []
    for i in range(rakes_needed):
        allocated.append({
            "rake_id": f"RK-{commodity[:3].upper()}-{1000 + i}",
            "wagons": 58,
            "capacity_tonnes": payload_per_rake,
            "assigned_tonnes": round(min(payload_per_rake, tonnes - i * payload_per_rake), 1),
            "priority": priority,
        })
    return {
        "commodity": commodity,
        "tonnes_requested": tonnes,
        "rakes_needed": rakes_needed,
        "total_capacity": rakes_needed * payload_per_rake,
        "allocations": allocated,
    }


def detect_conflicts(trains: List[dict]) -> List[dict]:
    by_section: Dict[str, List[dict]] = {}
    for t in trains:
        section = f"{t.get('current_station')}-{t.get('next_station')}"
        by_section.setdefault(section, []).append(t)
    conflicts = []
    for section, ts in by_section.items():
        if len(ts) < 2:
            continue
        ts_sorted = sorted(ts, key=lambda x: x["eta_minutes"])
        for i in range(len(ts_sorted) - 1):
            a, b = ts_sorted[i], ts_sorted[i + 1]
            gap = abs(a["eta_minutes"] - b["eta_minutes"])
            if gap < 30:
                conflicts.append({
                    "section": section,
                    "train_a": a["number"],
                    "train_b": b["number"],
                    "commodity_a": a.get("commodity"),
                    "commodity_b": b.get("commodity"),
                    "gap_minutes": gap,
                    "severity": "high" if gap < 10 else "medium",
                    "recommendation": f"Hold {b['number']} at {a['current_station']} for {30 - gap} min",
                })
    return conflicts
