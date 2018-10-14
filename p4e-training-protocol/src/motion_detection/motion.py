import Config
from motion_detection.Main.MotionTracking import backgroundSubtraction


def motionDetection(dog_size):
    backgroundSubtraction(Config.CAMERA_ID, dog_size)
    # backgroundSubtraction("D:/ds.mp4", resultQueue, "", 0))
