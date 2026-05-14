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
