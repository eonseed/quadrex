import datetime

def date_filter(value, format='%B'):
    if value is None:
        return ''
    if isinstance(value, int):
        value = datetime.date(1900, value, 1)
    return value.strftime(format)
