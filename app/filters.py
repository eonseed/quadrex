import datetime

def date_filter(value, format='%B'):
    if value is None:
        return ''
    return value.strftime(format)
