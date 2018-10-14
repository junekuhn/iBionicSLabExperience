import cv2
import numpy as np
import openni

# Initialise OpenNI
context = openni.Context()
context.init()

# Create a depth generator to access the depth stream
depth = openni.DepthGenerator()
depth.create(context)
depth.set_resolution_preset(openni.RES_VGA)
depth.fps = 30

# Start Kinect
context.start_generating_all()
context.wait_any_update_all()

# Create array from the raw depth map string
frame = np.fromstring(depth.get_raw_depth_map_8(), "uint8").reshape(480, 640)

# Render in OpenCV
cv2.imshow("image", frame)
