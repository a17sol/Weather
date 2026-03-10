import datetime
import urllib.request
import urllib.parse
import json
from dataclasses import dataclass
import threading
import sublime
import sublime_plugin


VIEW_KEY = "weather_plugin_tab"
SETTINGS_CALLBACK_TAG = "weather_settings_callback"


providers = {}


@dataclass
class Formats:
    timestamp: str
    header: str
    loading: str
    entry: str
    error: str

    def __post_init__(self):
        if "\n" in self.timestamp:
            raise ValueError("Timestamp format cannot contain \"\\n\"")
        if "\n" in self.loading:
            raise ValueError("Loading format cannot contain \"\\n\"")
        if "\n" in self.entry:
            raise ValueError("Entry format cannot contain \"\\n\"")
        if "\n" in self.error:
            raise ValueError("Error format cannot contain \"\\n\"")


@dataclass
class Weather:
    temp: float
    weather: str

@dataclass
class APIConfig:
    units: str
    lang: str
    key: str

class Place:
    def __init__(self, name, query=None, city_id=None, lat=None, lon=None):
        self.name = name
        self.query = None
        self.city_id = None
        self.lat, self.lon = None, None

        modes = [
            query is not None,
            city_id is not None,
            lat is not None or lon is not None
        ]

        if sum(modes) != 1:
            raise ValueError("Place must specify exactly one of query, city_id or coordinates")

        if modes[0]:
            self.query = str(query)
        elif modes[1]:
            self.city_id = city_id
        elif modes[2]:
            if lat is None or lon is None:
                raise ValueError("Both lat and lon required")

            self.lat = float(lat)
            self.lon = float(lon)


def plugin_loaded():
    global settings
    settings = sublime.load_settings("Weather.sublime-settings")
    print(settings.to_dict())
    settings.add_on_change(SETTINGS_CALLBACK_TAG, unpack_settings)
    unpack_settings()

def plugin_unloaded():
    global settings
    settings.clear_on_change(SETTINGS_CALLBACK_TAG)

def unpack_settings():
    print("unpacking")
    unpack_places()
    unpack_api_config()
    unpack_provider()
    unpack_formats()

def unpack_places():
    global places
    global max_name_len

    places = []
    raw = settings.get("places", [])
    for item in raw:
        if isinstance(item, str):
            places.append(Place(name=item, query=item))
        elif isinstance(item, dict):
            places.append(
                Place(
                    name=item.get("name"),
                    query=item.get("query"),
                    city_id=item.get("city_id"),
                    lat=item.get("lat"),
                    lon=item.get("lon"),
                )
            )

    max_name_len = max(len(place.name) for place in places)

def unpack_api_config():
    global api_config
    api_config = APIConfig(
        units=settings["units"],
        lang=settings["lang"],
        key=settings["key"]
    )

def unpack_provider():
    global provider
    provider = settings["provider"]

def unpack_formats():
    global formats
    formats = Formats(
        timestamp=settings["timestamp_f"],
        header=settings["header_f"],
        loading=settings["loading_f"],
        entry=settings["entry_f"],
        error=settings["error_f"]
    )


class WeatherCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.find_or_create_view()
        view.run_command("weather_render_loading_page")
        for i in range(len(places)):
            threading.Thread(target=self.process_place, args=(view, i), daemon=True).start()
        self.window.focus_view(view)

    def process_place(self, view, i):
        place = places[i]

        lf_in_header = formats.header.count("\n")
        line = i + lf_in_header + 1

        try:
            weather = fetch_weather(place)
            new_entry = formats.entry.format(name=place.name, weather=weather, max_name_len=max_name_len)

        except BaseException as e:
            new_entry = formats.error.format(name=place.name, error=str(e), max_name_len=max_name_len)

        sublime.set_timeout(
            lambda: view.run_command("weather_replace_string", {"number": line, "text": new_entry})
        )


    def find_or_create_view(self):
        for view in self.window.views():
            if view.settings().get(VIEW_KEY):
                return view

        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name("☼ Weather")
        view.settings().set(VIEW_KEY, True)
        view.set_read_only(True)
        return view


class WeatherRenderLoadingPageCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        timestamp = datetime.datetime.now().strftime(formats.timestamp)
        separator = '—'*len(timestamp)
        page = formats.header.format(timestamp=timestamp, separator=separator)

        for place in places:
            page = page + "\n" + formats.loading.format(name=place.name, max_name_len=max_name_len)

        with preserve_readonly(self.view):
            self.view.sel().clear()
            region = sublime.Region(0, self.view.size())
            self.view.replace(edit, region, page)


class WeatherReplaceStringCommand(sublime_plugin.TextCommand):
    def run(self, edit, number, text):
        pt = self.view.text_point(number, 0)
        region = self.view.line(pt)

        with preserve_readonly(self.view):
            self.view.replace(edit, region, text)


class preserve_readonly:
    def __init__(self, view):
        self.view = view
        self.was_read_only = view.is_read_only()

    def __enter__(self):
        self.view.set_read_only(False)
        return self.view

    def __exit__(self, type, value, traceback):
        self.view.set_read_only(self.was_read_only)


def fetch_weather(place):
    return providers[provider](place, api_config)


def register_provider(name):
    def decorator(func):
        providers[name] = func
        return func
    return decorator


@register_provider("test")
def fetch_weather_test(place, config):
    return Weather(temp=12.3, weather="Test")


@register_provider("openweather")
def fetch_weather_openweather(place, config):
    base = "http://api.openweathermap.org/data/2.5/weather"

    params = {'APPID': config.key, 'units': config.units, 'lang': config.lang}
    if place.query is not None:
        params['q'] = place.query
    elif place.city_id is not None:
        params['id'] = place.city_id
    elif place.lat is not None and place.lon is not None:
        params['lat'] = place.lat; params['lon'] = place.lon
    else:
        raise RuntimeError("Invalid Place object")

    query = urllib.parse.urlencode(params)
    url = base + "?" + query
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode())

    temp, weath = data["main"]["temp"], data["weather"][0]["description"]
    return Weather(temp=temp, weather=weath)


def fetch_weather_wttr(city, config):

    base = "https://wttr.in"
    params = {"format": "j2"}
    # tmp = city.replace(" ", "+")
    url = f"https://wttr.in/{tmp}?format=j2"
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode())
    temp = data["current_condition"][0]["temp_C"]
    weath = data["current_condition"][0]["weatherDesc"][0]["value"]
    return Weather(temp=float(temp), weather=weath)


@register_provider("wttr")
def fetch_weather_wttr(place: Place, config: APIConfig) -> Weather:
    base = "https://wttr.in"

    if place.query is not None:
        location = place.query.replace(" ", "+")
    elif place.city_id is not None:
        location = str(place.city_id)
    elif place.lat is not None and place.lon is not None:
        location = f"{place.lat},{place.lon}"
    else:
        raise ValueError("Invalid place configuration")

    params = {"format": "j1", "lang": config.lang}

    if config.units == "metric":
        params["m"] = ""
    elif config.units == "imperial":
        params["u"] = ""

    url = f"{base}/{location}?{urllib.parse.urlencode(params)}"
    print(url)
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode())


    cond = data["current_condition"][0]

    if config.units == "imperial":
        temp = float(cond["temp_F"])
    elif config.units =="metric":
        temp = float(cond["temp_C"])

    weather = cond["weatherDesc"][0]["value"]

    return Weather(temp=temp, weather=weather)
