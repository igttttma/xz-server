"""
Time utility module.
Provides unified time retrieval functions.
"""

import cnlunar
from datetime import datetime
from zoneinfo import ZoneInfo


def local_now(timezone: str = None) -> datetime:
    """The time where the device is (an IANA name such as "America/Detroit", from its
    IP location); the server clock when the timezone is unknown. The server may run in
    another country (the VPS clock is China time)."""
    if timezone:
        try:
            return datetime.now(ZoneInfo(timezone)).replace(tzinfo=None)
        except Exception:
            pass
    return datetime.now()

WEEKDAY_MAP = {
    "Monday": "Monday",
    "Tuesday": "Tuesday", 
    "Wednesday": "Wednesday",
    "Thursday": "Thursday",
    "Friday": "Friday",
    "Saturday": "Saturday",
    "Sunday": "Sunday",
}


def get_current_time(now: datetime = None) -> str:
    """
    Get the current time string (format: HH:MM).
    """
    return (now or datetime.now()).strftime("%H:%M")


def get_current_date(now: datetime = None) -> str:
    """
    Get today's date string (format: YYYY-MM-DD).
    """
    return (now or datetime.now()).strftime("%Y-%m-%d")


def get_current_weekday(now: datetime = None) -> str:
    """
    Get today's weekday.
    """
    return WEEKDAY_MAP[(now or datetime.now()).strftime("%A")]


def get_current_lunar_date(now: datetime = None) -> str:
    """
    Get the lunar date string.
    """
    try:
        now = now or datetime.now()
        today_lunar = cnlunar.Lunar(now, godType="8char")
        return "%s %s%s" % (
            today_lunar.lunarYearCn,
            today_lunar.lunarMonthCn[:-1],
            today_lunar.lunarDayCn,
        )
    except Exception:
        return "Failed to get the lunar date"


def get_current_time_info(timezone: str = None) -> tuple:
    """
    Get the current time information.
    Returns: (current time string, today's date, today's weekday, lunar date)
    """
    now = local_now(timezone)
    current_time = get_current_time(now)
    today_date = get_current_date(now)
    today_weekday = get_current_weekday(now)
    lunar_date = get_current_lunar_date(now)
    
    return current_time, today_date, today_weekday, lunar_date
