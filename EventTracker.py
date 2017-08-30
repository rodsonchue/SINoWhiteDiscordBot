import asyncio
import time
from TimeUtils import TimeOfDay
from TimeUtils import subtract
from operator import attrgetter

class EventTracker:
    def __init__(self):
        self.eventList = {}

    def hasEvent(self, eventName):
        return eventName in self.eventList

    def getEvent(self, eventName):
        return self.eventList[eventName]

    def nextEventTime(self, eventName):
        refTime = time.gmtime()
        currTime = TimeOfDay(refTime.tm_hour, refTime.tm_min)
        event = self.eventList[eventName]

        hasChosen = False
        nextTime = None
        
        for timeStart in event:
            if not hasChosen:
                if (timeStart.hours > currTime.hours or \
                   (timeStart.hours == currTime.hours and timeStart.minutes > currTime.minutes)):
                    nextTime = timeStart
                    hasChosen = True

        if hasChosen:
            return subtract(nextTime, currTime)
        else:
            #Next time is tomorrow
            nextTime = event[0]
            return subtract(nextTime, currTime)

    def addEvent(self, eventName, event):
        """
        Adds event to tracker. event should be a distinct list of TimeOfDay
        """
        self.eventList[eventName] = event
        self.eventList[eventName] = sorted(self.eventList[eventName], key=attrgetter('hours', 'minutes'))
    
            
