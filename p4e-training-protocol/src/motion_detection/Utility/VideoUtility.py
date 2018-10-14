import cv2

from util import Logger


def playVideo(fileName):
    Logger.info("-----Playing Video-----")
    Logger.info("Video File :" + str(fileName))
    cap = cv2.VideoCapture(fileName)
    key = 0
    try:
        while 1:
            (ret, frame) = cap.read()
            if not ret:
                break
            cv2.imshow("Feed : " + fileName, frame)
            if key == ord("q"):
                break
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                break
        cv2.destroyAllWindows()
        Logger.info("-----Video Play completed-----")
    except OSError as err:
        Logger.error("OS error: %s" % err.message)
    except Exception as exp:
        Logger.error("exception: %s" % exp.message)
