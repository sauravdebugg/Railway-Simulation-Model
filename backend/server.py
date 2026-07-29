"""
Indian Railway Digital Twin & Freight Simulation Platform — Backend
FastAPI + MongoDB + ML (scikit-learn on real FY 2025-26 OD data) + Claude LLM insights.
"""
from __future__ import annotations
import os
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict

from .real_data import (
    STATIONS_REAL, STATION_BY_CODE, ZONES_REAL, COMMODITIES_REAL, LOADTYPES_REAL,
    zones_list, build_live_trains, aggregate_kpis, aggregate_zone_stats,
    aggregate_commodity_mix, aggregate_route_analytics, aggregate_asset_utilization,
    build_congestion_from_data, heatmap_points, sample_od_pairs, COMMODITY_LABELS,
    aggregate_outgoing_stations, aggregate_incoming_stations,
    aggregate_loading_zone_dispatch, aggregate_destination_zone_arrival,
    aggregate_daily_dispatch_trend, aggregate_daily_arrival_trend,
    aggregate_top_loading_stations, aggregate_top_destination_stations,
)
from .ml_models import FreightModels
from .simulation import shortest_path, allocate_rakes, detect_conflicts, GRAPH

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL")
use_mongomock = os.environ.get("USE_MONGOMOCK", "").lower() == "true"
if use_mongomock:
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
    print("[server] using in-memory MongoDB fallback for local development", flush=True)
else:
    if not mongo_url:
        raise RuntimeError(
            "MONGO_URL is required. Set it to a MongoDB Atlas URI on Vercel, "
            "or set USE_MONGOMOCK=true for local development only."
        )
    client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get("DB_NAME", "railway_twin")]

print("[server] loading freight ML models...", flush=True)
ML = FreightModels()
print(
    f"[server] ML source: {'cache' if ML.loaded_from_cache else 'training'}",
    flush=True,
)
print(f"[server] ML ready on {ML.trained_rows:,} rows | ETA R²={ML.eta_score} | Circuit R²={ML.circuit_score}",
      flush=True)

app = FastAPI(title="Indian Railway Digital Twin API", version="1.0.0")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("railway")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# --- In-memory live state ---
LIVE_TRAINS = build_live_trains(6000)
CONGESTION = build_congestion_from_data(60)


# ========= Models =========
class SimulationRequest(BaseModel):
    origin: str
    destination: str
    commodity: str = "Coal"
    tonnes: float = 3500
    priority: int = 2


class PredictionRequest(BaseModel):
    distance_km: float = 500
    wagons: int = 58
    loaded_pct: float = 85
    priority: int = 2
    congestion: float = 0.4
    weather: float = 0.2
    is_dfc: int = 0


class DemandRequest(BaseModel):
    commodity: str = "Coal"
    zone: str = "ER"
    current_tonnes: float = 12000
    growth_pct: float = 5
    seasonality: float = 0.08
    horizon_days: int = 30


class InsightRequest(BaseModel):
    context: str
    question: str = "Provide operational insights in 3 crisp bullets."


class Report(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    kind: str = "custom"
    payload: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


# ========= Meta =========
@api.get("/")
async def root():
    return {"service": "Indian Railway Digital Twin", "status": "ok",
            "records": ML.trained_rows, "stations": len(STATIONS_REAL),
            "zones": len(ZONES_REAL), "time": now_iso()}


@api.get("/zones")
async def get_zones():
    z = zones_list()
    return {"count": len(z), "zones": z}


@api.get("/stations")
async def get_stations(zone: Optional[str] = None, limit: int = 500):
    data = STATIONS_REAL if not zone else [s for s in STATIONS_REAL if s.get("zone") == zone]
    return {"count": len(data), "stations": data[:limit]}


@api.get("/meta/commodities")
async def meta_commodities():
    return {"count": len(COMMODITIES_REAL),
            "commodities": [{"code": c, "name": COMMODITY_LABELS.get(c, c)} for c in COMMODITIES_REAL]}


@api.get("/meta/loadtypes")
async def meta_loadtypes():
    return {"count": len(LOADTYPES_REAL), "loadtypes": LOADTYPES_REAL}


@api.get("/meta/sample-od-pairs")
async def meta_od():
    return {"pairs": sample_od_pairs(30)}


# ========= Trains / Live =========
@api.get("/trains")
async def get_trains(status: Optional[str] = None, zone: Optional[str] = None, limit: int = 200):
    data = LIVE_TRAINS
    if status:
        data = [t for t in data if t["status"] == status]
    if zone:
        data = [t for t in data if t["zone"] == zone]
    return {"count": len(data), "trains": data[:limit]}


@api.get("/trains/{train_id}")
async def get_train(train_id: str):
    for t in LIVE_TRAINS:
        if t["id"] == train_id or t["number"] == train_id:
            return t
    raise HTTPException(status_code=404, detail="Train not found")


@api.post("/trains/refresh")
async def refresh_trains():
    global LIVE_TRAINS
    LIVE_TRAINS = build_live_trains(6000)
    return {"refreshed": True, "trains": len(LIVE_TRAINS)}


@api.get("/congestion")
async def get_congestion():
    return {"count": len(CONGESTION), "sections": CONGESTION}


# ========= Dashboard =========
@api.get("/dashboard/kpis")
async def kpis():
    return aggregate_kpis(LIVE_TRAINS)


@api.get("/dashboard/zone-stats")
async def zone_stats():
    return {"zones": aggregate_zone_stats()}


@api.get("/dashboard/commodity-mix")
async def commodity_mix():
    return {"mix": aggregate_commodity_mix(15)}


@api.get("/dashboard/route-analytics")
async def route_analytics():
    return {"routes": aggregate_route_analytics(20)}


@api.get("/dashboard/outgoing-stations")
async def outgoing_stations(top: int = 12):
    return {"stations": aggregate_outgoing_stations(top)}


@api.get("/dashboard/incoming-stations")
async def incoming_stations(top: int = 12):
    return {"stations": aggregate_incoming_stations(top)}


@api.get("/dashboard/loading-zone-dispatch")
async def loading_zone_dispatch():
    return {"zones": aggregate_loading_zone_dispatch()}


@api.get("/dashboard/destination-zone-arrival")
async def destination_zone_arrival():
    return {"zones": aggregate_destination_zone_arrival()}


@api.get("/dashboard/daily-dispatch-trend")
async def daily_dispatch_trend(days: int = 30):
    return {"trend": aggregate_daily_dispatch_trend(days)}


@api.get("/dashboard/daily-arrival-trend")
async def daily_arrival_trend(days: int = 30):
    return {"trend": aggregate_daily_arrival_trend(days)}


@api.get("/dashboard/top-loading-stations")
async def top_loading_stations(top: int = 10):
    return {"stations": aggregate_top_loading_stations(top)}


@api.get("/dashboard/top-destination-stations")
async def top_destination_stations(top: int = 10):
    return {"stations": aggregate_top_destination_stations(top)}


# ========= Simulation =========
@api.post("/simulation/plan")
async def sim_plan(req: SimulationRequest):
    path = shortest_path(req.origin, req.destination)
    if "error" in path:
        raise HTTPException(status_code=400, detail=path["error"])
    alloc = allocate_rakes(req.commodity, req.tonnes, req.priority)
    payload = {
        "distance_km": path["distance_km"],
        "wagons": 58,
        "loaded_pct": 90,
        "priority": req.priority,
        "congestion": 0.4,
        "weather": 0.2,
        "is_dfc": 1 if path["distance_km"] > 800 else 0,
    }
    eta = ML.predict_eta(payload)
    circuit = ML.predict_circuit(payload)
    return {
        "plan_id": str(uuid.uuid4()),
        "path": path,
        "allocation": alloc,
        "eta": eta,
        "circuit": circuit,
        "created_at": now_iso(),
    }


@api.get("/simulation/conflicts")
async def sim_conflicts():
    conflicts = detect_conflicts(LIVE_TRAINS)
    return {"count": len(conflicts), "conflicts": conflicts}


# ========= Predictions =========
@api.post("/predict/eta")
async def predict_eta(req: PredictionRequest):
    return ML.predict_eta(req.model_dump())


@api.post("/predict/circuit-time")
async def predict_circuit(req: PredictionRequest):
    return ML.predict_circuit(req.model_dump())


@api.post("/predict/utilization")
async def predict_util(req: PredictionRequest):
    return ML.predict_utilization(req.model_dump())


@api.post("/predict/congestion")
async def predict_cong(req: PredictionRequest):
    return ML.predict_congestion(req.model_dump())


@api.post("/predict/demand")
async def predict_demand(req: DemandRequest):
    return ML.predict_demand(req.model_dump())


# ========= Analytics =========
@api.get("/analytics/heatmap")
async def heatmap():
    return {"points": heatmap_points(200)}


@api.get("/analytics/asset-utilization")
async def asset_util():
    return {"assets": aggregate_asset_utilization()}


# ========= Reports =========
@api.post("/reports")
async def create_report(r: Report):
    doc = r.model_dump()
    await db.reports.insert_one(doc)
    return r


@api.get("/reports")
async def list_reports():
    docs = await db.reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"count": len(docs), "reports": docs}


@api.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    res = await db.reports.delete_one({"id": report_id})
    return {"deleted": res.deleted_count}


# ========= Settings =========
class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    theme: str = "dark"
    map_provider: str = "osm"
    refresh_interval_sec: int = 30
    default_zone: str = "NR"
    alerts_enabled: bool = True


@api.get("/settings")
async def get_settings():
    doc = await db.settings.find_one({"key": "global"}, {"_id": 0})
    if not doc:
        defaults = Settings().model_dump()
        await db.settings.insert_one({**defaults, "key": "global"})
        return defaults
    doc.pop("key", None)
    return doc


@api.post("/settings")
async def save_settings(s: Settings):
    doc = s.model_dump()
    doc["key"] = "global"
    await db.settings.update_one({"key": "global"}, {"$set": doc}, upsert=True)
    doc.pop("key", None)
    return doc


# ========= LLM Insights =========
@api.post("/ai/insight")
async def ai_insight(req: InsightRequest):
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Optional AI integration is not installed in this deployment",
        ) from exc

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY missing")

    system_msg = (
        "You are a Senior Indian Railways freight operations analyst. "
        "You analyse KPIs, congestion, rake allocation and give crisp, decisive, "
        "actionable operational insights. Never use fluff. Use short bullet points. "
        "Reference zones (NR/SR/CR/WR/ER/SCR/ECR/DFCR), corridors (DFC East/West), and commodities. "
        "Keep total response under 180 words."
    )

    chat = LlmChat(
        api_key=api_key,
        session_id=f"insight-{uuid.uuid4()}",
        system_message=system_msg,
    ).with_model("anthropic", "claude-sonnet-4-6")

    msg = UserMessage(text=f"CONTEXT:\n{req.context}\n\nTASK:\n{req.question}")

    async def event_gen():
        try:
            async for ev in chat.stream_message(msg):
                if isinstance(ev, TextDelta):
                    # SSE-safe: replace newlines with literal \n
                    content = ev.content.replace("\n", "\\n")
                    yield f"data: {content}\n\n"
                elif isinstance(ev, StreamDone):
                    yield "data: [DONE]\n\n"
                    break
        except Exception as e:
            log.exception("LLM stream failed")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.include_router(api)

cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=cors_origins != ["*"],
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown():
    client.close()
