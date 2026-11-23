"""Open-Meteo 地理編碼與天氣資料。"""
from .common import UpstreamError, get_json

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CODES = {
    0: "晴朗", 1: "大致晴朗", 2: "局部多雲", 3: "陰天", 45: "有霧", 48: "霧凇",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨", 61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪", 80: "陣雨", 81: "陣雨", 82: "強陣雨",
    95: "雷雨", 96: "雷雨伴隨冰雹", 99: "雷雨伴隨冰雹",
}


class WeatherError(Exception):
    pass


def search_places(city):
    """搜尋最多五筆同名城市，供使用者挑選。"""
    try:
        data = get_json(GEOCODING_URL, params={"name": city, "count": 5, "language": "zh", "format": "json"}, cache_seconds=3600)
    except UpstreamError as exc:
        raise WeatherError(str(exc)) from exc
    return data.get("results", [])


def get_weather(city=None, place=None):
    """以城市名稱或已選地點座標取得目前天氣及七日預報。"""
    if place is None:
        places = search_places(city or "")
        if not places:
            raise WeatherError("找不到這個城市，請試試英文名稱或其他拼法。")
        place = places[0]
    try:
        data = get_json(FORECAST_URL, params={
            "latitude": place["latitude"], "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min", "timezone": "auto",
        }, cache_seconds=600)
    except (UpstreamError, KeyError, TypeError) as exc:
        raise WeatherError(str(exc) if isinstance(exc, UpstreamError) else "天氣資料格式暫時無法讀取。") from exc
    current, daily = data.get("current", {}), data.get("daily", {})
    days = daily.get("time", [])
    return {
        "place": place.get("name", city or ""), "country": place.get("country", ""),
        "admin1": place.get("admin1", ""), "latitude": place.get("latitude"),
        "longitude": place.get("longitude"), "timezone": data.get("timezone", ""),
        "temperature": current.get("temperature_2m"), "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"), "wind": current.get("wind_speed_10m"),
        "condition": WEATHER_CODES.get(current.get("weather_code"), "天氣資訊"),
        "forecast": [{"date": day, "high": (daily.get("temperature_2m_max") or [])[i],
                      "low": (daily.get("temperature_2m_min") or [])[i]}
                     for i, day in enumerate(days) if i < len(daily.get("temperature_2m_max", [])) and i < len(daily.get("temperature_2m_min", []))],
    }
