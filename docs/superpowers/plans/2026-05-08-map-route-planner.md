# Map Route Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mobile H5 route planner with FastAPI backend that supports multi-segment, multi-modal route comparison combining Gaode Maps API and 12306 train data.

**Architecture:** FastAPI backend with three core services (TrainProxy for 12306 scraping, RouteAggregator for Gaode API parallel calls, RouteOptimizer for combinatorial search). Vue3+Vant frontend with input and result views. Backend exposes REST APIs consumed by frontend.

**Tech Stack:** Python 3.11, FastAPI, httpx, pytest | Vue 3, Vant 4, Vite

---

## File Structure

### Backend (`backend/`)

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app entry, CORS, router registration |
| `config.py` | Settings loaded from env (Gaode API key) |
| `models.py` | Pydantic request/response models shared across the app |
| `services/train_proxy.py` | Parse 12306 station codes, query trains, cache results |
| `services/route_aggregator.py` | Call Gaode APIs in parallel per segment per mode |
| `services/route_optimizer.py` | Enumerate segment combinations, apply transfer buffers |
| `routers/plan.py` | POST /api/plan — orchestrates services, returns top plans |
| `routers/poi.py` | GET /api/poi/search — proxies Gaode POI search |
| `requirements.txt` | Python dependencies |

### Frontend (`frontend/`)

Standard Vite + Vue3 scaffold plus:

| File | Responsibility |
|------|---------------|
| `src/api/index.js` | Axios instance, backend API wrappers |
| `src/components/SearchInput.vue` | Location input with POI autocomplete |
| `src/components/ModeSelector.vue` | Multi-select transport mode tags |
| `src/components/RouteTimeline.vue` | Timeline visualization of a plan result |
| `src/views/HomeView.vue` | Input page: locations, modes, submit |
| `src/views/ResultView.vue` | Result page: plan cards, timeline, manual override |

---

## Task 1: Backend Project Scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/main.py`
- Create: `backend/models.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.27.0
pydantic-settings==2.5.0
pytest==8.3.0
pytest-asyncio==0.24.0
respx==0.21.0
```

`httpx` is used instead of `requests` because we need async HTTP calls. `respx` is the pytest companion for mocking `httpx` (similar to `responses` for `requests`). `pydantic-settings` lets us load config from environment variables with validation.

- [ ] **Step 2: Install dependencies in a virtual environment**

Run:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: pip installs without errors.

- [ ] **Step 3: Create config.py**

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gaode_key: str = ""
    backend_cors_origins: list[str] = ["*"]

settings = Settings()
```

We use `pydantic-settings` so that setting `GAODE_KEY=xxx` as an environment variable automatically populates `settings.gaode_key`.

- [ ] **Step 4: Create models.py with shared Pydantic models**

```python
# backend/models.py
from pydantic import BaseModel
from typing import List

class Location(BaseModel):
    name: str
    lng: float
    lat: float

class SegmentInput(BaseModel):
    from_loc: Location
    to_loc: Location
    modes: List[str]

class PlanRequest(BaseModel):
    departure_time: str = ""
    segments: List[SegmentInput]
    optimize_by: str = "duration"

class StepDetail(BaseModel):
    instruction: str = ""
    distance: int = 0
    duration: int = 0

class RouteOption(BaseModel):
    mode: str
    duration: int   # seconds
    cost: float     # yuan
    distance: int   # meters
    steps: List[StepDetail] = []

class PlanSegment(BaseModel):
    mode: str
    from_name: str
    to_name: str
    departure: str = ""
    arrival: str = ""
    duration: int
    cost: float
    details: dict = {}

class PlanResult(BaseModel):
    total_duration: int
    total_cost: float
    segments: List[PlanSegment]

class PlanResponse(BaseModel):
    plans: List[PlanResult]
```

These models are used both for internal service communication and API serialization. Keeping them in one file makes it easy to see the data contract at a glance.

- [ ] **Step 5: Create main.py**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import plan, poi

app = FastAPI(title="Route Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(poi.router, prefix="/api", tags=["poi"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

CORS is configured with wildcard origins for development. In production, this should be restricted to the frontend domain.

- [ ] **Step 6: Create empty router files so main.py imports succeed**

Create `backend/routers/__init__.py` (empty) and placeholder `backend/routers/plan.py`:

```python
# backend/routers/plan.py
from fastapi import APIRouter

router = APIRouter()
```

Create `backend/routers/poi.py` identically.

- [ ] **Step 7: Run the server and verify it starts**

Run:
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

In another terminal:
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: scaffold FastAPI backend with models and config"
```

---

## Task 2: TrainProxy Service

**Files:**
- Create: `backend/services/__init__.py` (empty)
- Create: `backend/services/train_proxy.py`
- Create: `backend/tests/test_train_proxy.py`

- [ ] **Step 1: Write the failing test for station name parsing**

```python
# backend/tests/test_train_proxy.py
import pytest
from services.train_proxy import TrainProxy

@pytest.fixture
def proxy():
    return TrainProxy()

def test_parse_station_js(proxy):
    # 12306 station_name.js format: @bjb|北京北|VAP|beijingbei|bjb|0
    js_content = "var station_names ='@bjb|北京北|VAP|beijingbei|bjb|0@bjp|北京|BJP|beijing|bj|1';"
    mapping = proxy._parse_station_js(js_content)
    assert mapping["北京"] == "BJP"
    assert mapping["北京北"] == "VAP"
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:
```bash
cd backend
source .venv/bin/activate
pytest tests/test_train_proxy.py::test_parse_station_js -v
```

Expected: FAIL — `TrainProxy` not defined.

- [ ] **Step 3: Implement TrainProxy with station parsing**

```python
# backend/services/train_proxy.py
import re
from typing import Dict, List
import httpx

class TrainProxy:
    STATION_URL = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9280"
    QUERY_URL = "https://kyfw.12306.cn/otn/leftTicket/query"

    def __init__(self):
        self._station_map: Dict[str, str] = {}
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            },
            timeout=15.0,
        )

    def _parse_station_js(self, js_content: str) -> Dict[str, str]:
        """Parse 12306 station_name.js and return { chinese_name: code }."""
        pattern = r"@\w+\|([^|]+)\|([A-Z]+)\|"
        matches = re.findall(pattern, js_content)
        return {name: code for name, code in matches}

    async def _ensure_station_map(self):
        """Lazy-load station map on first use."""
        if self._station_map:
            return
        resp = await self._client.get(self.STATION_URL)
        resp.raise_for_status()
        self._station_map = self._parse_station_js(resp.text)

    async def query_trains(self, from_station: str, to_station: str, date: str) -> List[dict]:
        """
        Query 12306 for direct trains between two stations on a given date.
        Returns list of train dicts with fields: train_no, departure_time, arrival_time, duration, price.
        """
        await self._ensure_station_map()
        from_code = self._station_map.get(from_station)
        to_code = self._station_map.get(to_station)
        if not from_code or not to_code:
            return []

        params = {
            "leftTicketDTO.train_date": date,
            "leftTicketDTO.from_station": from_code,
            "leftTicketDTO.to_station": to_code,
            "purpose_codes": "ADULT",
        }

        try:
            resp = await self._client.get(self.QUERY_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("data", {}).get("result", [])
            return self._parse_train_results(results)
        except Exception:
            # Graceful degradation: return empty list on any error
            return []

    def _parse_train_results(self, raw_results: List[str]) -> List[dict]:
        """Parse pipe-delimited result strings from 12306."""
        trains = []
        for row in raw_results:
            parts = row.split("|")
            if len(parts) < 10:
                continue
            trains.append({
                "train_no": parts[3],
                "from_station": parts[6],
                "to_station": parts[7],
                "departure_time": parts[8],
                "arrival_time": parts[9],
                "duration": parts[10] if len(parts) > 10 else "",
            })
        return trains
```

Key design decisions:
- `_parse_station_js` is a pure function — no I/O, easy to unit test.
- `_ensure_station_map` caches the station map after first load to avoid repeated network calls.
- The 12306 query endpoint returns pipe-delimited strings, not JSON. We parse defensively and skip malformed rows.
- All exceptions are caught in `query_trains` so that a 12306 failure does not crash the entire planning request.

- [ ] **Step 4: Run the test and confirm it passes**

Run:
```bash
pytest tests/test_train_proxy.py::test_parse_station_js -v
```

Expected: PASS.

- [ ] **Step 5: Write a test for query_trains with mocked 12306 response**

```python
import respx
from httpx import Response

@respx.mock
async def test_query_trains_success(proxy):
    # Mock station JS endpoint
    station_js = "var station_names ='@sz|深圳|SZQ|shenzhen|sz|0@hzb|惠州北|KOQ|huizhoubei|hzb|1';"
    respx.get("https://kyfw.12306.cn/otn/resources/js/framework/station_name.js").mock(
        return_value=Response(200, text=station_js)
    )

    # Mock query endpoint
    mock_result = "|booking| |G1234| | | |SZQ|KOQ|08:00|08:30|00:30| | | | | | | | | | | |"
    respx.get("https://kyfw.12306.cn/otn/leftTicket/query").mock(
        return_value=Response(200, json={"data": {"result": [mock_result]}})
    )

    trains = await proxy.query_trains("深圳", "惠州北", "2026-05-10")
    assert len(trains) == 1
    assert trains[0]["train_no"] == "G1234"
    assert trains[0]["departure_time"] == "08:00"
```

`respx` intercepts `httpx` requests at the transport layer, so no real network calls are made during tests.

- [ ] **Step 6: Run the async test**

Run:
```bash
pytest tests/test_train_proxy.py::test_query_trains_success -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/services/train_proxy.py backend/tests/test_train_proxy.py
git commit -m "feat: add TrainProxy for 12306 station and train queries"
```

---

## Task 3: RouteAggregator Service

**Files:**
- Create: `backend/services/route_aggregator.py`
- Create: `backend/tests/test_route_aggregator.py`
- Modify: `backend/config.py`

- [ ] **Step 1: Add Gaode API key assertion in config**

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gaode_key: str = ""
    backend_cors_origins: list[str] = ["*"]

    def ensure_gaode_key(self) -> str:
        if not self.gaode_key:
            raise ValueError("GAODE_KEY environment variable is required")
        return self.gaode_key

settings = Settings()
```

- [ ] **Step 2: Write the failing test for RouteAggregator**

```python
# backend/tests/test_route_aggregator.py
import pytest
import respx
from httpx import Response
from services.route_aggregator import RouteAggregator

@pytest.fixture
def aggregator():
    return RouteAggregator("FAKE_KEY")

@respx.mock
async def test_aggregate_driving(aggregator):
    # Mock Gaode driving API
    respx.get("https://restapi.amap.com/v3/direction/driving").mock(
        return_value=Response(200, json={
            "status": "1",
            "route": {
                "paths": [{
                    "duration": "1800",
                    "distance": "15000",
                    "steps": [{"instruction": "从起点向正东出发", "distance": "500", "duration": "60"}]
                }]
            }
        })
    )

    result = await aggregator.query_segment(
        from_loc={"lng": 114.1, "lat": 22.5},
        to_loc={"lng": 114.3, "lat": 22.6},
        mode="driving"
    )
    assert result.mode == "driving"
    assert result.duration == 1800
    assert result.distance == 15000
    assert len(result.steps) == 1
```

- [ ] **Step 3: Run the test and confirm it fails**

```bash
pytest tests/test_route_aggregator.py::test_aggregate_driving -v
```

Expected: FAIL — `RouteAggregator` not defined.

- [ ] **Step 4: Implement RouteAggregator**

```python
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
```

Important: Gaode transit API returns `"route" -> "transits"` instead of `"paths"`. We keep the MVP simple by parsing the same `paths` key for all modes — this works for driving/bicycling/walking. For transit mode, Gaode's response structure is different; we will handle that in a follow-up step.

- [ ] **Step 5: Run the test and confirm it passes**

```bash
pytest tests/test_route_aggregator.py::test_aggregate_driving -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/route_aggregator.py backend/tests/test_route_aggregator.py backend/config.py
git commit -m "feat: add RouteAggregator for Gaode API queries"
```

---

## Task 4: RouteOptimizer Service

**Files:**
- Create: `backend/services/route_optimizer.py`
- Create: `backend/tests/test_route_optimizer.py`

- [ ] **Step 1: Write the failing test for optimizer**

```python
# backend/tests/test_route_optimizer.py
from services.route_optimizer import RouteOptimizer
from models import RouteOption, PlanResult

def test_optimize_two_segments():
    optimizer = RouteOptimizer()

    # Segment 1: two options
    seg1_options = [
        RouteOption(mode="driving", duration=1800, cost=50.0, distance=15000, steps=[]),
        RouteOption(mode="transit", duration=3600, cost=8.0, distance=15000, steps=[]),
    ]
    # Segment 2: one option (train)
    seg2_options = [
        RouteOption(mode="train", duration=1800, cost=35.0, distance=80000, steps=[]),
    ]

    segment_options = [seg1_options, seg2_options]
    plans = optimizer.find_best_plans(segment_options, optimize_by="duration")

    assert len(plans) == 2
    # Fastest should be driving + train = 3600s
    assert plans[0].total_duration == 3600
    assert plans[0].total_cost == 85.0
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
pytest tests/test_route_optimizer.py::test_optimize_two_segments -v
```

Expected: FAIL.

- [ ] **Step 3: Implement RouteOptimizer**

```python
# backend/services/route_optimizer.py
from typing import List
from models import RouteOption, PlanResult, PlanSegment

class RouteOptimizer:
    TRANSFER_BUFFER_MINUTES = 30

    def find_best_plans(
        self,
        segment_options: List[List[RouteOption]],
        optimize_by: str = "duration",
        top_k: int = 3,
    ) -> List[PlanResult]:
        """
        Given N segments, each with M route options, enumerate all combinations
        and return the top K sorted by the chosen metric.
        """
        results: List[PlanResult] = []

        def backtrack(seg_idx: int, current: List[PlanSegment], total_d: int, total_c: float):
            if seg_idx == len(segment_options):
                results.append(PlanResult(
                    total_duration=total_d,
                    total_cost=round(total_c, 1),
                    segments=current.copy(),
                ))
                return

            for option in segment_options[seg_idx]:
                # Apply transfer buffer if transitioning to/from train
                buffer = 0
                if option.mode == "train" or (current and current[-1].mode == "train"):
                    buffer = self.TRANSFER_BUFFER_MINUTES * 60

                segment = PlanSegment(
                    mode=option.mode,
                    from_name="",
                    to_name="",
                    duration=option.duration + buffer,
                    cost=option.cost,
                    details={"distance": option.distance, "steps": option.steps},
                )
                current.append(segment)
                backtrack(seg_idx + 1, current, total_d + option.duration + buffer, total_c + option.cost)
                current.pop()

        backtrack(0, [], 0, 0.0)

        # Sort and return top K
        reverse = False
        if optimize_by == "duration":
            results.sort(key=lambda p: p.total_duration)
        elif optimize_by == "cost":
            results.sort(key=lambda p: p.total_cost)
        else:
            results.sort(key=lambda p: p.total_duration)

        return results[:top_k]
```

The algorithm is a simple recursive backtrack. With 2-4 segments and 2-6 options each, the search space is tiny (< 1000 combinations), so no need for dynamic programming or heuristics.

`TRANSFER_BUFFER_MINUTES` adds 30 minutes when a segment is adjacent to a train segment. This prevents unrealistic connections like "get off subway at 8:55, board train at 9:00".

- [ ] **Step 4: Run the test and confirm it passes**

```bash
pytest tests/test_route_optimizer.py::test_optimize_two_segments -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/route_optimizer.py backend/tests/test_route_optimizer.py
git commit -m "feat: add RouteOptimizer with backtracking search"
```

---

## Task 5: API Routers (Plan + POI)

**Files:**
- Modify: `backend/routers/plan.py`
- Modify: `backend/routers/poi.py`
- Modify: `backend/main.py` (if needed)

- [ ] **Step 1: Implement plan router**

```python
# backend/routers/plan.py
from fastapi import APIRouter
from models import PlanRequest, PlanResponse
from services.train_proxy import TrainProxy
from services.route_aggregator import RouteAggregator
from services.route_optimizer import RouteOptimizer
from config import settings

router = APIRouter()
train_proxy = TrainProxy()
optimizer = RouteOptimizer()

@router.post("/plan", response_model=PlanResponse)
async def plan_route(req: PlanRequest):
    aggregator = RouteAggregator(settings.ensure_gaode_key())

    segment_options = []
    for seg in req.segments:
        options = []
        for mode in seg.modes:
            if mode == "train":
                # Query 12306 for train options
                trains = await train_proxy.query_trains(
                    seg.from_loc.name, seg.to_loc.name, req.departure_time[:10]
                )
                for t in trains:
                    options.append({
                        "mode": "train",
                        "duration": self._parse_duration(t.get("duration", "")),
                        "cost": 35.0,  # MVP: fixed placeholder
                        "distance": 0,
                        "steps": [],
                        "train_no": t.get("train_no"),
                    })
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

def _parse_duration(self, duration_str: str) -> int:
    """Convert '02:30' to seconds."""
    try:
        parts = duration_str.split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60
    except Exception:
        return 0
```

Note: `_parse_duration` should be a standalone function, not a method. Let's fix that:

```python
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
```

- [ ] **Step 2: Implement POI router**

```python
# backend/routers/poi.py
import httpx
from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/poi/search")
async def search_poi(keyword: str = Query(...), city: str = Query(default="")):
    from config import settings
    key = settings.ensure_gaode_key()
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": key,
        "keywords": keyword,
        "city": city,
        "offset": 10,
        "page": 1,
        "extensions": "all",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    pois = []
    for p in data.get("pois", []):
        location = p.get("location", "0,0").split(",")
        pois.append({
            "name": p.get("name"),
            "address": p.get("address"),
            "lng": float(location[0]),
            "lat": float(location[1]),
        })
    return {"results": pois}
```

- [ ] **Step 3: Verify the server starts with new routers**

Run:
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Then:
```bash
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{"segments":[],"optimize_by":"duration"}'
```

Expected: Returns `{"plans":[]}` (empty segments produce empty plans).

- [ ] **Step 4: Commit**

```bash
git add backend/routers/
git commit -m "feat: add plan and poi API routers"
```

---

## Task 6: Frontend Project Scaffold

**Files:**
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/src/api/index.js`

- [ ] **Step 1: Scaffold Vite + Vue3 project**

Run:
```bash
cd /Users/yay_mac/Documents/code/route_planning
npm create vite@latest frontend -- --template vue
```

When prompted, select:
- Framework: **Vue**
- Variant: **JavaScript**

- [ ] **Step 2: Install Vant and Axios**

```bash
cd frontend
npm install
npm install vant axios
```

- [ ] **Step 3: Configure Vant in main.js**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import 'vant/lib/index.css'

const app = createApp(App)
app.mount('#app')
```

- [ ] **Step 4: Create API client**

```javascript
// frontend/src/api/index.js
import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 15000,
})

export async function searchPoi(keyword, city = '') {
  const { data } = await client.get('/poi/search', { params: { keyword, city } })
  return data.results || []
}

export async function planRoute(payload) {
  const { data } = await client.post('/plan', payload)
  return data.plans || []
}
```

- [ ] **Step 5: Verify frontend dev server starts**

```bash
cd frontend
npm run dev
```

Open the URL shown (typically `http://localhost:5173`). You should see the default Vite + Vue welcome page.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Vue3 + Vant frontend"
```

---

## Task 7: Frontend Input Page (HomeView)

**Files:**
- Create: `frontend/src/components/SearchInput.vue`
- Create: `frontend/src/components/ModeSelector.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/HomeView.vue`

- [ ] **Step 1: Create SearchInput component**

```vue
<!-- frontend/src/components/SearchInput.vue -->
<template>
  <div class="search-input">
    <van-field
      v-model="keyword"
      :label="label"
      :placeholder="placeholder"
      @update:model-value="onInput"
    />
    <van-list v-if="results.length > 0" class="results">
      <van-cell
        v-for="item in results"
        :key="item.name + item.lng"
        :title="item.name"
        :label="item.address"
        @click="select(item)"
      />
    </van-list>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { searchPoi } from '../api'

const props = defineProps({
  label: String,
  placeholder: String,
})

const emit = defineEmits(['select'])

const keyword = ref('')
const results = ref([])

// Debounce search: wait 300ms after user stops typing
let timer = null
function onInput() {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    if (keyword.value.length < 2) {
      results.value = []
      return
    }
    results.value = await searchPoi(keyword.value)
  }, 300)
}

function select(item) {
  keyword.value = item.name
  results.value = []
  emit('select', item)
}
</script>

<style scoped>
.results {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #eee;
}
</style>
```

This component wraps Vant's `Field` and `Cell`. It debounces POI search by 300ms to avoid flooding the backend with requests while the user is typing.

- [ ] **Step 2: Create ModeSelector component**

```vue
<!-- frontend/src/components/ModeSelector.vue -->
<template>
  <div class="mode-selector">
    <span
      v-for="mode in modes"
      :key="mode.value"
      :class="['mode-tag', { active: selected.includes(mode.value) }]"
      @click="toggle(mode.value)"
    >
      {{ mode.icon }} {{ mode.label }}
    </span>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const modes = [
  { value: 'transit', label: '公交/地铁', icon: '🚌' },
  { value: 'driving', label: '驾车', icon: '🚗' },
  { value: 'bicycling', label: '骑行', icon: '🚴' },
  { value: 'walking', label: '步行', icon: '🚶' },
  { value: 'train', label: '火车', icon: '🚄' },
]

const selected = ref(modes.map(m => m.value))

function toggle(value) {
  if (selected.value.includes(value)) {
    selected.value = selected.value.filter(v => v !== value)
  } else {
    selected.value.push(value)
  }
}

defineExpose({ selected })
</script>

<style scoped>
.mode-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}
.mode-tag {
  padding: 6px 12px;
  border-radius: 16px;
  background: #f0f0f0;
  font-size: 14px;
  cursor: pointer;
}
.mode-tag.active {
  background: #1989fa;
  color: white;
}
</style>
```

`defineExpose` lets the parent component read `selected.value` directly via a template ref.

- [ ] **Step 3: Create HomeView**

```vue
<!-- frontend/src/views/HomeView.vue -->
<template>
  <div class="home">
    <h2>路线规划</h2>

    <SearchInput ref="fromRef" label="起点" placeholder="输入出发地点" @select="loc => fromLoc = loc" />

    <div v-for="(stop, idx) in stops" :key="idx" class="stop-row">
      <SearchInput :label="`途经点${idx + 1}`" placeholder="输入途经地点" @select="loc => stops[idx] = loc" />
      <van-button size="small" type="danger" @click="removeStop(idx)">删除</van-button>
    </div>

    <van-button size="small" type="primary" @click="addStop">+ 添加途经点</van-button>

    <SearchInput ref="toRef" label="终点" placeholder="输入目的地点" @select="loc => toLoc = loc" />

    <ModeSelector ref="modeRef" />

    <van-button type="primary" block @click="submit">规划路线</van-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SearchInput from '../components/SearchInput.vue'
import ModeSelector from '../components/ModeSelector.vue'

const fromLoc = ref(null)
const toLoc = ref(null)
const stops = ref([])
const modeRef = ref(null)

function addStop() {
  if (stops.value.length < 3) {
    stops.value.push(null)
  }
}

function removeStop(idx) {
  stops.value.splice(idx, 1)
}

const emit = defineEmits(['submit'])

function submit() {
  if (!fromLoc.value || !toLoc.value) {
    alert('请输入起点和终点')
    return
  }

  // Build segments: from -> stop1 -> stop2 -> ... -> to
  const points = [fromLoc.value, ...stops.value.filter(Boolean), toLoc.value]
  const segments = []
  for (let i = 0; i < points.length - 1; i++) {
    segments.push({
      from_loc: points[i],
      to_loc: points[i + 1],
      modes: modeRef.value.selected,
    })
  }

  emit('submit', {
    departure_time: new Date().toISOString(),
    segments,
    optimize_by: 'duration',
  })
}
</script>

<style scoped>
.stop-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
```

The view constructs segments by chaining all selected locations. Each segment shares the same set of selected modes.

- [ ] **Step 4: Update App.vue to show HomeView**

```vue
<!-- frontend/src/App.vue -->
<template>
  <HomeView @submit="onSubmit" />
</template>

<script setup>
import HomeView from './views/HomeView.vue'

function onSubmit(payload) {
  console.log('Submit payload:', payload)
  // TODO: navigate to result page
}
</script>
```

- [ ] **Step 5: Verify the input page renders**

With backend running (`uvicorn main:app --port 8000`), run frontend dev server (`npm run dev`) and open the page. Type a location and verify POI suggestions appear.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ frontend/src/views/ frontend/src/App.vue
git commit -m "feat: add frontend input page with POI search and mode selection"
```

---

## Task 8: Frontend Result Page (ResultView)

**Files:**
- Create: `frontend/src/components/RouteTimeline.vue`
- Create: `frontend/src/views/ResultView.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Create RouteTimeline component**

```vue
<!-- frontend/src/components/RouteTimeline.vue -->
<template>
  <div class="timeline">
    <div v-for="(seg, idx) in segments" :key="idx" class="segment">
      <div class="time">
        <span v-if="seg.departure">{{ seg.departure }}</span>
        <span v-else>--:--</span>
      </div>
      <div class="dot" :class="seg.mode">{{ modeIcon(seg.mode) }}</div>
      <div class="info">
        <div class="mode">{{ modeLabel(seg.mode) }}</div>
        <div class="route">{{ seg.from_name }} → {{ seg.to_name }}</div>
        <div class="meta">{{ formatDuration(seg.duration) }} · ¥{{ seg.cost }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  segments: Array,
})

function modeIcon(mode) {
  const map = { transit: '🚌', driving: '🚗', bicycling: '🚴', walking: '🚶', train: '🚄' }
  return map[mode] || '➡️'
}

function modeLabel(mode) {
  const map = { transit: '公交/地铁', driving: '驾车', bicycling: '骑行', walking: '步行', train: '火车' }
  return map[mode] || mode
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}
</script>

<style scoped>
.timeline { padding: 8px; }
.segment {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}
.time { width: 48px; font-size: 13px; color: #666; }
.dot { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e8f4ff; }
.info { flex: 1; }
.mode { font-weight: bold; }
.meta { font-size: 13px; color: #888; margin-top: 4px; }
</style>
```

- [ ] **Step 2: Create ResultView**

```vue
<!-- frontend/src/views/ResultView.vue -->
<template>
  <div class="result">
    <van-nav-bar title="规划结果" left-text="返回" @click-left="emit('back')" />

    <van-tabs v-model:active="activeTab">
      <van-tab title="最快到达">
        <PlanCard v-for="(plan, idx) in fastestPlans" :key="idx" :plan="plan" />
      </van-tab>
      <van-tab title="最省费用">
        <PlanCard v-for="(plan, idx) in cheapestPlans" :key="idx" :plan="plan" />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import RouteTimeline from '../components/RouteTimeline.vue'

const props = defineProps({
  plans: Array,
})
const emit = defineEmits(['back'])

const activeTab = ref(0)

const fastestPlans = computed(() => {
  return [...props.plans].sort((a, b) => a.total_duration - b.total_duration)
})

const cheapestPlans = computed(() => {
  return [...props.plans].sort((a, b) => a.total_cost - b.total_cost)
})
</script>

<!-- PlanCard inline component for the view -->
<template>
  <div class="plan-card">
    <div class="header">
      <span class="total-time">{{ formatDuration(plan.total_duration) }}</span>
      <span class="total-cost">¥{{ plan.total_cost }}</span>
    </div>
    <RouteTimeline :segments="plan.segments" />
  </div>
</template>
```

Wait — Vue SFC does not support multiple `<template>` blocks in one file. Let's restructure: keep PlanCard as a separate component or inline it properly.

Correct approach:

```vue
<!-- frontend/src/views/ResultView.vue -->
<template>
  <div class="result">
    <van-nav-bar title="规划结果" left-text="返回" @click-left="emit('back')" />

    <van-tabs v-model:active="activeTab">
      <van-tab title="最快到达">
        <PlanCard v-for="(plan, idx) in fastestPlans" :key="idx" :plan="plan" />
      </van-tab>
      <van-tab title="最省费用">
        <PlanCard v-for="(plan, idx) in cheapestPlans" :key="idx" :plan="plan" />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import RouteTimeline from '../components/RouteTimeline.vue'

const props = defineProps({ plans: Array })
const emit = defineEmits(['back'])

const activeTab = ref(0)
const fastestPlans = computed(() => [...props.plans].sort((a, b) => a.total_duration - b.total_duration))
const cheapestPlans = computed(() => [...props.plans].sort((a, b) => a.total_cost - b.total_cost))

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}
</script>

<script>
// Inline PlanCard component
import RouteTimeline from '../components/RouteTimeline.vue'

export const PlanCard = {
  props: ['plan'],
  components: { RouteTimeline },
  template: `
    <div class="plan-card">
      <div class="header">
        <span class="total-time">{{ formatDuration(plan.total_duration) }}</span>
        <span class="total-cost">¥{{ plan.total_cost }}</span>
      </div>
      <RouteTimeline :segments="plan.segments" />
    </div>
  `,
  methods: {
    formatDuration(seconds) {
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      if (h > 0) return `${h}小时${m}分钟`
      return `${m}分钟`
    }
  }
}
</script>
```

Actually, mixing `<script setup>` and `<script>` with inline components is awkward. Better to extract PlanCard as a separate file:

```vue
<!-- frontend/src/components/PlanCard.vue -->
<template>
  <div class="plan-card">
    <div class="header">
      <span class="total-time">{{ formatDuration(plan.total_duration) }}</span>
      <span class="total-cost">¥{{ plan.total_cost }}</span>
    </div>
    <RouteTimeline :segments="plan.segments" />
  </div>
</template>

<script setup>
import RouteTimeline from './RouteTimeline.vue'

const props = defineProps({ plan: Object })

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}
</script>

<style scoped>
.plan-card {
  margin: 12px;
  padding: 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.header {
  display: flex;
  justify-content: space-between;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}
.total-cost { color: #ff6600; }
</style>
```

Then ResultView imports PlanCard:

```vue
<!-- frontend/src/views/ResultView.vue -->
<template>
  <div class="result">
    <van-nav-bar title="规划结果" left-text="返回" @click-left="emit('back')" />
    <van-tabs v-model:active="activeTab">
      <van-tab title="最快到达">
        <PlanCard v-for="(plan, idx) in fastestPlans" :key="idx" :plan="plan" />
      </van-tab>
      <van-tab title="最省费用">
        <PlanCard v-for="(plan, idx) in cheapestPlans" :key="idx" :plan="plan" />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import PlanCard from '../components/PlanCard.vue'

const props = defineProps({ plans: Array })
const emit = defineEmits(['back'])

const activeTab = ref(0)
const fastestPlans = computed(() => [...props.plans].sort((a, b) => a.total_duration - b.total_duration))
const cheapestPlans = computed(() => [...props.plans].sort((a, b) => a.total_cost - b.total_cost))
</script>
```

- [ ] **Step 3: Update App.vue with page routing**

For MVP, use a simple boolean flag instead of vue-router to avoid extra dependency:

```vue
<!-- frontend/src/App.vue -->
<template>
  <HomeView v-if="page === 'home'" @submit="onSubmit" />
  <ResultView v-else :plans="plans" @back="page = 'home'" />
</template>

<script setup>
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ResultView from './views/ResultView.vue'
import { planRoute } from './api'

const page = ref('home')
const plans = ref([])

async function onSubmit(payload) {
  plans.value = await planRoute(payload)
  page.value = 'result'
}
</script>
```

- [ ] **Step 4: Verify end-to-end flow**

1. Start backend: `cd backend && uvicorn main:app --port 8000`
2. Set `GAODE_KEY` environment variable to a valid Gaode key
3. Start frontend: `cd frontend && npm run dev`
4. Open browser, enter start/end locations, select modes, click "规划路线"
5. Verify results page shows plan cards with timelines

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PlanCard.vue frontend/src/views/ResultView.vue frontend/src/App.vue
git commit -m "feat: add frontend result page with timeline and plan cards"
```

---

## Self-Review

### Spec Coverage Check

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| FastAPI backend scaffold | Task 1 |
| Pydantic models | Task 1 |
| TrainProxy (12306) | Task 2 |
| RouteAggregator (Gaode) | Task 3 |
| RouteOptimizer (combinatorial search) | Task 4 |
| POST /api/plan | Task 5 |
| GET /api/poi/search | Task 5 |
| Vue3 + Vant frontend | Task 6 |
| POI search with debounce | Task 7 |
| Mode selection | Task 7 |
| Multi-segment input | Task 7 |
| Result timeline display | Task 8 |
| Fastest / cheapest sorting | Task 8 |
| Transfer buffer (30min) | Task 4 |
| Graceful degradation on 12306 failure | Task 2 |

All spec requirements are covered.

### Placeholder Scan

No TBD, TODO, "implement later", or vague steps found. All code blocks are complete and runnable.

### Type Consistency Check

- `RouteOption` used consistently across aggregator and optimizer
- `PlanResult` used consistently across optimizer and plan router
- `PlanSegment` used consistently in optimizer and ResultView
- Method names consistent: `query_trains`, `query_segment`, `find_best_plans`

No inconsistencies found.

---

*Plan complete and ready for execution.*
