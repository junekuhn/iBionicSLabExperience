import Config
import util.Challenge as Challenge
import util.Logger as Logger
import util.NoiseUtil as NoiseUtil
from util import FileIOUtil


# def level_one(dog_id):
#    Logger.info("Phase Three: Level 1 - Starting")
#    Logger.data(dog_id, 3, 1, "starting")
#    if Challenge.phase_three(dog_id=dog_id, level=1, treat_frequency_min=2, quiet_length=30, fail_max=3):
#        FileIOUtil.save(dog_id, 3, 1)
#        Logger.info("Phase Three: Level 1 - Complete")
#        Logger.data(dog_id, 3, 1, "complete")
#        return level_two(dog_id)
#    else:
#        if not Config.RUN_FLAG:
#            Logger.info("Phase Three: Level 1 - Cancelled")
#            return False
#        Logger.info("Phase Three: Level 1 - Failed, regressing to Level 1")
#        Logger.data(dog_id, 3, 1, "failed")
#        return level_one(dog_id)


def level_two(dog_id):
    Logger.info("Phase Three: Level 2 - Starting")
    Logger.data(dog_id, 3, 2, "starting")
    if Challenge.phase_three(dog_id=dog_id, level=2, treat_frequency_min=3, quiet_length=30, fail_max=3):
        FileIOUtil.save(dog_id, 3, 2)
        Logger.info("Phase Three: Level 2 - Complete")
        Logger.data(dog_id, 3, 2, "complete")
        return level_three(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Three: Level 2 - Cancelled")
            return False
        Logger.info("Phase Three: Level 2 - Failed, regressing to Level 2")
        Logger.data(dog_id, 3, 2, "failed")
        return level_two(dog_id)


def level_three(dog_id):
    Logger.info("Phase Three: Level 3 - Starting")
    Logger.data(dog_id, 3, 3, "starting")
    if Challenge.phase_three(dog_id=dog_id, level=3, treat_frequency_min=5, quiet_length=50, fail_max=3):
        FileIOUtil.save(dog_id, 3, 3)
        Logger.info("Phase Three: Level 3 - Complete")
        Logger.data(dog_id, 3, 3, "complete")
        return level_four(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Three: Level 3 - Cancelled")
            return False
        Logger.info("Phase Three: Level 3 - Failed, regressing to Level 2")
        Logger.data(dog_id, 3, 3, "failed")
        return level_two(dog_id)


def level_four(dog_id):
    Logger.info("Phase Three: Level 4 - Starting")
    Logger.data(dog_id, 3, 4, "starting")
    if Challenge.phase_three(dog_id=dog_id, level=4, treat_frequency_min=8, quiet_length=64, fail_max=3):
        FileIOUtil.save(dog_id, 3, 4)
        Logger.info("Phase Three: Level 4 - Complete")
        Logger.data(dog_id, 3, 4, "complete")
        return level_five(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Three: Level 4 - Cancelled")
            return False
        Logger.info("Phase Three: Level 4 - Failed, regressing to Level 3")
        Logger.data(dog_id, 3, 4, "failed")
        return level_three(dog_id)


def level_five(dog_id):
    Logger.info("Phase Three: Level 5 - Starting")
    Logger.data(dog_id, 3, 5, "starting")
    if Challenge.phase_three(dog_id=dog_id, level=5, treat_frequency_min=12, quiet_length=60, fail_max=3):
        FileIOUtil.save(dog_id, 3, 5)
        Logger.info("Phase Three: Level 5 - Complete")
        Logger.data(dog_id, 3, 5, "complete")
        return level_six(dog_id)
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Three: Level 5 - Cancelled")
            return False
        Logger.info("Phase Three: Level 5 - Failed, regressing to Level 4")
        Logger.data(dog_id, 3, 5, "failed")
        return level_four(dog_id)


def level_six(dog_id):
    Logger.info("Phase Three: Level 6 - Starting")
    Logger.data(dog_id, 3, 6, "starting")
    if Challenge.phase_three(dog_id=dog_id, level=6, treat_frequency_min=3, treat_frequency_max=17, quiet_length=120,
                             fail_max=3):
        FileIOUtil.save(dog_id, 3, 6)
        Logger.info("Phase Three: Level 6 - Complete")
        Logger.data(dog_id, 3, 6, "complete")
        return True
    else:
        if not Config.RUN_FLAG:
            Logger.info("Phase Three: Level 6 - Cancelled")
            return False
        Logger.info("Phase Three: Level 6 - Failed, regressing to Level 5")
        Logger.data(dog_id, 3, 6, "failed")
        return level_five(dog_id)


def start(dog_id, level):
    if level < 2 or level > 6:
        Logger.error("You have entered an invalid level for Phase Three.")
        return
    Logger.info("Phase Three: Starting.")
    # Start mic recording
    NoiseUtil.record_bark_status()

    #    if level == 1:
    #        if level_one(dog_id):
    #            Logger.info("Phase Three: Complete.")
    #            return
    #        else:
    #            Logger.warning("Phase Three: Failed")
    if level == 2:
        if level_two(dog_id):
            Logger.info("Phase Three: Complete.")
            return
        else:
            Logger.warning("Phase Three: Failed")
    elif level == 3:
        if level_three(dog_id):
            Logger.info("Phase Three: Complete.")
            return
        else:
            Logger.warning("Phase Three: Failed")
    elif level == 4:
        if level_four(dog_id):
            Logger.info("Phase Three: Complete.")
            return
        else:
            Logger.warning("Phase Three: Failed")
    elif level == 5:
        if level_five(dog_id):
            Logger.info("Phase Three: Complete.")
            return
        else:
            Logger.warning("Phase Three: Failed")
    elif level == 6:
        if level_six(dog_id):
            Logger.info("Phase Three: Complete.")
            return
        else:
            Logger.warning("Phase Three: Failed")


def stop():
    Logger.debug("Cancelling all future events for Phase Three.")
