"""
This file is intended for user-defined weather providers.

You can add your own functions here that fetch weather data from any API
or service you like. Each provider must be registered using the
@register_provider decorator and must have the following signature:
(place: Place, config: APIConfig) -> Weather.
The Weather object must contain parameters in basic SI units.

Example provider is shown below. Check also builtin_providers.py
You can add multiple providers in this file if needed. Alternatively, you
can define providers in separate .py files within the plugin directory -
they will be loaded automatically when the plugin starts.
Make sure each provider has a unique name.
"""

# import urllib.request
# import json

# from .registry import register_provider
# from .models import Place, APIConfig, Weather

# @register_provider("my_weather_api")
# def my_weather_provider(place: Place, config: APIConfig) -> Weather:
#     API_URL = f"https://example.com/weather?query={place.query}"

#     with urllib.request.urlopen(API_URL) as response:
#         data = json.load(response)

#     return Weather(
#     	temp=data["temperature"],
#     	humidity=data["humidity"],
#     	wind_speed=data["wind_speed"],
#     	pressure=data["pressure"],
#     	weather=data["description"]
#     )
