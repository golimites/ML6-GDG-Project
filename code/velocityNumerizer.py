from datetime import datetime

import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim


#Class to numerize time and date for anomaly detection
class velocityNumerizer:
    @staticmethod
    def detect_impossible_travel(
        logins: list[dict[str, str]],
        speed_threshold_mph: float = 400.0,
        geolocator: Nominatim | None = None,
    ) -> pd.DataFrame:
        """Return login records annotated with travel speed and anomaly status."""
        df = pd.DataFrame(logins)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        if geolocator is None:
            geolocator = Nominatim(user_agent="login_anomaly_detector")

        location_cache: dict[str, tuple[float, float]] = {}

        def get_coords(loc_name: str) -> tuple[float, float]:
            if loc_name not in location_cache:
                location = geolocator.geocode(loc_name)
                if location is None:
                    raise ValueError(f"Unable to geocode location: {loc_name!r}")
                location_cache[loc_name] = (location.latitude, location.longitude)
            return location_cache[loc_name]

        df["coords"] = df["location"].apply(get_coords)
        df = df.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)

        speeds: list[float] = []
        anomalies: list[bool] = []

        for i in range(len(df)):
            if i == 0 or df.loc[i, "user_id"] != df.loc[i - 1, "user_id"]:
                speeds.append(0.0)
                anomalies.append(False)
                continue

            prev_coords = df.loc[i - 1, "coords"]
            curr_coords = df.loc[i, "coords"]
            prev_time = df.loc[i - 1, "timestamp"]
            curr_time = df.loc[i, "timestamp"]

            distance_miles = geodesic(prev_coords, curr_coords).miles
            time_diff_hours = (curr_time - prev_time).total_seconds() / 3600.0
            if time_diff_hours > 0:
                calculated_speed = distance_miles / time_diff_hours
            else:
                calculated_speed = float("inf") if distance_miles > 0 else 0.0

            speeds.append(round(calculated_speed, 2))
            anomalies.append(calculated_speed > speed_threshold_mph)

        df["speed_mph"] = speeds
        df["impossible_travel_anomaly"] = anomalies
        return df