from dataclasses import dataclass
from typing import Callable, Optional, Tuple


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class Units:
    temp: str

    def __post_init__(self):
        allowed_temp = ("C", "F")
        if self.temp not in allowed_temp:
            raise ValueError(f"Temperature units must be one of {allowed_temp}.")


@dataclass(frozen=True)
class APIConfig:
    lang: str
    key: str


@dataclass(frozen=True)
class Place:
    name: str
    query: Optional[str] = None
    city_id: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

    def __post_init__(self):
        modes = [
            self.query is not None,
            self.city_id is not None,
            self.lat is not None or self.lon is not None
        ]

        if sum(modes) != 1:
            raise ValueError("Place must specify exactly one of query, city_id or coordinates")

        if modes[2] and (self.lat is None or self.lon is None):
            raise ValueError("Both lat and lon required")


@dataclass(frozen=True)
class Weather:
    temp: float
    weather: str

    def convert(self, units: Units):
        if units.temp == "F": temp = 1.8 * self.temp - 459.67
        else:                 temp = self.temp - 273.15

        return Weather(temp, self.weather)


Provider = Callable[[Place, APIConfig], Weather]


@dataclass(frozen=True)
class Config:
    provider: Provider
    api: APIConfig
    places: Tuple[Place]
    units: Units
    formats: Formats
    max_name_len: int = 0

    def __post_init__(self):
        max_len = max(len(place.name) for place in self.places)
        object.__setattr__(self, "max_name_len", max_len)
