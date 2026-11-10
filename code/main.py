#Imports
import sys
import time
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

#Local Imports
from timeNumerizer import TimeNumerizer
from data_reader import DataReader
from velocityNumerizer import velocityNumerizer
from location_check import LocationChecker


things_to_flag = ["hour_of_day", "days_since_last_login", "flag_device", "failed_attempts", "speed_mph"]

def isolationForest(logins):
    X = StandardScaler().fit_transform(logins[things_to_flag])
    model = IsolationForest(contamination = "auto", random_state = 42)
    return (model.fit_predict(X) == -1).astype(int)

def cleanLocation(location):
    name = ""
    for letter in location:
        if letter.isupper() and len(name) > 0 and name[-1].islower():
            name = name + " "
        name = name + letter
    return name.replace("_", ", ")

def findAnomalies(
    file_path: str
):
    
    #seperate by user
    df = DataReader.read(file_path)

    df["hour_of_day"] = df["timestamp"].dt.hour

    df = df.sort_values(["user_id", "timestamp"])
    df["days_since_last_login"] = df.groupby("user_id")["timestamp"].diff().dt.total_seconds() / 86400
    df["days_since_last_login"] = df["days_since_last_login"].fillna(0)

    flag_device_if = "Tor|Automated|Unknown"
    df["flag_device"] = df["device_type"].str.contains(flag_device_if).astype(int)

    userDict = {}
    users = list(df["user_id"])
    index = df.to_dict("records")
    
    geolocator = Nominatim(user_agent = "sentinelml", timeout = 10)
    userTables = []
    
    for i in range(len(users)):
        # print(df["user_id"])
        if users[i] in userDict:
            userDict[users[i]].append(index[i])
        else:
            userDict[users[i]] = [index[i]]

    #run isolation forest by user
    for userProf in userDict:
        for userEntry in userDict[userProf]:
            # print(userEntry["timestamp"])
            userEntry["numerizedDate"] = TimeNumerizer.date_to_num(str(userEntry["timestamp"]))
            userEntry["numerizedTime"] = TimeNumerizer.time_to_num(str(userEntry["timestamp"]))
            userEntry["location"] = cleanLocation(userEntry["location"])
            
        velocity = velocityNumerizer.detect_impossible_travel(userDict[userProf], geolocator = geolocator)
        userTables.append(velocity)
        time.sleep(1)

    df = pd.concat(userTables, ignore_index = True)
    df["speed_mph"] = df["speed_mph"].clip(upper = 1000)

    # isolation forest on everyone
    df["flagged"] = isolationForest(df)

    # isolation forest by user but only if they have a certain amount of logins
    for userProf in userDict:
        if len(userDict[userProf]) >= 10:
            rows = df["user_id"] == userProf
            df.loc[rows, "flagged"] = isolationForest(df[rows])

        #what category got each login flagged
    rows = df.to_dict("records")
    categories = []
    for row in rows:
        found = []
        if row["hour_of_day"] < 6:
            found.append("Off-hours")
        if row["flag_device"] == 1:
            found.append("Risky device")
        if row["failed_attempts"] > 0:
            found.append("Failed attempts")
        if row["impossible_travel_anomaly"]:
            found.append("Impossible travel")
        if len(found) == 0:
            found.append("Unusual pattern")
        categories.append(", ".join(found))
    df["category"] = categories

    return df


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "sample_data.json"

    results = findAnomalies(file_path)

    flagged = results[results["flagged"] == 1]
    print(flagged[["user_id", "timestamp", "location", "device_type", "speed_mph"]])

    if "is_anomaly" in results.columns:
        print("Precision:", precision_score(results["is_anomaly"], results["flagged"]))
        print("Recall:", recall_score(results["is_anomaly"], results["flagged"]))

    results.to_csv("results.csv", index = False)


#Create a databse to go off of using pandas
# >>> TODO:
# - make logins able to read from whatever filetype is provided instead of hardcoding cases

# #hardcoded case
# logins = [
#     {"hour_of_day": "08:12", "user_id": "user_1042", "location": "Dallas", "device_type": "Desktop", "failed_attempts": 0},
#     {"hour_of_day": "08:47", "user_id": "user_2087", "location": "Austin", "device_type": "Mobile", "failed_attempts": 0},
#     {"hour_of_day": "09:03", "user_id": "user_1042", "location": "Dallas", "device_type": "Desktop", "failed_attempts": 5},
#     {"hour_of_day": "09:04", "user_id": "user_1042", "location": "Dallas", "device_type": "Desktop", "failed_attempts": 1}
# ]

# #read from data file example
# df = DataReader.read("sample_data.json")
# print(df)

# #add hour_of_day
# df["hour_of_day"] = df["timestamp"].dt.hour

# #time since last login in days
# df = df.sort_values(["user_id", "timestamp"])
# df["days_since_last_login"] = df.groupby("user_id")["timestamp"].diff().dt.total_seconds() / 86400
# df["days_since_last_login"] = df["days_since_last_login"].fillna(0)

# #flag devices
# flag_device_if = "Tor|Automated|Unknown"
# df["flag_device"] = df["device_type"].str.contains(flag_device_if).astype(int)

# print(df[["user_id", "timestamp", "hour_of_day", "days_since_last_login", "flag_device"]])

# #numerizes hour_of_day to minutes for data to work
# # >>> TODO:
# # - numerize time with library
# # - numerize
# # for i in range(len(logins)):
# #     timeString = logins[i]["hour_of_day"].split(":")
# #     logins[i]["hour_of_day"] = int(timeString[0]) * 60 + int(timeString[1])

# Ex = "2026-10-27T15:00:00"
# print(TimeNumerizer.date_to_num(Ex), TimeNumerizer.time_to_num(Ex))

# Locatio-Numeration: check whether coordinates are within the configured area
# location_checker = LocationChecker.from_config({
#     "name": "Dallas", "lat": 32.7767, "lon": -96.7970, "radius_km": 40,
# })
# print(location_checker.check_data({"lat": 32.9126, "lon": -96.6389}))

#prototype anomaly detection program
# print(df)
# print(df["failed_attempts"].max())

# print(df["failed_attempts"] > 4)
# df["anomalies"] = df["failed_attempts"] > 4
# print(df)


# anomaly detection with isolation forest
# >>> NOTES:
# - double brackets because IsolationForest returns a dataframe 2D
# - only sees failed_attempts
# - random_state=0 makes the seed set for now (aka, it will always return the same thing which is not necessarily wanted)
# - [-1] is an anomalie, otherwise it becomes [1]
# >>> TODO:
# - numerize values so they can be put through isolation forest
# - create a frontend to display data
# - *split analysis by user (aka: do IsolationForest for user_1042 then user_2087) < IMPORTANT