import asyncio
import time
import TimeUtils as tu
from contextlib import suppress

class DailyTask:
    def __init__(self, func, func_name, timeofday : tu.TimeOfDay):
        self.func = func
        self.func_name = func_name
        self.timeofday = timeofday
        self.is_started = False
        self._task = None

    async def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    def getWaitDuration(self, tod):
        t = time.gmtime()

        seconds = ((tod.hours-t.tm_hour)*3600) + ((tod.minutes-t.tm_min)*60) - t.tm_sec

        #When the time has already passed for the current day
        if(seconds < 0):
            seconds = seconds + 86400
        return seconds

    async def _run(self):
        while True:
            s = self.getWaitDuration(self.timeofday)
            time_stamp = tu.time_now()
            print (time_stamp + " DAILY TASK: " + self.func_name + " fires off after " + str(s) + "s")
            await asyncio.sleep(s)
            await self.func()
            await asyncio.sleep(5.0)
