import random
import time

import Config
import util.Logger as Logger
import util.MoveUtil as MoveUtil
import util.NoiseUtil as NoiseUtil
import util.PetTutorUtil as PetTutorUtil


def phase_three(dog_id, level, quiet_length, fail_max, treat_frequency_min, treat_frequency_max=-1):
    if treat_frequency_max == -1:
        treat_frequency_max = treat_frequency_min

    quiet_timer = 0
    treat_timer = 0
    treat_dispense_time = 0
    fail_count = 0
    # Reset quiet status
    NoiseUtil.reset_bark_status()
    while quiet_timer < quiet_length and fail_count < fail_max:
        # Wait 1 second
        time.sleep(1)

        if not Config.RUN_FLAG:
            Logger.data(dog_id, 3, level, "cancelled")
            return False

        if treat_timer == 0:
            treat_dispense_time = random.randint(treat_frequency_min, treat_frequency_max)

        if NoiseUtil.has_dog_barked:
            Logger.info("Dog just barked, incrementing fail count.")
            Logger.data(dog_id, 3, level, "dog_bark")
            fail_count += 1
            quiet_timer = 0
            NoiseUtil.reset_bark_status()
            continue
        else:
            quiet_timer += 1
            treat_timer += 1

        # Check if a treat should be dispensed
        if treat_timer == treat_dispense_time:
            PetTutorUtil.dispense_treat()
            treat_timer = 0
            fail_count = 0

    if quiet_timer >= quiet_length:  # Dog passed the Challenge.
        return True
    if fail_count >= fail_max:  # Dog has failed the challenge
        return False

    Logger.error("[Quiet Challenge] CODE SHOULD NEVER GET HERE!")


def phase_four(dog_id, level, still_length, fail_max, treat_frequency_min, treat_frequency_max=-1):
    if treat_frequency_max == -1:
        treat_frequency_max = treat_frequency_min

    still_timer = 0
    treat_timer = 0
    treat_dispense_time = 0
    fail_count = 0
    # Reset quiet and move status
    NoiseUtil.reset_bark_status()
    MoveUtil.reset_move_status()
    while still_timer < still_length and fail_count < fail_max:
        # Wait 1 second
        time.sleep(1)

        if not Config.RUN_FLAG:
            Logger.data(dog_id, 4, level, "cancelled")
            return False

        if treat_timer == 0:
            treat_dispense_time = random.randint(treat_frequency_min, treat_frequency_max)

        if NoiseUtil.has_dog_barked or MoveUtil.has_dog_moved:
            if NoiseUtil.has_dog_barked:
                Logger.data(dog_id, 4, level, "dog_bark")
            else:
                Logger.data(dog_id, 4, level, "dog_move")
            fail_count += 1
            still_timer = 0
            NoiseUtil.reset_bark_status()
            MoveUtil.reset_move_status()

            # Check if the dog has failed too many times
            if fail_count >= fail_max:
                break

            """
            Wait for 10 seconds to allow the dog to stop moving.
            """
            sleep_time = 0
            for i in range(1, Config.MOVE_PAUSE + 1):
                time.sleep(1)
                Logger.debug("Letting the dog stop moving... (%s seconds)" % i)
                if not MoveUtil.has_dog_moved:
                    sleep_time += 1
                else:
                    sleep_time = 0
                    MoveUtil.reset_move_status()
                if sleep_time >= 2:
                    break

            continue  # Continue loop (timer has been reset, don't reward dog, etc)
        else:
            still_timer += 1
            treat_timer += 1

        # Check if a treat should be dispensed
        if treat_timer == treat_dispense_time:
            PetTutorUtil.dispense_treat()
            treat_timer = 0
            fail_count = 0
            """
            Wait for 5 seconds to allow the dog to eat the treat.
            """
            sleep_time = 0
            MoveUtil.reset_move_status()  # This is just a precaution, it should already be reset
            for i in range(1, Config.TREAT_PAUSE + 1):
                time.sleep(1)
                if not MoveUtil.has_dog_moved:
                    sleep_time += 1  # Increment the amount of time the dog has not moved.
                else:
                    sleep_time = 0  # The dog moved, reset sleep time
                    MoveUtil.reset_move_status()
                if sleep_time >= 2:  # Once dog has not moved for X seconds, continue training.
                    break
                Logger.debug("Letting the dog eat... (%s seconds)" % i)

    if still_timer >= still_length:  # Dog passed the Challenge.
        return True
    if fail_count >= fail_max:  # Dog has failed the challenge
        return False

    Logger.error("[Still Challenge] CODE SHOULD NEVER GET HERE!")
