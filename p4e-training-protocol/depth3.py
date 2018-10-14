import cv2

cap = cv2.VideoCapture(cv2.CAP_OPENNI_DEPTH_MAP)

width = cap.get(3)
height = cap.get(4)

print width
print height

bgs = cv2.createBackgroundSubtractorMOG2()
fgMask = None

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 30.0, (int(width), int(height)))

for x in range(0, 500):
    print x
    (ret, frame) = cap.read()

    if not ret:
        break

    fgMask = bgs.apply(frame)

    frame = cv2.cvtColor(fgMask, cv2.COLOR_GRAY2RGB)
    out.write(frame)

out.release()
""" WORKS with RGB"""
