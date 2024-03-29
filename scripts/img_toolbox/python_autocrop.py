# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from pprint import pprint
from PIL import Image, ImageChops

from img_toolbox.filters import (
    automatic_brightness_and_contrast_gray
)
from utils.pretty_print import *
from img_toolbox.utils import show_image


def __get_coordinates(coordinates:np.array) -> list:
    threshold = int((max(coordinates) - min(coordinates))/2)
    return (max(coordinates[coordinates < threshold]),
            min(coordinates[coordinates > threshold]))



def calculate_crop_values(
        images:list[np.ndarray],
        threshold_min:int=10,
        additional_crop:int=0,
        morph_kernel_radius:int=3,
        erode_kernel_radius:int=0,
        do_add_borders:bool=False
        ) -> list[list, list]:
    # Calculate the max crop values for a list of images
    # returns a list of crop values and img dimensions
    # images shall be BGR
    verbose = False
    debug = False

    border_size = 2 if do_add_borders else 0
    morph_kernel = np.ones((morph_kernel_radius, morph_kernel_radius), np.uint8)
    if erode_kernel_radius != 0:
        erode_kernel = np.ones((erode_kernel_radius, erode_kernel_radius), np.uint8)
        erode_iterations = 2

    h_img, w_img, _ = images[0].shape

    shot_contours = list()
    for i, bgr_img in enumerate(images):
        if do_add_borders:
            # Do add border to correctly detect the outer limits
            # Do it before conversion to facilitate debug. TODO: do this after conversion
            #   once validated and correct all coordinates used for debug
            bgr_img = cv2.copyMakeBorder(bgr_img,
                top=border_size, bottom=border_size, left=border_size, right=border_size,
                borderType=cv2.BORDER_CONSTANT,
                value=[0, 0, 0])

        gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        brightness_estimation = int(cv2.mean(gray_img)[0])
        contrast_estimation = int(gray_img.std())
        print(yellow(f"\tmean: {brightness_estimation}\tcontrast: {contrast_estimation}"))

        if brightness_estimation < 25:
            try:
                gray_img, _, _ = automatic_brightness_and_contrast_gray(gray_img)
                brightness_estimation = int(cv2.mean(gray_img)[0])
                contrast_estimation = int(gray_img.std())
                print(p_orange(f"\tcorrected, mean: {brightness_estimation}\tcontrast: {contrast_estimation}"))
            except:
                print(p_orange(f"Warning:cannot apply automatic brightness&contrast"))
                shot_contours.append([0, 0, gray_img.shape[1], gray_img.shape[0]])
                continue
        _, gray_img = cv2.threshold(gray_img, threshold_min, 255, cv2.THRESH_BINARY)

        # show_image(gray_img, f"{i}")

        gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_OPEN, morph_kernel)
        gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_CLOSE, morph_kernel)

        if erode_kernel_radius != 0:
            gray_img = cv2.erode(gray_img, erode_kernel, iterations=erode_iterations)

        # show_image(gray_img, f"{i}")

        if debug:
            img_debug = cv2.cvtColor(gray_img.copy(), cv2.COLOR_GRAY2BGR)


        contours, hierarchy  = cv2.findContours(gray_img,
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
        outer_contour = None
        for hierarchy_values, contour in zip(hierarchy[0], contours):
            if hierarchy_values[0] == -1 and hierarchy_values[3] == -1:
                # shot_contours.append(cv2.boundingRect(contour))
                outer_contour = contour

                if False:
                    img_debug = cv2.cvtColor(gray_img.copy(), cv2.COLOR_GRAY2BGR)
                    x,y,w,h = cv2.boundingRect(contour)
                    cv2.rectangle(img_debug,
                        (x, y ),
                        (x + w , y + h),
                        (0, 0, 255), 1)
                    cv2.putText(img_debug,
                        f"{hierarchy_values}",
                        (x, y+10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255,30,12), 2)
                    show_image(img_debug, f"{i}")


                break


        # if debug:
        #     print("hierarchy")
        #     pprint(hierarchy)
        #     print("contours")
        #     pprint(contours)
        # print("outer contour")
        # pprint(outer_contour)

        # area = cv2.contourArea(outer_contour)
        epsilon = 0.1 * cv2.arcLength(outer_contour, True)
        polygon = cv2.approxPolyDP(outer_contour, epsilon, True)

        if debug:
            cv2.drawContours(img_debug, [polygon], -1, (0, 255, 0), 1)
            cv2.imwrite("mask.png", img_debug)
            show_image(img_debug, f"{i}")

        if polygon.shape[0] < 4:
            print(p_orange(f"Polygon not found"))
            print(print_darkgrey(f"\tshape:{polygon.shape}"))
            # print("hierarchy")
            # pprint(hierarchy)
            # print("contours")
            # pprint(contours)

            img_debug = cv2.cvtColor(gray_img.copy(), cv2.COLOR_GRAY2BGR)
            if True:
                # show all points
                contour = outer_contour.reshape(len(outer_contour),2)
                for (_x, _y) in contour:
                    cv2.rectangle(img_debug, (_x-1, _y-1), (_x+1, _y+1), (0,255,0), 1)
                show_image(img_debug, f"{i}")

            if False:
                # Show all contours
                for hierarchy_values, contour in zip(hierarchy[0], contours):
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(img_debug,
                        (x, y ), (x + w , y + h),
                        (0, 0, 255), 1)
                    cv2.putText(img_debug,
                        f"{hierarchy_values}",
                        (x, y+10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255,30,12), 2)
                show_image(img_debug, f"{i}")

        contour = polygon.reshape(len(polygon), 2)
        x0, x1 = __get_coordinates(contour[:, 0:1])
        y0, y1 = __get_coordinates(contour[:, 1:])
        if verbose:
            print(f"rect: x0, y0, x1, y1: [{x0}, {y0}, {x1}, {y1}]")

        if debug:
            cv2.rectangle(img_debug, (x0 +1, y1+1), (x1-1, y0-1), (0,0,255), 2)
            cv2.imwrite("mask_final.png", img_debug)
            show_image(img_debug, f"{i}")

        shot_contours.append([x0+1, y0+1, x1-1, y1-1])



    if len(shot_contours) == 0:
        print(red("Error: cannot find contour for this shot"))
        return ([0]*4, (w_img, h_img))

    elif len(shot_contours) < len(images):
        print(p_orange(f"Warning: found {len(shot_contours)}/{len(images)}"))

    if verbose:
        print(lightcyan("all images parsed, shot_contours:"))
        pprint(shot_contours)

    # Find the minimum area
    l, t = np.max(shot_contours, axis=0)[:2] - border_size + additional_crop
    rectangle_x1_y1 = np.min(shot_contours, axis=0)[2:] - border_size - additional_crop
    b = h_img - rectangle_x1_y1[1]
    r = w_img - rectangle_x1_y1[0]
    w, h = (w_img - (r + l), h_img - (t+b))

    if verbose:
        print(f"crop: t, b, l, r: [{t}, {b}, {l}, {r}] -> {w}x{h}")


    return ((t, b, l, r), (w, h))






def __archive():


        sys.exit()
# rect: x0, y0, x1, y1: [41, 1174, 1425, 21]
# 0.2 array([[  41,   21],
#        [1425, 1174]], dtype=int32)
# 0.1 array([[  41,   21],
#        [1425, 1174]], dtype=int32)

        # pprint(hierarchy)
        # pprint(contours)
        if False:
            hierarchy = hierarchy[0]
            for component in zip(contours, hierarchy):
                currentContour = component[0]
                currentHierarchy = component[1]
                x,y,w,h = cv2.boundingRect(currentContour)

                cv2.rectangle(img_debug,
                    (x, y ),
                    (x + w , y + h),
                    (0, 0, 255), 2)

                # Has inner contours which means it is unfilled
                if currentHierarchy[3] > 0:
                    cv2.putText(img_debug, 'Unfilled', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (36,255,12), 1)
                # No child which means it is filled
                elif currentHierarchy[2] == -1:
                    cv2.putText(img_debug, 'Filled', (x,y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (36,255,12), 1)

        # show_image(img_debug, f"{i}")
        # sys.exit()

        img_debug = cv2.cvtColor(gray_img.copy(), cv2.COLOR_GRAY2BGR)
        outer_contour = None
        for hierarchy_values, contour in zip(hierarchy[0], contours):

            # red
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(img_debug,
                (x + additional_crop, y +additional_crop ),
                (x + w -additional_crop , y + h -additional_crop ),
                (0, 0, 255), 1)


            # Blue
            box = np.int0(cv2.boxPoints(cv2.minAreaRect(contour)))
            cv2.drawContours(img_debug,[box],0,(255,0,0),1)
            print(box.shape)
            print(box)

            x_coords = box[:, 0:1]
            print(f"x_coords")
            print(x_coords)
            x_min = min(box[0, :])
            x_max = max(box[0, :])
            x_threshold = int((x_max - x_min)/2)
            print(f"x_threshold: {x_threshold}")
            x_mins = x_coords[x_coords < x_threshold]
            x_maxs = x_coords[x_coords > x_threshold]
            x0 = max(x_mins)
            x1 = min(x_maxs)



            y_coords = box[:, 1:]
            print(f"y_coords")
            print(y_coords)
            y_min = min(box[:, 1:])
            y_max = max(box[:, 1:])
            y_threshold = int((y_max - y_min)/2)
            print(f"y_threshold: {y_threshold}")
            y_mins = y_coords[y_coords < y_threshold]
            y_maxs = y_coords[y_coords > y_threshold]
            y1 = max(y_mins)
            y0 = min(y_maxs)

            # Blue
            # cv2.rectangle(img_debug,
            #     (x0, y0), (x1, y1),
            #     (255, 0, 0), 1)

            print(f"rect: x0, y0, x1, y1: [{x0}, {y0}, {x1}, {y1}]")

            # sys.exit()
            # min

            # Draw contour
            # cv2.drawContours(img_debug,[box],0,(0,0,255),2)

            # Draw contour
            # x, y, w, h = cv2.boxPoints(cv2.minAreaRect(contour))
            # cv2.rectangle(img_debug,
            #     (x + additional_crop, y +additional_crop ),
            #     (x + w -additional_crop , y + h -additional_crop ),
            #     (0, 0, 255), 1)

            # Draw points:
            # green
            contour = contour.reshape(len(contour),2)
            for (_x, _y) in contour:
                cv2.rectangle(img_debug, (_x-1, _y-1), (_x+1, _y+1), (0,255,0), 1)


            if hierarchy_values[0] == -1 and hierarchy_values[3] == -1:
                # shot_contours.append(cv2.boundingRect(contour))
                outer_contour = contour
                break
        cv2.imwrite("mask.png", img_debug)

        show_image(img_debug, f"{i}")




        if outer_contour is not None:
            # Get all the points of the contour
            contour = outer_contour.reshape(len(outer_contour),2)
            pprint(contour)

            x1, y1 = np.max(contour, axis=0)
            x0, y0 = np.min(contour, axis=0)

            # array([[  45,   25],
            #         [  45,   30],
            #         [  46,  129],
            #         [  45,  257],
            #         ...
            #         [ 210, 1176],
            #         [ 362, 1177],
            #         ...
            #         [1436,  178],
            #         [1437,  177],
            #         ...
            #         [ 224,   26],
            #         [ 223,   27]
            #         ...], dtype=int32)


            if verbose:
                print(f"{x0}, {y0}, {x1}, {y1}")
            cv2.rectangle(img_debug,
                (x0, y0),
                (x1, y1),
                (0, 255,0), 1)

            show_image(img_debug, f"{i}")

            # x0 += additional_crop
            # y0 += additional_crop
            # x1 -=  additional_crop
            # y1 -=  additional_crop

            if False:
                img_debug = bgr_img.copy()
                cv2.rectangle(img_debug, (x0, y1), (x1, y0), (0,255,0), 1)
                show_image(img_debug, "Is that rectangle ok?")

            #     shot_contours.append([x0, y0, x1, y1])

            percentage = 0.05

            h_grey, w_grey = gray_img.shape

            y_t_min = max(0, y0 - int(percentage * h_grey))
            y_t_max = y0+ int(percentage * h_grey)
            print(f"[{y_t_min}:{y_t_max}, {x1}:{x0}]")
            print(f"{gray_img.shape}")
            top_img = gray_img[y_t_min:y_t_max, x0:x1]
            top_img = cv2.flip(top_img, 0)
            top_img = cv2.bitwise_not(top_img)
            top_img = cv2.copyMakeBorder(top_img,
                top=2, bottom=2, left=2, right=2,
                borderType=cv2.BORDER_CONSTANT,
                value=[0]*3)
            contours, hierarchy  = cv2.findContours(top_img,
                cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            img_debug = cv2.cvtColor(top_img.copy(), cv2.COLOR_GRAY2BGR)
            for hierarchy_values, contour in zip(hierarchy[0], contours):
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(img_debug,
                    (x + additional_crop, y +additional_crop ),
                    (x + w -additional_crop , y + h -additional_crop ),
                    (0, 0, 255), 1)

                if hierarchy_values[0] == -1 and hierarchy_values[3] == -1:
                    outer_contour = contour
                    break
            show_image(img_debug, "Is that rectangle ok?")
            # contour = outer_contour.reshape(len(outer_contour),2)
            # x1_t, y1_t = np.max(contour, axis=0)
            # x0_t, y0_t = np.min(contour, axis=0)
            # cv2.rectangle(img_debug, (x0_t, y0_t), (x1_t, y1_t), (0,255,0), 1)

            # shot_contours.append([x0, y0, x1, y1])


            # show_image(img_debug, f"{i}")


            # show_image(top_img, 'top_img')




            sys.exit()


        if False:
            rect = []
            for i in range(len(contour)):
                x1, y1 = contour[i]
                for j in range(len(contour)):
                    x2, y2 = contour[j]
                    area = abs(y2-y1)*abs(x2-x1)
                    rect.append(((x1,y1), (x2,y2), area))

            # the first rect of all_rect has the biggest area, so it's the best solution if he fits in the picture
            all_rect = sorted(rect, key = lambda x : x[2], reverse = True)


            # if the list is not empty
            if all_rect:

                best_rect_found = False
                index_rect = 0
                nb_rect = len(all_rect)

                # we check if the rectangle is  a good solution
                while not best_rect_found and index_rect < nb_rect:

                    rect = all_rect[index_rect]
                    (x1, y1) = rect[0]
                    (x2, y2) = rect[1]

                    valid_rect = True

                    # we search a black area in the perimeter of the rectangle (vertical borders)
                    x = min(x1, x2)
                    while x <max(x1,x2)+1 and valid_rect:
                        if gray_img[y1,x] == 0 or gray_img[y2,x] == 0:
                            # if we find a black pixel, that means a part of the rectangle is black
                            # so we don't keep this rectangle
                            valid_rect = False
                        x+=1

                    y = min(y1, y2)
                    while y <max(y1,y2)+1 and valid_rect:
                        if gray_img[y,x1] == 0 or gray_img[y,x2] == 0:
                            valid_rect = False
                        y+=1

                    if valid_rect:
                        best_rect_found = True

                    index_rect+=1

                if best_rect_found:
                    img_debug = bgr_img.copy()
                    cv2.rectangle(img_debug, (x1,y1), (x2,y2), (0,255,0), 1)
                    show_image(img_debug, "Is that rectangle ok?")

                    # Finally, we crop the picture and store it
                    # result = input_picture[min(y1, y2):max(y1, y2), min(x1,x2):max(x1,x2)]
                    t = min(y1, y2)
                    l = min(x1,x2)
                    b = h_img - max(y1, y2)
                    r = w_img - min(x1,x2)

                    return ((t, b, l, r), (w_img - l -r), (h_img - t -b))
                else:
                    print("No rectangle fitting into the area")

            else:
                print("No rectangle found")

