import random
import time

import Config
from util import FileIOUtil, Logger, NoiseUtil, MoveUtil, PetTutorUtil
from util.PetTutorUtil import dispense_treat


def start(dog_id, level):
    if str(level) not in ('1', '2', '1D', '2D', '3D', '4D', '5D', '6D', '7D', '8D', '9D'):
        Logger.error("You have entered an invalid level for Phase Five.")
        return
    Logger.info("Phase Five: Starting.")
    # Start mic recording
    NoiseUtil.record_bark_status()
    MoveUtil.record_down_status()

    if str(level) in ('1', '2'):
        if str(level) == '1':
            dog_standing(dog_id, 1)
        elif str(level) == '2':
            dog_standing(dog_id, 2)
    else:
        dog_down(dog_id, level)


def stop():
    Logger.debug("Cancelling all future events for Phase Five.")


levels = {
    '1': {
        'min': 10,
        'max': 30,
        'duration': 180
    },
    '2': {
        'min': 20,
        'max': 60,
        'duration': -1
    },
    '1D': {
        'min': 2,
        'max': 2,
        'duration': 30
    },
    '2D': {
        'min': 3,
        'max': 3,
        'duration': 30
    },
    '3D': {
        'min': 5,
        'max': 5,
        'duration': 50
    },
    '4D': {
        'min': 8,
        'max': 8,
        'duration': 64
    },
    '5D': {
        'min': 12,
        'max': 12,
        'duration': 60
    },
    '6D': {
        'min': 3,
        'max': 17,
        'duration': 180
    },
    '7D': {
        'min': 3,
        'max': 45,
        'duration': 300
    },
    '8D': {
        'min': 10,
        'max': 75,
        'duration': 600
    },
    '9D': {
        'min': 10,
        'max': 120,
        'duration': 900
    }
}


def dog_standing(dog_id, level=1):
    Logger.info("Phase Five: Level %s - Starting" % level)
    Logger.data(dog_id, 5, level, "starting")

    stand_time = 0
    treat_timer = 1
    treat_dispense_time = 0

    if level == 2:
        stand_time = levels['1']['duration'] + 1

    """ DOG IS STANDING """
    while True:
        # If the program is calling for cancellation, just cancel whatever we are doing
        if not Config.RUN_FLAG:
            return False

        # If the dog has laid down, move to #D levels.
        if MoveUtil.is_dog_down:
            Logger.data(dog_id, 5, 1 if stand_time <= levels['1']['duration'] else 2, "dog_down")
            return dog_down(dog_id, '1D')

        # If the dog has barked, reset to level 1
        if NoiseUtil.has_dog_barked:
            stand_time = 0
            treat_timer = 1
            continue

        # If the dog has completed Level 1, announce and save
        if stand_time == levels['1']['duration']:
            FileIOUtil.save(dog_id, 5, 1)
            Logger.info("Phase Five: Level 1 - Complete")
            Logger.data(dog_id, 5, 1, "complete")
            FileIOUtil.save(dog_id, 5, 1)

            Logger.info("Phase Five: Level 2 - Starting")
            Logger.data(dog_id, 5, 2, "starting")

        # If we just gave a treat, figure out the next time we should dispense one
        if treat_timer == 1:
            treat_dispense_time = random.randint(
                levels['1']['min'] if stand_time <= levels['1']['duration'] else levels['2']['min'],
                levels['1']['max'] if stand_time <= levels['1']['duration'] else levels['2']['max'])

        # Check if a treat should be dispensed
        if treat_timer == treat_dispense_time:
            dispense_treat()
            treat_timer = 0

        # End stuff
        time.sleep(1)
        treat_timer += 1
        stand_time += 1


def dog_down(dog_id, level="1D"):
    # How long the dog is laying down
    down_time = 0
    # What time interval we will give the treat on
    treat_timer = 1
    treat_dispense_time = 0
    fail_count = 0
    stand_timer = 0

    level = int(level[0])

    # Grace periods
    grace_down_timer = 0
    grace_bark_timer = 0

    dog_stand_state = False

    Logger.info("Phase Five: Level %sD - Starting" % level)
    Logger.data(dog_id, 5, "%sD" % level, "starting")

    while True:
        if not Config.RUN_FLAG:
            return False

        ''' Setup '''

        if down_time >= levels["%sD" % level]['duration']:
            Logger.info("Phase Five: Level %sD - Complete" % level)
            Logger.data(dog_id, 5, "%sD" % level, "complete")
            FileIOUtil.save(dog_id, 5, "%sD" % level)
            if level >= 9:
                Logger.info("Phase Five: Complete.")
                return  # Dog has passed Phase 5
            level += 1  # Increase the level the dog is on
            Logger.info("Phase Five: Level %sD - Starting" % level)
            Logger.data(dog_id, 5, "%sD" % level, "starting")
            down_time = 0  # Start timer over for new level
            treat_timer = 1  # Calculate new treat time based on new level

        if treat_timer == 1:
            treat_dispense_time = random.randint(levels["%sD" % level]['min'], levels["%sD" % level]['max'])

        ''' Log what happened in the last second '''

        if not MoveUtil.is_dog_down and not dog_stand_state:
            dog_stand_state = True
            Logger.data(dog_id, 5, "%sD" % level, "dog_stand")
        if MoveUtil.is_dog_down and dog_stand_state:
            dog_stand_state = False
            Logger.data(dog_id, 5, "%sD" % level, "dog_down")
        if NoiseUtil.has_dog_barked:
            Logger.data(dog_id, 5, "%sD" % level, "dog_bark")

        ''' manage stand timer '''
        if not MoveUtil.is_dog_down:
            stand_timer += 1
        else:
            stand_timer = 0

        ''' Punishments for bad behavior '''

        if grace_down_timer <= 0 and not MoveUtil.is_dog_down:
            NoiseUtil.reset_bark_status()
            if level < 8 or (level >= 8 and stand_timer > 10):
                Logger.info("Dog just stood, incrementing fail count.")
                fail_count += 1
                grace_down_timer = 20  # Grace period
                down_time = 0

        elif grace_bark_timer <= 0 and NoiseUtil.has_dog_barked:
            NoiseUtil.reset_bark_status()
            Logger.info("Dog just barked, incrementing fail count.")
            fail_count += 1
            grace_bark_timer = 5  # Grace period
            down_time = 0

        if fail_count >= 6:  # Dog failed 2 levels in a row, go to level 1
            Logger.info("Phase Five: Level %sD and %sD - Failed, regressing to Level 1" % (level + 1, level))
            Logger.data(dog_id, 5, level, "failed_restart")
            return dog_standing(dog_id, 1)

        if fail_count == 3:  # Maximum number of fails before regressing level
            Logger.info(
                "Phase Five: Level %sD - Failed, regressing to Level %sD" % (level, level - 1 if level - 1 >= 1 else 1))
            Logger.data(dog_id, 5, "%sD" % level, "failed")
            if level > 1:
                level -= 1

            Logger.info("Phase Five: Level %sD - Starting" % level)
            Logger.data(dog_id, 5, "%sD" % level, "starting")
            down_time = 0
            # Treat reset
            treat_timer = 1
            treat_dispense_time = 0
            # Grace periods reset
            grace_bark_timer = 0
            grace_down_timer = 0
            continue

        ''' Reset grace period once dog lays back down '''

        if grace_down_timer > 0 and MoveUtil.is_dog_down:
            grace_down_timer = 0
            down_time = 0

        if treat_timer == treat_dispense_time:
            PetTutorUtil.dispense_treat()
            treat_timer = 0
            fail_count = 0

        # End stuff
        time.sleep(1)
        treat_timer += 1
        down_time += 1
        if grace_down_timer > 0:
            grace_down_timer -= 1
        if grace_bark_timer > 0:
            grace_bark_timer -= 1
