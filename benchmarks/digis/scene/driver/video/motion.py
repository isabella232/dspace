import cv2
import numpy as np

# contour area threshold
contour_thresh = 10000


class MotionDetect:
    def __init__(self, ref_frame):
        # init with empty frame
        f_init = np.zeros(ref_frame.shape, np.uint8)
        f_init = cv2.cvtColor(f_init, cv2.COLOR_BGR2GRAY)
        f_init = cv2.GaussianBlur(f_init, (21, 21), 0)

        self.prev_frame = f_init
        self.history = list()

    def moved(self, frame) -> bool:
        moved = False

        f_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        f_gray = cv2.GaussianBlur(f_gray, (21, 21), 0)

        delta_frame = cv2.absdiff(self.prev_frame, f_gray)
        thresh_frame = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

        contours, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for ctr in contours:
            if cv2.contourArea(ctr) < contour_thresh:
                continue
            moved = True

            # plot bounding box
            # (x, y, w, h) = cv2.boundingRect(ctr)
            # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        self.history.append(moved)
        self.history = self.history[-2:]

        # cv2.imshow("Gray Frame", f_gray)
        # cv2.imshow("Delta Frame", delta_frame)
        # cv2.imshow("Threshold Frame", thresh_frame)
        # cv2.imshow("Color Frame", frame)
        self.prev_frame = f_gray
        if moved:
            print(f"motion detected")
        return moved
