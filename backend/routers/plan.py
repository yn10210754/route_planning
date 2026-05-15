# backend/routers/plan.py
from fastapi import APIRouter
from models import PlanRequest, PlanResponse, RouteOption
from services.train_proxy import TrainProxy
from services.route_aggregator import RouteAggregator
from services.route_optimizer import RouteOptimizer
from config import settings

router = APIRouter()
train_proxy = TrainProxy()
optimizer = RouteOptimizer()

def _parse_duration(duration_str: str) -> int:
    """Convert '02:30' to seconds."""
    try:
        parts = duration_str.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60
    except Exception:
        return 0

@router.post("/plan", response_model=PlanResponse)
async def plan_route(req: PlanRequest):
    aggregator = RouteAggregator(settings.ensure_gaode_key())

    segment_options = []
    for seg in req.segments:
        options = []
        for mode in seg.modes:
            if mode == "train":
                trains = await train_proxy.query_trains(
                    seg.from_loc.name, seg.to_loc.name, req.departure_time[:10]
                )
                for t in trains:
                    options.append(RouteOption(
                        mode="train",
                        duration=_parse_duration(t.get("duration", "")),
                        cost=35.0,
                        distance=0,
                        steps=[],
                    ))
            else:
                route = await aggregator.query_segment(
                    from_loc={"lng": seg.from_loc.lng, "lat": seg.from_loc.lat},
                    to_loc={"lng": seg.to_loc.lng, "lat": seg.to_loc.lat},
                    mode=mode,
                )
                if route.duration > 0:
                    options.append(route)
        segment_options.append(options)

    plans = optimizer.find_best_plans(segment_options, req.optimize_by)
    return PlanResponse(plans=plans)
