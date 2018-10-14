import cv2
import numpy as np


def reject_outliers(data, m=1):
    return data[abs(data - np.mean(data)) < m * np.std(data)]


def getOrb():
    return cv2.BRISK_create()


def computeFeatures(orb, img):
    return orb.detectAndCompute(img, None)


def featureMatching(des1, des2):
    bf = cv2.BFMatcher(cv2.NORM_HAMMING2, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    return matches


def drawMatchesForImage(img1, img2, kp1, kp2, matches, maxMatches):
    img3 = cv2.drawMatches(img1, kp1, img2, kp2, matches[:maxMatches], outImg=img2, flags=2)
    return img3


def drawRectForImg(kp, sortedMatches, img, maxMatches):
    lx = []
    ly = []
    for i in range(1, maxMatches):
        lx.append(int(kp[sortedMatches[i].trainIdx].pt[0]))
        ly.append(int(kp[sortedMatches[i].trainIdx].pt[1]))

    lx = np.asarray(lx)
    ly = np.asarray(ly)
    arrx = reject_outliers(lx)
    arry = reject_outliers(ly)
    pt1 = (int(min(arrx)), int(min(arry)))
    pt2 = (int(max(arrx)), int(max(arry)))
    cv2.rectangle(img, pt1, pt2, (255, 0, 0), 3)
    return img
