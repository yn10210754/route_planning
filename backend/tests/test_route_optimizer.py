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
    # Fastest should be driving + train = 3600s (+ 30min buffer for train transition)
    # driving 1800s + train 1800s + buffer 1800s = 5400s
    # transit 3600s + train 1800s + buffer 1800s = 7200s
    assert plans[0].total_duration == 5400
    assert plans[0].total_cost == 85.0
