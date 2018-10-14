import Config
import util.Challenge as Challenge
import util.Logger as Logger
import util.MoveUtil as MoveUtil
import util.NoiseUtil as NoiseUtil
from util import FileIOUtil


def level_one(dog_id):
    Logger.info("Phase Four: Level 1 - Starting")
    Logger.data(dog_id, 4, 1, "starting")
    if Challenge.phase_four(dog_id=dog_id, level=1, treat_frequency_min=3, still_length=30, fail_max=3):
        FileIOUtil.save(dog_id, 4, 1)
        Logger.info("Phase Four: Level 1 - Complete")
        Logger.data(dog_id, 4, 1, "complete")
        return level_two(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Four: Level 1 - Cancelled")
            return False
        Logger.info("Phase Four: Level 1 - Failed, regressing to Level 1")
        Logger.data(dog_id, 4, 1, "failed")
        return level_one(dog_id)


def level_two(dog_id):
    Logger.info("Phase Four: Level 2 - Starting")
    Logger.data(dog_id, 4, 2, "starting")
    if Challenge.phase_four(dog_id=dog_id, level=2, treat_frequency_min=5, still_length=50, fail_max=3):
        FileIOUtil.save(dog_id, 4, 2)
        Logger.info("Phase Four: Level 2 - Complete")
        Logger.data(dog_id, 4, 2, "complete")
        return level_three(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Four: Level 2 - Cancelled")
            return False
        Logger.info("Phase Four: Level 2 - Failed, regressing to Level 1")
        Logger.data(dog_id, 4, 2, "failed")
        return level_one(dog_id)


def level_three(dog_id):
    Logger.info("Phase Four: Level 3 - Starting")
    Logger.data(dog_id, 4, 3, "starting")
    if Challenge.phase_four(dog_id=dog_id, level=3, treat_frequency_min=8, still_length=64, fail_max=3):
        FileIOUtil.save(dog_id, 4, 3)
        Logger.info("Phase Four: Level 3 - Complete")
        Logger.data(dog_id, 4, 3, "complete")
        return level_four(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Four: Level 3 - Cancelled")
            return False
        Logger.info("Phase Four: Level 3 - Failed, regressing to Level 2")
        Logger.data(dog_id, 4, 3, "failed")
        return level_two(dog_id)


def level_four(dog_id):
    Logger.info("Phase Four: Level 4 - Starting")
    Logger.data(dog_id, 4, 4, "starting")
    if Challenge.phase_four(dog_id=dog_id, level=4, treat_frequency_min=12, still_length=60, fail_max=3):
        FileIOUtil.save(dog_id, 4, 4)
        Logger.info("Phase Four: Level 4 - Complete")
        Logger.data(dog_id, 4, 4, "complete")
        return level_five(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Four: Level 4 - Cancelled")
            return False
        Logger.info("Phase Four: Level 4 - Failed, regressing to Level 3")
        Logger.data(dog_id, 4, 4, "failed")
        return level_three(dog_id)


def level_five(dog_id):
    Logger.info("Phase Four: Level 5 - Starting")
    Logger.data(dog_id, 4, 5, "starting")
    if Challenge.phase_four(dog_id=dog_id, level=5, treat_frequency_min=3, treat_frequency_max=17, still_length=120,
                            fail_max=3):
        FileIOUtil.save(dog_id, 4, 5)
        Logger.info("Phase Four: Level 5 - Complete")
        Logger.data(dog_id, 4, 5, "complete")
        return True
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Four: Level 5 - Cancelled")
            return False
        Logger.info("Phase Four: Level 5 - Failed, regressing to Level 4")
        Logger.data(dog_id, 4, 5, "failed")
        return level_four(dog_id)


def start(dog_id, dog_size, level):
    if level < 1 or level > 5:
        Logger.error("You have entered an invalid level for Phase Four.")
        return
    Logger.info("Phase Four: Starting.")
    # Start mic recording
    NoiseUtil.record_bark_status()
    MoveUtil.record_move_status(dog_size)

    if level == 1:
        if level_one(dog_id):
            Logger.info("Phase Four: Complete.")
            return
        else:
            Logger.warning("Phase Four: Failed")
    elif level == 2:
        if level_two(dog_id):
            Logger.info("Phase Four: Complete.")
            return
        else:
            Logger.warning("Phase Four: Failed")
    elif level == 3:
        if level_three(dog_id):
            Logger.info("Phase Four: Complete.")
            return
        else:
            Logger.warning("Phase Four: Failed")
    elif level == 4:
        if level_four(dog_id):
            Logger.info("Phase Four: Complete.")
            return
        else:
            Logger.warning("Phase Four: Failed")
    elif level == 5:
        if level_five(dog_id):
            Logger.info("Phase Four: Complete.")
            return
        else:
            Logger.warning("Phase Four: Failed")


def stop():
    Logger.debug("Cancelling all future events for Phase Four.")
