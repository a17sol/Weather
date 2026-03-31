import datetime
import threading
import sublime
import sublime_plugin
from .models import Formats, APIConfig, Place, Config, Units, Weather


VIEW_KEY = "weather_plugin_tab"
SETTINGS_CALLBACK_TAG = "weather_settings_callback"


def plugin_loaded():
    global settings
    settings = sublime.load_settings("Weather.sublime-settings")
    settings.add_on_change(SETTINGS_CALLBACK_TAG, unpack_settings)
    unpack_settings()

def plugin_unloaded():
    global settings
    settings.clear_on_change(SETTINGS_CALLBACK_TAG)

def unpack_settings():
    global config
    print("unpacking")

    def unpack_places():
        places = []
        raw = settings.get("places", [])
        for item in raw:
            if isinstance(item, str):
                places.append(Place(name=item, query=item))
            elif isinstance(item, dict):
                places.append(
                    Place(
                        name=str(item.get("name")),
                        query=item.get("query"),
                        city_id=item.get("city_id"),
                        lat=item.get("lat"),
                        lon=item.get("lon"),
                    )
                )
        return tuple(places)

    def unpack_api_config():
        return APIConfig(
            lang=settings["lang"],
            key=settings["key"]
        )

    def unpack_provider():
        from .registry import providers
        return providers[settings["provider"]]

    def unpack_formats():
        return Formats(
            timestamp=settings["timestamp_f"],
            header=settings["header_f"],
            loading=settings["loading_f"],
            entry=settings["entry_f"],
            error=settings["error_f"]
        )

    def unpack_units():
        return Units(
            temp=settings["temp_u"],
            speed=settings["speed_u"],
            pressure=settings["pressure_u"]
        )

    config = Config(
        provider=unpack_provider(),
        api=unpack_api_config(),
        places=unpack_places(),
        units=unpack_units(),
        formats=unpack_formats()
    )


class WeatherCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.find_or_create_view()
        view.run_command("weather_render_loading_page")
        for i in range(len(config.places)):
            threading.Thread(target=self.process_place, args=(view, i), daemon=True).start()
        self.window.focus_view(view)

    def process_place(self, view, i):
        place = config.places[i]

        lf_in_header = config.formats.header.count("\n")
        line = i + lf_in_header + 1

        try:
            weather = fetch_weather(place).convert(config.units)
            new_entry = config.formats.entry.format(
                name=place.name, max_name_len=config.max_name_len, **weather
            )

        except BaseException as e:
            new_entry = config.formats.error.format(
                name=place.name, error=str(e), max_name_len=config.max_name_len
            )

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
        timestamp = datetime.datetime.now().strftime(config.formats.timestamp)
        separator = '—'*len(timestamp)
        page = config.formats.header.format(timestamp=timestamp, separator=separator)

        for place in config.places:
            page = page + "\n" + config.formats.loading.format(
                name=place.name, max_name_len=config.max_name_len
            )

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
    return config.provider(place, config.api)
