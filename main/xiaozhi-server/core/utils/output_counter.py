import datetime
from typing import Dict, Tuple

# Global dict storing the daily output character count for each device
_device_daily_output: Dict[Tuple[str, datetime.date], int] = {}
# Date of the last check
_last_check_date: datetime.date = None


def reset_device_output():
    """
    Reset the daily output character count for all devices.
    Called every day at midnight.
    """
    _device_daily_output.clear()


def get_device_output(device_id: str) -> int:
    """
    Get today's output character count for a device.
    """
    current_date = datetime.datetime.now().date()
    return _device_daily_output.get((device_id, current_date), 0)


def add_device_output(device_id: str, char_count: int):
    """
    Increase the output character count for a device.
    """
    current_date = datetime.datetime.now().date()
    global _last_check_date

    # Clear the counter on the first call or when the date changes
    if _last_check_date is None or _last_check_date != current_date:
        _device_daily_output.clear()
        _last_check_date = current_date

    current_count = _device_daily_output.get((device_id, current_date), 0)
    _device_daily_output[(device_id, current_date)] = current_count + char_count


def check_device_output_limit(device_id: str, max_output_size: int) -> bool:
    """
    Check whether a device has exceeded its output limit.
    :return: True if the limit is exceeded, False otherwise
    """
    if not device_id:
        return False
    current_output = get_device_output(device_id)
    return current_output >= max_output_size
