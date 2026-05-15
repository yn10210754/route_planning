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
        if optimize_by == "duration":
            results.sort(key=lambda p: p.total_duration)
        elif optimize_by == "cost":
            results.sort(key=lambda p: p.total_cost)
        else:
            results.sort(key=lambda p: p.total_duration)

        return results[:top_k]
