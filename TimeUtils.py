import asyncio
import time
from contextlib import suppress

def time_now():
    return time.strftime("%d/%m/%Y %H:%M", time.gmtime())

class TimeOfDay:
    #In GMT/UTC
    def __init__(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes
        
    def subtract(self, other):
        hr = self.hours - other.hours
        minute = self.minutes - other.minutes
        if minute < 0:
            minute = minute + 60
            hr = hr - 1
        if hr < 0:
            hr = hr + 24
        return hr, minute

    def toJST(self):
        string = str((self.hours+9)%24) + ':' + str(self.minutes)
        if self.minutes < 10: string += '0'
        string += ' JST'
        return string
