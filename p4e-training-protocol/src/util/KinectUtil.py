import time

import numpy as np
from primesense import _openni2 as c_api
from primesense import openni2

width = 512
height = 424

zeros = np.zeros((1, height, width), dtype=np.uint8)
depth_stream = None


def init_depth_stream():
    global depth_stream
    openni2.initialize()  # This file should be in the same directory as OpenNI2.dll
    kinect = openni2.Device.open_any()
    depth_stream = kinect.create_depth_stream()
    depth_stream.set_video_mode(
        c_api.OniVideoMode(pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM, resolutionX=width,
                           resolutionY=height, fps=25))
    depth_stream.start()
    time.sleep(1)  # Sleep and wait for the kinect to be ready


def get_depth_map():
    frame = depth_stream.read_frame()  # Get a frame from the kinect
    frame_data = frame.get_buffer_as_uint16()  # Get depth data about the frame
    array = np.frombuffer(frame_data, dtype=np.uint16)  # Convert into a 1D array
    return array
