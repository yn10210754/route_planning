# backend/tests/test_train_proxy.py
import pytest
import respx
from httpx import Response
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

@respx.mock
async def test_query_trains_success(proxy):
    # Mock station JS endpoint
    station_js = "var station_names ='@sz|深圳|SZQ|shenzhen|sz|0@hzb|惠州北|KOQ|huizhoubei|hzb|1';"
    respx.get("https://kyfw.12306.cn/otn/resources/js/framework/station_name.js").mock(
        return_value=Response(200, text=station_js)
    )

    # Mock query endpoint — 12306 returns pipe-delimited strings
    # Format: |status|secret|train_no|...|from|to|depart|arrive|duration|...
    mock_result = "|预订|70000G123401|G1234|||SZQ|KOQ|08:00|08:30|00:30|IS|"
    respx.get("https://kyfw.12306.cn/otn/leftTicket/query").mock(
        return_value=Response(200, json={"data": {"result": [mock_result]}})
    )

    trains = await proxy.query_trains("深圳", "惠州北", "2026-05-10")
    assert len(trains) == 1
    assert trains[0]["train_no"] == "G1234"
    assert trains[0]["departure_time"] == "08:00"
