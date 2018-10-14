import cv2

# cap = cv2.VideoCapture("../../Data/example.mp4")
cap = cv2.VideoCapture(0)
# dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
# dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
img = cv2.imread("../Data/input.png")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if frame is None:
        break
        # Our operations on the frame come here
    #    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = frame
    res = cv2.aruco.detectMarkers(gray, dictionary)
    #    print(res[0],res[1],len(res[2]))
    if len(res[0]) > 0:
        i = 0
        for arr in res[0]:
            for ar in arr:
                cntx = ar[0][0] + ar[1][0] + ar[2][0] + ar[3][0]
                cnty = ar[0][1] + ar[1][1] + ar[2][1] + ar[3][1]
                cntx = int(cntx / 4)
                cnty = int(cnty / 4)
                print cntx, cnty
        cv2.circle(gray, (cntx, cnty), 10, (100, 010, 100), 5)
        cv2.aruco.drawDetectedMarkers(gray, res[0], res[1])

    # Display the resulting frame
    cv2.imshow('frame', gray)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
