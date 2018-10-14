import pickle
import random

import cv2
import numpy

from util import Logger


def tracePath(fileName):
    Logger.info("-----Read File Started-----")
    Logger.info("Reading File :" + str(fileName))
    try:
        with open(fileName, 'rb') as fp:
            pathModel = pickle.load(fp)
            outputImage = numpy.full((int(pathModel.height), int(pathModel.width), 3), dtype='uint8',
                                     fill_value=[255, 255, 255])
            for currentList in pathModel.tracks:
                i = (random.random() * 1000) % 255
                j = (random.random() * 1000) % 255
                k = (random.random() * 1000) % 255
                for points in currentList:
                    cv2.circle(outputImage, points[0], 3, color=(i, j, k))
                    cv2.imshow("output", outputImage)
                    k = cv2.waitKey(5) & 0xff
                    if k == 27:
                        break
        cv2.destroyAllWindows()
        Logger.info("-----Read File Complete-----")
    except OSError as err:
        Logger.error("OS error: %s" % err.message)
    except Exception as exp:
        Logger.error("exception: %s" % exp.message)


def writeAllPaths(pathModel, outputFileName):
    Logger.info("-----Write File Started-----")
    Logger.info("Writing file :" + str(outputFileName))
    try:
        with open(outputFileName, 'wb') as fp:
            pickle.dump(pathModel, fp)
        Logger.info("-----Write File Complete-----")
    except OSError as err:
        Logger.error("OS error: %s" % err.message)
    except Exception as exp:
        Logger.error("exception: %s" % exp.message)
