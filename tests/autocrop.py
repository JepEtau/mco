
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import signal
from pprint import pprint

filename = 'ep02_00030'
threshold = 236

# https://stackoverflow.com/questions/21410449/how-do-i-crop-to-largest-interior-bounding-box-in-opencv
# https://stackoverflow.com/questions/56263917/how-to-auto-crop-the-white-part-of-this-picture-that-is-inside-the-grey
# https://stackoverflow.com/questions/64795711/removing-border-from-the-image

def main():

    # read image
    img = cv2.imread(f"{filename}.png")
    img_copy = img.copy()

    # convert to grayscale
    gray_img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    # invert gray image
    # gray_img = 255 - gray_img

    # gaussian blur
    blurred = cv2.GaussianBlur(gray_img, (3,3), 0)

    kernel = np.ones((5,5), np.uint8)

    ret, thresh = cv2.threshold(blurred,threshold,255,cv2.THRESH_BINARY)

    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # invert thresh
    thresh = 255 - thresh

    if True:
        canny = cv2.Canny(thresh, 25, 235, 1)
        # Find contours in the image
        cnts = cv2.findContours(canny.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        # Obtain area for each contour
        contour_sizes = [(cv2.contourArea(contour), contour) for contour in cnts]

        if len(contour_sizes) > 0:
            largest_contour = max(contour_sizes, key=lambda x: x[0])[1]
            x,y,w,h = cv2.boundingRect(largest_contour)
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), (36,255,12), 2)
            ROI = img[y:y+h, x:x+w]
            cv2.imshow("ROI", ROI)

        cv2.imshow("canny", canny)
        cv2.imshow("detected", img_copy)
        cv2.waitKey(0)

    else:

        # threshold
        ret, thresh = cv2.threshold(blur,threshold,255,cv2.THRESH_BINARY)

        # apply close and open morphology to fill tiny black and white holes
        # edges = cv2.Canny(gray_img,25,235)
        # cv2.imwrite(f"{filename}_edges.png",edges)

        kernel = np.ones((5,5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # invert thresh
        thresh = 255 - thresh

        # get contours (presumably just one around the nonzero pixels)
        # then crop it to bounding rectangle
        # contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        # pprint(contours)
        print(len(contours))
        print(type(contours))
        print(hierarchy)

        # contours = contours[0] if len(contours) == 2 else contours[1]

        cntr = contours[0]
        x,y,w,h = cv2.boundingRect(cntr)



    crop = img[y:y+h, x:x+w]


    # save cropped image
    cv2.imwrite(f"{filename}_thtreshold.png",thresh)
    cv2.imwrite(f"{filename}_cropped.png",crop)



    # cv2.imshow("IMAGE", img)
    cv2.imshow("THRESH", thresh)
    # cv2.imshow("CROP", crop)
    cv2.waitKey(0)
    cv2.destroyAllWindows()





if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()



# # stupid FFmpeg
# cls; ../mco_3rd_party/ffmpeg-5.1/ffmpeg -i ep02_032.mkv -vf cropdetect -f null - 2>&1 | awk '/crop/ { print $NF }' | tail -1

# crop=1408:1152:46:26

# cls; ../mco_3rd_party/ffmpeg-5.1/ffmpeg -i ep02_032.mkv  -vf crop=1408:1152:46:26 -y output.mp4


