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
