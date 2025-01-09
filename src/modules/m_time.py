from datetime import datetime

def get_current_time():
    return datetime.now().strftime("hour: %H, minute: %M, second: %S")

def get_current_date():
    return datetime.now().strftime("day: %d, month: %m, year: %y")
