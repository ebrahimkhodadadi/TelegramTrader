from datetime import datetime, time

def is_now_between(start_str, end_str):
    """
    start_str and end_str should be in 'HH:MM' format (24-hour clock)
    """
    now = datetime.now().time()
    start = datetime.strptime(start_str, "%H:%M").time()
    end = datetime.strptime(end_str, "%H:%M").time()

    if start <= end:
        return start <= now <= end
    else:
        # Time range crosses midnight
        return now >= start or now <= end