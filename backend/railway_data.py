"""
Indian Railway seed data — Realistic stations, zones, routes, freight rakes.
"""
from datetime import datetime, timezone
import random
import uuid

# Indian Railway Zones
ZONES = [
    {"code": "NR", "name": "Northern Railway", "hq": "New Delhi", "color": "#007AFF"},
    {"code": "SR", "name": "Southern Railway", "hq": "Chennai", "color": "#34C759"},
    {"code": "CR", "name": "Central Railway", "hq": "Mumbai CSMT", "color": "#FFD60A"},
    {"code": "WR", "name": "Western Railway", "hq": "Mumbai Central", "color": "#FF9500"},
    {"code": "ER", "name": "Eastern Railway", "hq": "Kolkata", "color": "#FF3B30"},
    {"code": "NER", "name": "North Eastern Railway", "hq": "Gorakhpur", "color": "#AF52DE"},
    {"code": "SER", "name": "South Eastern Railway", "hq": "Kolkata", "color": "#5AC8FA"},
    {"code": "SCR", "name": "South Central Railway", "hq": "Secunderabad", "color": "#FF2D55"},
    {"code": "NCR", "name": "North Central Railway", "hq": "Prayagraj", "color": "#64D2FF"},
    {"code": "ECR", "name": "East Central Railway", "hq": "Hajipur", "color": "#BF5AF2"},
]

# Major freight stations across India with lat/lng
STATIONS = [
    {"code": "NDLS", "name": "New Delhi", "lat": 28.6431, "lng": 77.2197, "zone": "NR", "type": "junction", "platforms": 16},
    {"code": "CSMT", "name": "Mumbai CSMT", "lat": 18.9401, "lng": 72.8352, "zone": "CR", "type": "terminal", "platforms": 18},
    {"code": "MAS", "name": "Chennai Central", "lat": 13.0827, "lng": 80.2707, "zone": "SR", "type": "terminal", "platforms": 15},
    {"code": "HWH", "name": "Howrah Jn", "lat": 22.5804, "lng": 88.3428, "zone": "ER", "type": "terminal", "platforms": 23},
    {"code": "SBC", "name": "Bengaluru", "lat": 12.9784, "lng": 77.5686, "zone": "SWR", "type": "junction", "platforms": 10},
    {"code": "SC", "name": "Secunderabad Jn", "lat": 17.4344, "lng": 78.5013, "zone": "SCR", "type": "junction", "platforms": 10},
    {"code": "ADI", "name": "Ahmedabad Jn", "lat": 23.0225, "lng": 72.5714, "zone": "WR", "type": "junction", "platforms": 12},
    {"code": "JP", "name": "Jaipur Jn", "lat": 26.9196, "lng": 75.7889, "zone": "NWR", "type": "junction", "platforms": 7},
    {"code": "LKO", "name": "Lucknow Charbagh", "lat": 26.8306, "lng": 80.9236, "zone": "NR", "type": "junction", "platforms": 9},
    {"code": "PNBE", "name": "Patna Jn", "lat": 25.6018, "lng": 85.1416, "zone": "ECR", "type": "junction", "platforms": 10},
    {"code": "BBS", "name": "Bhubaneswar", "lat": 20.2698, "lng": 85.8434, "zone": "ECoR", "type": "junction", "platforms": 6},
    {"code": "NGP", "name": "Nagpur Jn", "lat": 21.1526, "lng": 79.0873, "zone": "CR", "type": "junction", "platforms": 8},
    {"code": "BPL", "name": "Bhopal Jn", "lat": 23.2686, "lng": 77.4001, "zone": "WCR", "type": "junction", "platforms": 6},
    {"code": "GHY", "name": "Guwahati", "lat": 26.1809, "lng": 91.7514, "zone": "NFR", "type": "junction", "platforms": 7},
    {"code": "TVC", "name": "Trivandrum Central", "lat": 8.4879, "lng": 76.9525, "zone": "SR", "type": "terminal", "platforms": 5},
    {"code": "CNB", "name": "Kanpur Central", "lat": 26.4551, "lng": 80.3505, "zone": "NCR", "type": "junction", "platforms": 10},
    {"code": "ALD", "name": "Prayagraj Jn", "lat": 25.4479, "lng": 81.8232, "zone": "NCR", "type": "junction", "platforms": 10},
    {"code": "GZB", "name": "Ghaziabad Jn", "lat": 28.6692, "lng": 77.4538, "zone": "NR", "type": "junction", "platforms": 6},
    {"code": "MGS", "name": "Mughal Sarai (DDU)", "lat": 25.2833, "lng": 83.1167, "zone": "ECR", "type": "junction", "platforms": 8},
    {"code": "BSB", "name": "Varanasi Jn", "lat": 25.3176, "lng": 82.9739, "zone": "NER", "type": "junction", "platforms": 9},
    {"code": "KYN", "name": "Kalyan Jn", "lat": 19.2437, "lng": 73.1355, "zone": "CR", "type": "junction", "platforms": 8},
    {"code": "PUNE", "name": "Pune Jn", "lat": 18.5289, "lng": 73.8744, "zone": "CR", "type": "junction", "platforms": 6},
    {"code": "VSKP", "name": "Visakhapatnam", "lat": 17.7247, "lng": 83.3018, "zone": "ECoR", "type": "port_terminal", "platforms": 8},
    {"code": "TATA", "name": "Tatanagar Jn", "lat": 22.7717, "lng": 86.1444, "zone": "SER", "type": "junction", "platforms": 5},
    {"code": "BSP", "name": "Bilaspur Jn", "lat": 22.0797, "lng": 82.1409, "zone": "SECR", "type": "junction", "platforms": 8},
    {"code": "RTM", "name": "Ratlam Jn", "lat": 23.3315, "lng": 75.0367, "zone": "WR", "type": "junction", "platforms": 7},
    {"code": "KOTA", "name": "Kota Jn", "lat": 25.1854, "lng": 75.8391, "zone": "WCR", "type": "junction", "platforms": 5},
    {"code": "MFP", "name": "Muzaffarpur Jn", "lat": 26.1224, "lng": 85.3906, "zone": "ECR", "type": "junction", "platforms": 6},
    {"code": "KGP", "name": "Kharagpur Jn", "lat": 22.3399, "lng": 87.3229, "zone": "SER", "type": "junction", "platforms": 12},
    {"code": "MB", "name": "Moradabad Jn", "lat": 28.8386, "lng": 78.7733, "zone": "NR", "type": "junction", "platforms": 7},
]

# Freight-heavy routes (corridors)
ROUTES = [
    {"id": "R-DFC-EAST", "name": "Eastern Dedicated Freight Corridor", "path": ["NDLS", "GZB", "CNB", "ALD", "MGS", "PNBE", "HWH"], "type": "DFC", "electrified": True, "priority": 1},
    {"id": "R-DFC-WEST", "name": "Western Dedicated Freight Corridor", "path": ["NDLS", "JP", "KOTA", "RTM", "ADI", "CSMT"], "type": "DFC", "electrified": True, "priority": 1},
    {"id": "R-COAL-01", "name": "Coal Corridor Bilaspur–Kolkata", "path": ["BSP", "TATA", "KGP", "HWH"], "type": "coal", "electrified": True, "priority": 2},
    {"id": "R-STEEL-01", "name": "Steel Corridor Tata–Chennai", "path": ["TATA", "KGP", "VSKP", "MAS"], "type": "steel", "electrified": True, "priority": 2},
    {"id": "R-GRAIN-01", "name": "Grain Corridor Punjab–South", "path": ["NDLS", "JP", "ADI", "PUNE", "SBC"], "type": "grain", "electrified": True, "priority": 3},
    {"id": "R-CEMENT-01", "name": "Cement Corridor Nagpur–Kanpur", "path": ["NGP", "BPL", "CNB", "LKO"], "type": "cement", "electrified": True, "priority": 3},
    {"id": "R-CONT-01", "name": "Container Corridor JNPT–Delhi", "path": ["CSMT", "KYN", "PUNE", "RTM", "KOTA", "JP", "NDLS"], "type": "container", "electrified": True, "priority": 1},
]

COMMODITIES = ["Coal", "Iron Ore", "Cement", "Steel", "Grain", "Containers", "POL", "Fertiliser", "Automobile"]
RAKE_TYPES = ["BOXN", "BOBRN", "BCN", "BTPN", "BTAP", "BCFC", "BOST"]


def _distance(a, b):
    # crude distance for demo (km) using lat/lng diff * ~111
    dx = (a["lat"] - b["lat"]) * 111
    dy = (a["lng"] - b["lng"]) * 100
    return round((dx * dx + dy * dy) ** 0.5, 1)


def generate_trains(n=40):
    stn_map = {s["code"]: s for s in STATIONS}
    trains = []
    for i in range(n):
        route = random.choice(ROUTES)
        path = route["path"]
        origin = path[0]
        dest = path[-1]
        commodity = random.choice(COMMODITIES) if route["type"] == "container" else {
            "coal": "Coal", "steel": "Steel", "grain": "Grain", "cement": "Cement",
            "container": "Containers", "DFC": random.choice(COMMODITIES)
        }.get(route["type"], "Mixed")
        rake_type = random.choice(RAKE_TYPES)
        wagons = random.randint(42, 58)
        loaded_pct = round(random.uniform(60, 100), 1)
        # progress 0..1 along route
        progress = round(random.uniform(0.05, 0.95), 3)
        # current position: interpolate along path
        seg_count = len(path) - 1
        idx_f = progress * seg_count
        idx = int(idx_f)
        frac = idx_f - idx
        if idx >= seg_count:
            idx, frac = seg_count - 1, 1.0
        a = stn_map[path[idx]]
        b = stn_map[path[idx + 1]]
        cur_lat = a["lat"] + (b["lat"] - a["lat"]) * frac
        cur_lng = a["lng"] + (b["lng"] - a["lng"]) * frac
        # total distance
        total_km = sum(_distance(stn_map[path[j]], stn_map[path[j+1]]) for j in range(seg_count))
        speed = random.randint(35, 75)
        delay_min = random.choice([0, 0, 0, 15, 30, 45, 60, 90, 120])
        status = "on_time" if delay_min <= 15 else ("delayed" if delay_min < 90 else "critical")
        trains.append({
            "id": f"FT{20000 + i}",
            "number": f"{20000 + i}",
            "name": f"{origin}-{dest} {commodity} Rake",
            "route_id": route["id"],
            "route_name": route["name"],
            "origin": origin,
            "destination": dest,
            "current_station": path[idx],
            "next_station": path[idx + 1],
            "current_lat": round(cur_lat, 4),
            "current_lng": round(cur_lng, 4),
            "commodity": commodity,
            "rake_type": rake_type,
            "wagons": wagons,
            "loaded_pct": loaded_pct,
            "load_tonnes": round(wagons * 58 * loaded_pct / 100, 1),
            "speed_kmph": speed,
            "progress": progress,
            "distance_total_km": round(total_km, 1),
            "distance_covered_km": round(total_km * progress, 1),
            "delay_min": delay_min,
            "status": status,
            "zone": stn_map[origin]["zone"],
            "eta_minutes": max(30, int((total_km * (1 - progress)) / max(speed, 20) * 60)) + delay_min,
            "circuit_time_hrs": round(random.uniform(48, 240), 1),
        })
    return trains


def generate_congestion():
    """Simulate section congestion 0..1 per pair of consecutive stations across routes"""
    seen = set()
    out = []
    for r in ROUTES:
        p = r["path"]
        for i in range(len(p) - 1):
            key = tuple(sorted([p[i], p[i+1]]))
            if key in seen:
                continue
            seen.add(key)
            level = round(random.uniform(0.15, 0.95), 2)
            out.append({
                "section_id": f"{key[0]}-{key[1]}",
                "from_station": key[0],
                "to_station": key[1],
                "congestion": level,
                "avg_speed_kmph": round(80 - level * 55, 1),
                "trains_in_section": random.randint(1, 8),
                "route_id": r["id"],
            })
    return out


def now_iso():
    return datetime.now(timezone.utc).isoformat()
