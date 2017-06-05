import db
from datetime import datetime

def stringify_time(time):
    time_format = '%-I:%M %P'
    return time.strftime(time_format)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))
