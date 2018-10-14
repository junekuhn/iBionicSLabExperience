import Config
import util.Logger as Logger
import util.ScheduleUtil as ScheduleUtil
from util import FileIOUtil
from util.PetTutorUtil import dispense_treat

scheduler = ScheduleUtil.Repeater()


def level_one(dog_id):
    Logger.info("Phase Two: Level 1 - Starting")
    Logger.data(dog_id, 2, 1, "starting")
    scheduler.schedule(3, 30, dispense_treat)
    if not Config.RUN_FLAG:
        Logger.data(dog_id, 2, 1, "cancelled")
        return False
    FileIOUtil.save(dog_id, 2, 1)
    Logger.info("Phase Two: Level 1 - Complete")
    Logger.data(dog_id, 2, 1, "complete")
    return level_two(dog_id)


def level_two(dog_id):
    Logger.info("Phase Two: Level 2 - Starting")
    Logger.data(dog_id, 2, 2, "starting")
    scheduler.schedule(5, 60, dispense_treat)
    if not Config.RUN_FLAG:
        Logger.data(dog_id, 2, 2, "cancelled")
        return False
    FileIOUtil.save(dog_id, 2, 2)
    Logger.info("Phase Two: Level 2 - Complete")
    Logger.data(dog_id, 2, 2, "complete")
    return level_three(dog_id)


def level_three(dog_id):
    Logger.info("Phase Two: Level 3 - Starting")
    Logger.data(dog_id, 2, 3, "starting")
    scheduler.schedule(8, 64, dispense_treat)
    if not Config.RUN_FLAG:
        Logger.data(dog_id, 2, 3, "cancelled")
        return False
    FileIOUtil.save(dog_id, 2, 3)
    Logger.info("Phase Two: Level 3 - Complete")
    Logger.data(dog_id, 2, 3, "complete")
    return level_four(dog_id)


def level_four(dog_id):
    Logger.info("Phase Two: Level 4 - Starting")
    Logger.data(dog_id, 3, 4, "starting")
    scheduler.schedule(12, 60, dispense_treat)
    if not Config.RUN_FLAG:
        Logger.data(dog_id, 2, 4, "cancelled")
        return False
    FileIOUtil.save(dog_id, 2, 4)
    Logger.info("Phase Two: Level 4 - Complete")
    Logger.data(dog_id, 3, 4, "complete")
    return True


def start(dog_id, level):
    if level < 1 or level > 4:
        Logger.error("You have entered an invalid level for Phase 2.")
        return
    Logger.info("Phase Two: Starting")
    if level == 1:
        if level_one(dog_id):
            Logger.info("Phase Two: Complete")
        else:
            Logger.warning("Phase Two: Failed")
    elif level == 2:
        if level_two(dog_id):
            Logger.info("Phase Two: Complete")
        else:
            Logger.warning("Phase Two: Failed")
    elif level == 3:
        if level_three(dog_id):
            Logger.info("Phase Two: Complete")
        else:
            Logger.warning("Phase Two: Failed")
    elif level == 4:
        if level_four(dog_id):
            Logger.info("Phase Two: Complete")
        else:
            Logger.warning("Phase Two: Failed")


def stop():
    Logger.debug("Cancelling all future events for Phase Two.")
    scheduler.stop()
