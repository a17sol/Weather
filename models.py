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
class APIConfig:
    units: str
    lang: str
    key: str

    def __post_init__(self):
        if self.units not in ("metric", "imperial"):
            raise ValueError("Units must be one of \"metric\", \"imperial\"")


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


Provider = Callable[[Place, APIConfig], Weather]


@dataclass(frozen=True)
class Config:
    provider: Provider
    api: APIConfig
    places: Tuple[Place]
    formats: Formats
    max_name_len: int = 0

    def __post_init__(self):
        max_len = max(len(place.name) for place in self.places)
        object.__setattr__(self, "max_name_len", max_len)
