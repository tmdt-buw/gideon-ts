import datetime
import datetime as dt
import pytz


def current_time():
    return dt.datetime.now().strftime("%H:%M:%S")


def time_string_to_js_timestamp(time: datetime) -> int:
    # js need * 1000 because of different standards
    timezone = pytz.timezone("UTC")
    return round(timezone.localize(time).timestamp() * 1000)

