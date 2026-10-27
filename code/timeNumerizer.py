from datetime import datetime

#Class to numerize time and date for anomaly detection
class TimeNumerizer:
    @staticmethod
    def date_to_num(timestamp):
        time = datetime.fromisoformat(timestamp)
        date_value = int(time.strftime("%Y%m%d"))  # 20261027
        return date_value

    @staticmethod
    def time_to_num(timestamp):
        time = datetime.fromisoformat(timestamp)
        time_value = int(time.strftime("%H%M"))    # 1435
        return time_value