import urllib.request
import urllib.parse
import json

from .models import Weather, Place, APIConfig
from .registry import register_provider


@register_provider("test")
def fetch_weather_test(place: Place, config: APIConfig) -> Weather:
    return Weather(temp=280, wind_speed=1, pressure=100000, weather="Test")


@register_provider("openweather")
def fetch_weather_openweather(place: Place, config: APIConfig) -> Weather:
    base = "http://api.openweathermap.org/data/2.5/weather"

    params: dict[str, object] = {
        'APPID': config.key,
        'lang': config.lang
    }

    if place.query is not None:
        params['q'] = place.query
    elif place.city_id is not None:
        params['id'] = place.city_id
    else:
        params['lat'] = place.lat; params['lon'] = place.lon

    query = urllib.parse.urlencode(params)
    url = base + "?" + query
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode())

    temp = data["main"]["temp"]
    wind_sp = data["wind"]["speed"]
    press = data["main"]["pressure"] * 100
    weath = data["weather"][0]["description"]
    return Weather(temp=temp, wind_speed=wind_sp, pressure=press, weather=weath)


@register_provider("wttr")
def fetch_weather_wttr(place: Place, config: APIConfig) -> Weather:
    base = "https://wttr.in"

    if place.query is not None:
        location = place.query.replace(" ", "+")
    elif place.city_id is not None:
        location = str(place.city_id)
    else:
        location = f"{place.lat:.4f},{place.lon:.4f}"

    long_params = {"format": "j2", "lang": config.lang}

    short_params = "M"

    url = f"{base}/{location}?{short_params}&{urllib.parse.urlencode(long_params)}"

    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode())

    cond = data['data']["current_condition"][0]

    temp = float(cond["temp_C"]) + 273.15
    wind_sp = float(cond["windspeedKmph"]) / 3.6
    press = int(cond["pressure"]) * 100
    weath = cond["weatherDesc"][0]["value"]

    return Weather(temp=temp, wind_speed=wind_sp, pressure=press, weather=weath)
