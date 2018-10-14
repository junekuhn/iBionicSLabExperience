import time
from threading import Thread

import numpy as np

import Config
import Logger
from motion_detection.motion import motionDetection
from util import KinectUtil

has_dog_moved = False
is_dog_down = False


def record_move_status(dog_size):
    Logger.debug("Starting recording of dog still status")
    move_thread = Thread(target=motionDetection, args=(dog_size,))
    move_thread.start()


def reset_move_status():
    global has_dog_moved
    has_dog_moved = False


standing_depth = -1


def record_down_status():
    Logger.debug("Starting recording of dog down status")

    # Start tracking depth
    depth_thread = Thread(target=run_depth_tracking)
    depth_thread.start()

    # Wait 3 seconds while BGS isolates the moving dog
    time.sleep(3)

    Logger.prompt("Press enter when the dog is standing.")
    raw_input()
    # Dog is now standing

    global standing_depth

    standing_depth = dog_depth

    calculate_dog_thread = Thread(target=_calculate_dog_status)
    calculate_dog_thread.start()


def _calculate_dog_status():
    global is_dog_down
    while Config.RUN_FLAG:
        time.sleep(1)
        if dog_depth > standing_depth * 1.1:
            if is_dog_down is not True:
                Logger.debug("Dog is now laying down.")
                is_dog_down = True
        else:
            if is_dog_down is True:
                Logger.debug("Dog is now standing up.")
                is_dog_down = False


dog_depth = -1


def run_depth_tracking():
    global dog_depth
    # Start Kinect software
    KinectUtil.init_depth_stream()

    while Config.RUN_FLAG:
        array = KinectUtil.get_depth_map()

        # TODO Do BGS, image cleanup, gaussian blur, etc

        # Extract depth values from original array
        dog_depth_map = np.extract(None, array)  # TODO replace None with dog_mask

        # Ignore the values if the mask doesn't know of the dog
        if dog_depth_map.size > 500 and np.amax(dog_depth_map) > 0:
            dog_depth = np.average(dog_depth_map)
