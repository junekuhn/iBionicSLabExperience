import Config
import util.FileIOUtil as FileIOUtil
import util.Logger as Logger
import util.ScheduleUtil as ScheduleUtil
from util.PetTutorUtil import dispense_treat

scheduler = ScheduleUtil.Repeater()


def level_one(dog_id):
    Logger.info("Phase One: Level 1 - Starting")
    Logger.data(dog_id, 1, 1, "starting")
    scheduler.schedule(5, 150, dispense_treat)
    if not Config.RUN_FLAG:
        Logger.data(dog_id, 1, 1, "cancelled")
        return False
    FileIOUtil.save(dog_id, 1, 1)
    Logger.info("Phase One: Level 1 - Complete")
    Logger.data(dog_id, 1, 1, "complete")
    return True


def start(dog_id, level):
    if level != 1:
        Logger.error("You have entered an invalid level for Phase One.")
        return
    Logger.info("Phase One: Starting")
    if level_one(dog_id):
        Logger.info("Phase One: Complete")
    else:
        Logger.warning("Phase One: Failed")


def stop():
    Logger.debug("Cancelling all future events for Phase One.")
    scheduler.stop()
