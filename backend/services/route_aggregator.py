# backend/services/route_aggregator.py
import httpx
from typing import List
from models import RouteOption, StepDetail

class RouteAggregator:
    GAODE_BASE = "https://restapi.amap.com/v3/direction"

    MODE_ENDPOINT = {
        "transit": "/direction/transit/integrated",
        "driving": "/driving",
        "bicycling": "/bicycling",
        "walking": "/walking",
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=10.0)

    async def query_segment(self, from_loc: dict, to_loc: dict, mode: str) -> RouteOption:
        """Query Gaode for a single segment with a specific mode."""
        endpoint = self.MODE_ENDPOINT.get(mode)
        if not endpoint:
            raise ValueError(f"Unsupported mode: {mode}")

        url = f"{self.GAODE_BASE}{endpoint}"
        params = {
            "key": self.api_key,
            "origin": f"{from_loc['lng']},{from_loc['lat']}",
            "destination": f"{to_loc['lng']},{to_loc['lat']}",
            "extensions": "all",
        }

        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_response(data, mode)

    def _parse_response(self, data: dict, mode: str) -> RouteOption:
        """Extract duration, distance, steps from Gaode response."""
        if data.get("status") != "1":
            # No route found
            return RouteOption(mode=mode, duration=0, cost=0.0, distance=0, steps=[])

        route = data.get("route", {})
        paths = route.get("paths", [])
        if not paths:
            return RouteOption(mode=mode, duration=0, cost=0.0, distance=0, steps=[])

        path = paths[0]
        steps = []
        for s in path.get("steps", []):
            steps.append(StepDetail(
                instruction=s.get("instruction", ""),
                distance=int(s.get("distance", 0)),
                duration=int(s.get("duration", 0)),
            ))

        # Cost estimation: driving mode gets taxi estimate; others are 0
        cost = 0.0
        if mode == "driving":
            cost = self._estimate_taxi_cost(int(path.get("distance", 0)))

        return RouteOption(
            mode=mode,
            duration=int(path.get("duration", 0)),
            cost=cost,
            distance=int(path.get("distance", 0)),
            steps=steps,
        )

    def _estimate_taxi_cost(self, distance_meters: int) -> float:
        """Rough taxi cost estimate: 14 yuan base + 2.5 yuan/km."""
        km = distance_meters / 1000
        return round(14 + km * 2.5, 1)
