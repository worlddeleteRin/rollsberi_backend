import pytz
from datetime import datetime

def get_time_now():
    tz = pytz.timezone('Europe/Moscow')
    time = datetime.now(tz)
    return time
