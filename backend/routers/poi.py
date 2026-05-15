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
