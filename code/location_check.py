"""Reusable location check for coordinates within an allowed radius."""

import json
import math

EARTH_RADIUS_KM = 6371.0

# Accepted key names for incoming data, so it plugs into different sources
LAT_KEYS = ("lat", "latitude")
LON_KEYS = ("lon", "lng", "long", "longitude")


def distance_km(lat1, lon1, lat2, lon2):
    """Haversine distance between two lat/lon points, in kilometers."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _pick(data, keys):
    for key in keys:
        if key in data:
            return data[key]
    raise KeyError(f"missing one of {keys}")


class LocationChecker:
    def __init__(self, name, lat, lon, radius_km=40):
        self.name = name
        self.lat = float(lat)
        self.lon = float(lon)
        self.radius_km = float(radius_km)

    @classmethod
    def from_config(cls, config):
        """Create a checker from a dict or JSON configuration string."""
        if isinstance(config, str):
            config = json.loads(config)
        return cls(
            config["name"],
            _pick(config, LAT_KEYS),
            _pick(config, LON_KEYS),
            config.get("radius_km", 40),
        )

    def check(self, lat, lon):
        """Returns 0 if inside the allowed area, 1 otherwise."""
        return self.check_detailed(lat, lon)["code"]

    def check_detailed(self, lat, lon):
        distance = distance_km(float(lat), float(lon), self.lat, self.lon)
        inside = distance <= self.radius_km
        return {
            "code": 0 if inside else 1,
            "allowed": inside,
            "distance_km": round(distance, 2),
            "location": self.name,
            "message": (f"You're in {self.name}. You're good!" if inside
                        else f"You're not in {self.name}."),
        }

    def check_data(self, data):
        """Accept coordinate data as a dict or JSON string; fail closed."""
        try:
            if isinstance(data, str):
                data = json.loads(data)
            lat = _pick(data, LAT_KEYS)
            lon = _pick(data, LON_KEYS)
            return self.check_detailed(lat, lon)
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
            return {
                "code": 1,
                "allowed": False,
                "distance_km": None,
                "location": self.name,
                "message": f"Invalid location data: {error}",
            }


if __name__ == "__main__":
    checker = LocationChecker.from_config({
        "name": "Dallas", "lat": 32.7767, "lon": -96.7970, "radius_km": 40,
    })

    tests = [
        {"lat": 32.9126, "lon": -96.6389},
        {"latitude": 29.7604, "longitude": -95.3698},
        '{"lat": 40.7128, "lng": -74.0060}',
        {"lat": "bad"},
    ]
    for test_data in tests:
        result = checker.check_data(test_data)
        print(result["code"], "-", result["message"])