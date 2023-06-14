
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("../scripts")

import cv2
import numpy as np
import signal
from pprint import pprint
import os

from filters.filters import *

def show_image(img, img_name:str=''):
    window_name = 'image' if img_name == '' else img_name
    cv2.namedWindow(window_name)
    _img = cv2.resize(img.copy(), (0, 0), fx=0.5,fy=0.5) if img.shape[0] > 800 else img.copy()
    cv2.moveWindow(window_name, 40, 30)
    cv2.imshow(window_name, _img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


input_path = 'ep02_episode_000'

def main():




    image_list = list()
    for f in os.listdir(input_path):
        if f.endswith(".png") and not f.endswith("_cropped.png"):
            image_list.append(os.path.join(input_path, f))
    image_list = sorted(image_list)

    images = list()
    for filepath in image_list:
        images.append(cv2.imread(filepath))


    crop_values, img_dimensions = calculate_crop_values(
        images=images,
        do_add_borders=True,
        additional_crop=0,
    )

    print(crop_values)
    print(img_dimensions)


    images = list()
    for filepath in image_list:
        bgr_img = cv2.imread(filepath)

        h, w, _ = bgr_img.shape
        t, b, l, r = crop_values
        cropped_img = bgr_img[t : h-b,
                            l : w-r,
                            ]

        outpout_filepath = filepath.replace('.png', '_cropped.png')
        outpout_filepath = outpout_filepath.replace(input_path, output_path)
        try:
            cv2.imwrite(outpout_filepath, cropped_img)
        except:
            print(f"failed: {outpout_filepath}")
            pass

        if (cropped_img.shape[0] != img_dimensions[1]
            or cropped_img.shape[1] != img_dimensions[0]):
            print(p_red("ERRRRRORRRRRR!!!!"))

    return





def main_2023_06_15():
    image_list = list()
    for f in os.listdir(input_path):
        if f.endswith(".png") and not f.endswith("_cropped.png"):
            image_list.append(os.path.join(input_path, f))
    image_list = sorted(image_list)



    threshold_min = 5
    remove_px = 0
    kernel = np.ones((3,3), np.uint8)
    erode_kernel = np.ones((3,3), np.uint8)

    for filepath in image_list:
        # Read image
        bgr_img = cv2.imread(filepath).copy()
        bgr_img = cv2.copyMakeBorder(bgr_img,
            top=2, bottom=2, left=2, right=2,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0])

        gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        gray_img, _, _ = automatic_brightness_and_contrast_gray(gray_img)
        _, gray_img = cv2.threshold(gray_img, threshold_min, 255, cv2.THRESH_BINARY)
        gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_CLOSE, kernel)
        gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_OPEN, kernel)
        gray_img = cv2.erode(gray_img,erode_kernel,iterations = 2)

        contours, hierarchy  = cv2.findContours(gray_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # contour = contours[0].reshape(len(contours[0]),2)
        # pprint(hierarchy)

        # img_debug = bgr_img.copy()
        for hi , contour in zip(hierarchy[0], contours):
            # print(hi)
            if hi[0] == -1 and hi[3] == -1:
                x, y, w, h = cv2.boundingRect(contour)
            # cv2.rectangle(img_debug,
            #     (x + remove_px, y +remove_px ),
            #     (x + w -remove_px , y + h -remove_px ),
            #     (255, 0, 0), 1)
                break
        # show_image(img_debug, 'contours')

        print(f"{filepath} -> crop: t,b,l,r: [{x}, {y}, {w}, {h}]")
        cropped_img = bgr_img[y + remove_px : y+h - remove_px,
                              x + remove_px : x+w - remove_px,
                              ]

                # cv2.rectangle(gray_img, (x1,y1), (x2,y2), (255,0,0), 1)
                # cv2.imshow("Is that rectangle ok?", gray_img)
                # cv2.waitKey(0)

                # Finally, we crop the picture and store it


        # contour = max(contours, key = cv2.contourArea)

        # contourImg = cv2.drawContours(bgr_img.copy(), contour, -1, (0,255,0), 3)
        # show_image(contourImg, "contourImg")
        # cv2.contourArea()
        # cv2.maxAreaRect()
        # rect = list()
        # for i in range(len(contour)):
        #     x1, y1 = contour[i]
        #     for j in range(len(contour)):
        #         x2, y2 = contour[j]
        #         area = abs(y2-y1)*abs(x2-x1)
        #         rect.append(((x1,y1), (x2,y2), area))

        # # the first rect of all_rect has the biggest area, so it's the best solution if he fits in the picture
        # all_rect = sorted(rect, key = lambda x : x[2], reverse = True)
        # pprint(rect)



        outpout_filepath = filepath.replace('.png', '_cropped.png')
        try:
            cv2.imwrite(outpout_filepath, cropped_img)
        except:
            print(f"failed: {outpout_filepath}")
            pass



def main_2023_06_24():
    debug = True

    image_list = list()
    for f in os.listdir(input_path):
        if f.endswith(".png") and not f.endswith("_cropped.png"):
            image_list.append(os.path.join(input_path, f))
    image_list = sorted(image_list)


    threshold = 5
    threshold_max = 255
    remove_px = 2

    kernel = np.ones((3,3), np.uint8)


    for filepath in image_list:
        # read image
        bgr_img = cv2.imread(filepath).copy()
        bgr_img = cv2.copyMakeBorder(bgr_img,
            top=2, bottom=2, left=2, right=2,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0])

        gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)


        mask = gray_img
        mask, _, _ = automatic_brightness_and_contrast_gray(mask)
        ret, mask = cv2.threshold(mask,threshold,255,cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, hierarchy  = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


        if False:
            # show all contours
            img_debug = bgr_img.copy()
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(img_debug,
                    (x + remove_px, y +remove_px ),
                    (x + w -remove_px , y + h -remove_px ),
                    (255, 0, 0), 1)
            show_image(img_debug, 'contours')


        # edged = cv2.Canny(gray_img, 30, 200)
        # ret, thresh = cv2.threshold(gray_img,threshold,255,cv2.THRESH_BINARY)

        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
        # mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # cv2.waitKey(0)

        # crop: t,b,l,r: [5, 575, 23, 706]


        if False:


            contours = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = contours[0] if len(contours) == 2 else contours[1]
            big_contour = max(contours, key=cv2.contourArea)
            x,y,w,h = cv2.boundingRect(big_contour)

            # crop image contour image
            img_cropped = bgr_img.copy()
            img_cropped = img_cropped[y:y+h, x:x+w]
        else:
            # bgr_img = high_pass_filter_node(bgr_img, radius=15, contrast=5)

            # linear_filter = cv2.boxFilter(bgr_img, -1, (3,3)) #linear filter
            # blur = cv2.blur(bgr_img, (3,3))
            # bgr_img = cv2.GaussianBlur(bgr_img, (7,7), 0)


            # show_image(linear_filter, 'linear_filter')
            # show_image(blur, 'blur')
            # show_image(gaussian, 'gaussian')
            remove_px = 2

            gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

            threshold = 5
            threshold_max = 255
            # gaussian blur
            # mask = cv2.GaussianBlur(gray_img, (5,5), 0)

            mask = gray_img
            mask, _, _ = automatic_brightness_and_contrast_gray(mask)
            # show_image(mask, 'mask')



            # mask = canny_edge_detection(mask, threshold, threshold_max)
            # mask = cv2.Canny(mask,threshold,255)
            # show_image(mask, 'mask')

            # kernel_size = 3
            # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
            # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            # show_image(mask, 'mask')

            ret, mask = cv2.threshold(mask,threshold,255,cv2.THRESH_BINARY)

            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            # mask = 255 - mask

            show_image(mask, 'mask')

            # show_image(mask, 'contours')
            contours, hierarchy  = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            img_debug = bgr_img.copy()
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(img_debug,
                    (x + remove_px, y +remove_px ),
                    (x + w -remove_px , y + h -remove_px ),
                    (255, 0, 0), 1)
            show_image(img_debug, 'contours')

            continue
            # external_contour = max(contours, key=cv2.contourArea)
            # x, y, w, h = cv2.boundingRect(external_contour)

            # result = bgr_img[y +1:y + h -1, x +1:x + w -1,]
            contour = contours[0].reshape(len(contours[0]),2)

            if False:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                # kernel = np.ones((5,5),np.uint8)
                # mask = cv2.erode(mask,kernel,iterations = 1)
                # mask = cv2.GaussianBlur(mask, (5,5), 0)

                ret, mask = cv2.threshold(mask,threshold,threshold_max,cv2.THRESH_BINARY_INV)
                mask = 255 - mask

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


                # show_image(mask, 'mask')
                # return

                contours, hierarchy  = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                # contours = contours[0] if len(contours) == 2 else contours[1]

                if True:
                    contour = contours[0].reshape(len(contours[0]),2)
                else:
                    external_contour = max(contours, key=cv2.contourArea)

                    contour = external_contour.reshape(len(external_contour),2)
                # print(len(contours[0]))
                # pprint(hierarchy)
                # return
                if debug:
                    for i, contour in enumerate(contours):
                        x, y, w, h = cv2.boundingRect(contour)
                        cv2.rectangle(bgr_img,
                            (x , y),
                            (x + w, y + h),
                            (255, 0, 0), 1)

                result = bgr_img[y_min:y_max, x_min:x_max]

                # cv2.imshow('image', findContours)
                img_debug = cv2.resize(bgr_img.copy(), (0, 0), fx=0.5,fy=0.5) if bgr_img.shape[0] > 800 else bgr_img.copy()
                cv2.imshow('contours', img_debug)
                cv2.waitKey(0)



                # Get all the points of the contour

                # pprint(contour)
                # print(len(contour))
                if debug:
                    img_debug = bgr_img.copy()
                    cv2.drawContours(img_debug, contours, -1, (0, 255, 0), 1)
                    cv2.imshow('Contours', cv2.resize(img_debug, (0, 0), fx=0.5,fy=0.5))
                    # cv2.waitKey(0)
                    # cv2.destroyAllWindows()

        # we assume a rectangle with at least two points on the contour gives a 'good enough' result
        # get all possible rectangles based on this hypothesis
        rect = []

        for i in range(len(contour)):
            x1, y1 = contour[i]
            for j in range(len(contour)):
                x2, y2 = contour[j]
                area = abs(y2-y1)*abs(x2-x1)
                rect.append(((x1,y1), (x2,y2), area))

        # the first rect of all_rect has the biggest area, so it's the best solution if he fits in the picture
        all_rect = sorted(rect, key = lambda x : x[2], reverse = True)

        if all_rect:

            best_rect_found = False
            index_rect = 0
            nb_rect = len(all_rect)
            if debug:
                print(nb_rect)

            # we check if the rectangle is  a good solution
            while not best_rect_found and index_rect < nb_rect:

                rect = all_rect[index_rect]
                (x1, y1) = rect[0]
                (x2, y2) = rect[1]

                valid_rect = True

                # we search a black area in the perimeter of the rectangle (vertical borders)
                x = min(x1, x2)
                while x <max(x1,x2)+1 and valid_rect:
                    if mask[y1,x] == 0 or mask[y2,x] == 0:
                        # if we find a black pixel, that means a part of the rectangle is black
                        # so we don't keep this rectangle
                        valid_rect = False
                    x+=1

                y = min(y1, y2)
                while y <max(y1,y2)+1 and valid_rect:
                    if mask[y,x1] == 0 or mask[y,x2] == 0:
                        valid_rect = False
                    y+=1

                if valid_rect:
                    best_rect_found = True

                index_rect+=1

            if best_rect_found:
                y_min = min(y1, y2)
                y_max = max(y1, y2)
                x_min = min(x1,x2)
                x_max = max(x1,x2)
                print(f"{filepath} -> crop: t,b,l,r: [{y_min}, {y_max}, {x_min}, {x_max}]")

                # cv2.rectangle(gray_img, (x1,y1), (x2,y2), (255,0,0), 1)
                # cv2.imshow("Is that rectangle ok?", gray_img)
                # cv2.waitKey(0)

                # Finally, we crop the picture and store it
                result = bgr_img[y_min:y_max, x_min:x_max]

            else:
                print("{filepath}: No rectangle fitting into the area")

        else:
            print("{filepath}: No rectangle found")




        outpout_filepath = filepath.replace('.png', '_cropped.png')
        try:
            cv2.imwrite(outpout_filepath, result)
        except:
            print(f"failed: {outpout_filepath}")
            pass
        # cv2.imwrite(f"{filename}_morph.png", morph)



    return

    # gaussian blur
    img_blurred = cv2.GaussianBlur(gray_img, (3,3), 0)
    kernel = np.ones((5,5), np.uint8)
    ret, mask = cv2.threshold(img_blurred,threshold,255,cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = 255 - mask

    # Create our mask by selecting the non-zero values of the picture
    # ret, mask = cv2.threshold(gray_img,threshold,255,cv2.THRESH_BINARY)

    # Select the contour
    contours = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    pprint(contours)

    cv2.drawContours(gray_img, contours, -1, (255,0,0), 1)
    cv2.imshow("Your picture with contour", gray_img)
    cv2.waitKey(0)


def main_2023_06_12():

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

    cv2.imshow("thresh", thresh)
    cv2.waitKey(0)


    if True:
        canny = cv2.Canny(thresh, 25, 235, 1)
        # Find contours in the image
        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        # Obtain area for each contour
        contour_sizes = [(cv2.contourArea(contour), contour) for contour in cnts]

        if len(contour_sizes) > 0:
            largest_contour = max(contour_sizes, key=lambda x: x[0])[1]
            x,y,w,h = cv2.boundingRect(largest_contour)
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), (36,255,12), 2)
            ROI = img[y:y+h, x:x+w]
            cv2.imshow("ROI", ROI)

        # cv2.imshow("canny", canny)
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


