#Imports
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

#Local Imports
from timeNumerizer import TimeNumerizer

#Create a databse to go off of using pandas
# >>> TODO:
# - make logins able to read from whatever filetype is provided instead of hardcoding cases

logins = [
    {"hour_of_day": "08:12", "user_id": "user_1042", "location": "Dallas", "device_type": "Desktop", "failed_attempts": 0},
    {"hour_of_day": "08:47", "user_id": "user_2087", "location": "Austin", "device_type": "Mobile", "failed_attempts": 0},
    {"hour_of_day": "09:03", "user_id": "user_1042", "location": "Dallas", "device_type": "Desktop", "failed_attempts": 5},
    {"hour_of_day": "09:04", "user_id": "user_1042", "location": "Dallas", "device_type": "Desktop", "failed_attempts": 1}
]

#numerizes hour_of_day to minutes for data to work
# >>> TODO:
# - numerize time with library
# - numerize
# for i in range(len(logins)):
#     timeString = logins[i]["hour_of_day"].split(":")
#     logins[i]["hour_of_day"] = int(timeString[0]) * 60 + int(timeString[1])

Ex = "2026-10-27T14:35:00"
print(TimeNumerizer.date_to_num(Ex), TimeNumerizer.time_to_num(Ex))

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