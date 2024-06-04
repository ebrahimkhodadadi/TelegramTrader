from jdatetime import datetime as jdatetime

def get_jalali_datetime():
    """
    Returns the current datetime in Jalali format.
    """
    now = jdatetime.now()
    jalali_datetime = now.strftime('%Y/%m/%d %H:%M:%S')
    return jalali_datetime
