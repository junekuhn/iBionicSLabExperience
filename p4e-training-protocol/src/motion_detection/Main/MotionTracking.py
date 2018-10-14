from collections import namedtuple

import cv2
import numpy
import numpy as np

import Config
import util.MoveUtil
from motion_detection.Model.PathModel import PathModel
from util import Logger

Point = namedtuple("Point", "x y")
sizeOfFrame = (0, 0)


def pathTrack(allTracks, centerPt, frame, frameNo):
    addNewList = True
    cv2.circle(frame, centerPt, 3, color=(255, 255, 255))
    for track in allTracks:
        pt1 = Point(track[len(track) - 1][0][0], track[len(track) - 1][0][1])
        pt1 = numpy.array(pt1)
        pt2 = numpy.array(centerPt)
        if numpy.linalg.norm(pt1 - pt2) < 20 and frameNo - track[len(track) - 1][1] < 5:
            util.MoveUtil.has_dog_moved = True
            track.append((centerPt, frameNo))
            for i in range(1, len(track)):
                cv2.line(frame, track[len(track) - i][0], track[len(track) - i - 1][0], (255, 255, 0), 4)
            addNewList = False
            break
    if addNewList:
        currentTrack = []
        currentTrack.append((centerPt, frameNo))
        allTracks.append(currentTrack)


def backgroundSubtraction(inputVideoStream, dog_size):  # minimum dog sizes
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

    Logger.debug("Dog Size is: %s" % dog_size)


    try:
        cap = cv2.VideoCapture(inputVideoStream)
    except Exception as exp:
        exit(1)
    width = cap.get(3)
    height = cap.get(4)
    resize = False
    if (int(width) != 640 and int(height) != 480):
        width = width / 2
        height = height / 2
        resize = True
    sizeOfFrame = (int(width), int(height))
    Logger.debug("Video Stream Acquired: " + str(inputVideoStream) + " with dimensions " + str(sizeOfFrame))
    heightWidthRect = 750  # detectionArea if detectionArea > 0 else (height * width * 0.002)
    Logger.debug("Minimum Contour Area: " + str(heightWidthRect))
    allTracks = []
    frameNo = 0
    kernel = numpy.ones((5, 5), numpy.uint8)
    cntx = -1
    cnty = -1
    xcoord = np.array([[459, 450]]).T  # storing x and y coordinates as column vectors
    ycoord = np.array([[467, 466]]).T
    coord_list = []
    cameraMatrix = np.array([[532.80990646, 0.0, 342.49522219], [0.0, 532.93344713, 233.88792491], [0.0, 0.0, 1.0]])
    distCoeffs = np.array([-2.81325798e-01, 2.91150014e-02, 1.21234399e-03, -1.40823665e-04, 1.54861424e-01])
    axisLen = 0.01
    slbg = cv2.createBackgroundSubtractorMOG2(varThreshold=16, detectShadows=False)
    axispoints = np.float32([[0, 0, 0], [axisLen, 0, 0], [0, axisLen, 0], [0, 0, axisLen]]).reshape(-1, 3)

    if dog_size == 0:
        heightWidthRect = 500
        Logger.debug("Small rectangle size is: " + str(heightWidthRect))

    elif dog_size == 1:
        heightWidthRect = 750
        Logger.debug("Medium rectangle size is: " + str(heightWidthRect))

    elif dog_size == 2:
        heightWidthRect = 1000
        Logger.debug("Large rectangle size is: " + str(heightWidthRect))

    try:
        while Config.RUN_FLAG:
            # capture frame-by-frame
            (ret, frame) = cap.read()
            if resize:
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            if not ret:
                break

            fgmask = slbg.apply(frame)
            fgmask = cv2.blur(fgmask, (15, 15), (-1, -1))
            fgmask = cv2.threshold(fgmask, 235, 255, cv2.THRESH_BINARY)[1]
            fgmask = cv2.dilate(fgmask, None, iterations=2)
            fgmask = cv2.erode(fgmask, kernel, iterations=2)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

            (_, contours, _) = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # contours is a double-array, outer array is a list of contours, inner array is points of a single contour
            # hierarchy is parent-child relationship of the contours
            # foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY)
            foreground = slbg.getBackgroundImage()
            res = cv2.aruco.detectMarkers(frame, dictionary)

            if len(res[0]) > 0:
                frame = cv2.aruco.drawDetectedMarkers(frame, res[0], res[1])
                rvecs, tvecs = cv2.aruco.estimatePoseSingleMarkers(res[0], 0.05, cameraMatrix, distCoeffs)
                print cv2.aruco.estimatePoseSingleMarkers(res[0], 0.05, cameraMatrix, distCoeffs)

                for i in range(0, len(res[1])):
                    #                cv2.circle(frame, Point(res[0][0][0][0][0],res[0][0][0][0][1]), 3, color=(255, 255, 255))
                    #                cv2.circle(frame, Point(res[0][0][0][1][0],res[0][0][0][1][1]), 3, color=(255, 255, 255))
                    #                cv2.circle(frame, Point(res[0][0][0][2][0],res[0][0][0][2][1]), 3, color=(255, 255, 255))
                    #                cv2.circle(frame, Point(res[0][0][0][3][0],res[0][0][0][3][1]), 3, color=(255, 255, 255))
                    #                frame = cv2.aruco.drawAxis(frame, cameraMatrix, distCoeffs, rvecs[i], tvecs[i], 0.01);
                    try:
                        imgpts, _ = cv2.projectPoints(axispoints, rvec=rvecs, tvec=tvecs, cameraMatrix=cameraMatrix,
                                                      distCoeffs=distCoeffs)

                        apt0 = Point(imgpts[0][0][0], imgpts[0][0][1])
                        apt1 = Point(imgpts[1][0][0], imgpts[1][0][1])
                        apt2 = Point(imgpts[2][0][0], imgpts[2][0][1])
                        apt3 = Point(imgpts[3][0][0], imgpts[3][0][1])
                        cv2.line(frame, apt0, apt1, (0, 0, 255), 3)
                        cv2.line(frame, apt0, apt2, (0, 255, 0), 3)
                        # cv2.line(frame, pt0, pt3, (255, 0, 0), 3)
                    except Exception as exp:
                        Logger.error(exp.message)

            listOfRectangles = []

            for c in contours:
                if cv2.contourArea(c) < heightWidthRect:
                    continue
                listOfRectangles.append(cv2.boundingRect(c))
                rect = cv2.minAreaRect(c)
                points = cv2.boxPoints(rect)
                points = np.int8(points)

                # check to see if any rectangle points are in list
                if np.any(np.logical_and(xcoord == points[:, 0], ycoord == points[:, 1])):  # checks to see if any instance occurs where coordinates are in bounding box
                    continue
                coord_list.append(points)

            if len(listOfRectangles) > 0:
                cv2.groupRectangles(listOfRectangles, 1, 0.05)
                if len(res[0]) > 0:
                    for arr in res[0]:
                        for ar in arr:
                            cntx = ar[0][0] + ar[1][0] + ar[2][0] + ar[3][0]
                            cnty = ar[0][1] + ar[1][1] + ar[2][1] + ar[3][1]
                            cntx = int(cntx / 4)
                            cnty = int(cnty / 4)
                    if len(res[0]) == 0:
                        cntx = -1
                        cnty = -1

                for rectangle in listOfRectangles:
                    (x, y, w, h) = rectangle
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, "Movement No. " + str(len(allTracks)), (x, y), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                (200, 0, 155), 1)
                    centerPt = Point((x + x + w) / 2, (y + y + h) / 2)
                    pathTrack(allTracks, centerPt, frame, frameNo)

                    pt1 = numpy.array([cntx, cnty])
                    pt2 = numpy.array(centerPt)
                    if cntx != -1 and numpy.linalg.norm(pt1 - pt2) < 200 and apt1[1] < pt2[1] and apt2[1] < pt2[1]:
                        Logger.debug("in proximity")

            cv2.imshow("Security Feed", frame)
            cv2.imshow("movements", fgmask)
            cv2.imshow("foreground", foreground)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            k = cv2.waitKey(2) & 0xff
            if k == 27:
                break
            frameNo = frameNo + 1
    except Exception as exp:
        Logger.error(exp)
    finally:
        cap.release()
        readFinished = True
        cv2.destroyAllWindows()
        Logger.debug("Total Tracks Detected:" + str(len(allTracks)))
        pathModel = PathModel(height=height, width=width, tracks=allTracks)
