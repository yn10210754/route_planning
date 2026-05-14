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
