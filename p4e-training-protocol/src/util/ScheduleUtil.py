import sched
import time

import Config


class Repeater:
    """Simple class to repetitively call a function"""
    """Note: The called function must execute in less time than the delay in order to stay accurate"""
    """Example: ScheduleUtil.Repeater().repeat(10, 1, function, (arg,)"""

    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def repeat(self, count, delay, action, args=()):
        if not Config.RUN_FLAG:
            return
        start_time = time.time()
        for x in range(1, count+1):
            self.scheduler.enterabs(start_time + x * delay, 1, action, args)
        self.scheduler.run()

    def schedule(self, every_seconds, for_seconds, action, args=()):
        if not Config.RUN_FLAG:
            return
        count = for_seconds / every_seconds
        self.repeat(count, every_seconds, action, args)

    def stop(self):
        for e in self.scheduler.queue:
            self.scheduler.cancel(e)
