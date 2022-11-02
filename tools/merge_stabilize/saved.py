
def process_single_frame(work_no, frame:dict, preview_options='stabilized'):
    now = time.time()
    # if work_no == -1:
    #     print("process_single_frame")
    # else:
    #     print("%d" % (work_no))
    # pprint(frame)

    # Foreground image (shall be denoised)
    # image_fgd = cv2.imread(frame['filepath'], cv2.IMREAD_COLOR)
    # image_fgd = frame['cache_fgd']
    image_fgd = pyvips.new_from_file(frame['filepath'])


    # To crop the image before stitching, use the forground image without stabilization
    if preview_options == 'fgd_crop_edition':
        return (work_no, image_fgd)

    # Apply stabilization if enabled before other modifications
    if frame['stabilize'] is not None:
        do_stabilize = True
    else:
        do_stabilize = False

    if preview_options in ['stabilized', 'fgd_cropped', 'stitching']:
        height_fgd, width_fgd, channel_count = image_fgd.shape

        # 1. Generate the translated image, add padding
        pad_w_l = 40
        pad_w_r = 20
        pad_h_t = 80
        pad_h_b = 40

        #   1.1. Add padding to the initial image, even if no stabilization
        width_stabilized = width_fgd + pad_w_l + pad_w_r
        height_stabilized = height_fgd + pad_h_t + pad_h_b
        image_fgd_with_borders = cv2.copyMakeBorder(image_fgd,
            pad_h_t, pad_h_b,
            pad_w_l, pad_w_r,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0])

        # print("image_fgd_with_borders: %dx%d" % (image_fgd_with_borders.shape[1], image_fgd_with_borders.shape[0]))

        if do_stabilize:
            #   1.2. Generate a stabilized image
            if False:
                transformation_matrix = np.float32([
                    [1, 0, 0],
                    [0, 1, frame['stabilize'][1]]
                ])
                img_stabilized = cv2.warpAffine(
                    image_fgd_with_borders,
                    transformation_matrix,
                    (width_stabilized, height_stabilized),
                    flags=cv2.INTER_LANCZOS4,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(0,0,0))
            else:
                if frame['stabilize'][1] >= 1:
                    # Add padding
                    dy = abs(int(frame['stabilize'][1]))

                    # image_fgd_with_borders_umat = cv2.UMat(image_fgd_with_borders)
                    # print(type(image_fgd_with_borders))
                    img_fgd_cropped = image_fgd_with_borders[
                        0:height_stabilized - dy,
                        0:width_stabilized
                    ]
                    img_stabilized = cv2.copyMakeBorder(img_fgd_cropped,
                        top=dy, bottom=0,
                        left=0, right=0,
                        borderType=cv2.BORDER_CONSTANT,
                        value=[0, 0, 0])

                elif frame['stabilize'][1] <= -1:
                    dy = abs(int(frame['stabilize'][1]))
                    # Remove
                    # image_fgd_with_borders_umat = cv2.UMat(image_fgd_with_borders)
                    # print(type(image_fgd_with_borders))
                    img_fgd_cropped = image_fgd_with_borders[
                        dy:height_stabilized,
                        0:width_stabilized
                    ]
                    img_stabilized = cv2.copyMakeBorder(img_fgd_cropped,
                        top = 0, bottom=dy,
                        left=0, right=0,
                        borderType=cv2.BORDER_CONSTANT,
                        value=[0, 0, 0])
                else:
                    img_stabilized = image_fgd_with_borders
        else:
            img_stabilized = image_fgd_with_borders

        # cv2.imwrite("test.png", img_stabilized)
        if preview_options == 'stabilized':
            print(1000*(time.time() - now))
            return (work_no, img_stabilized)

    if preview_options == 'fgd_cropped':
        # fgd_crop_list = frame['shot_stitching']['fgd_crop']
        # fgd_crop_x0 = fgd_crop_list[0]
        # fgd_crop_y0 = fgd_crop_list[1]
        # fgd_crop_w = width_fgd - (fgd_crop_list[2] + fgd_crop_x0)
        # fgd_crop_h = height_fgd - (fgd_crop_list[3] + fgd_crop_y0)

        # depends on each shot (defined by user -> use UI for this)
        crop_left = 25
        crop_right = 20
        crop_top = 10
        crop_bottom = 10

        dy_max = frame['delta_interval'][3]

        # Position and dimension for foreground ROI and cropped
        # with dx stabilization:
        # x0 = pad_w_l + dx_max + crop_left
        # x1 = width_fgd + pad_w_l + dx_max - crop_right

        # w/out dx stabilization:
        x0 = pad_w_l + crop_left
        x1 = width_fgd + pad_w_l - crop_right

        dy = 0
        if frame['stabilize'] is not None:
            dy = frame['stabilize'][1]
            if abs(dy) < dy_max:
                dy = int(dy_max)
            #     print("use dy rather than dy_min")
            #     y0 = pad_h_t + int(dy) + crop_top
            #     y1 = height_fgd + pad_h_t + int(dy) - crop_bottom
            # else:
            #     y0 = pad_h_t + int(dy_max) + crop_top
            #     y1 = height_fgd + pad_h_t + int(dy_max) - crop_bottom

        # else:
            # print("no stabilization for %d" % (frame_no))
        y0 = pad_h_t + int(dy) + crop_top
        y1 = pad_h_t + height_fgd + int(dy) - crop_top - crop_bottom

        # print("dimensions: (x0, x1)(y0, y1) = (%d;%d)(%d;%d)" % (x0, x1, y0, y1))

        img_fgd_cropped = img_stabilized[
            y0:y1,
            x0:x1
        ]

        #   2.2. Add padding to the stabilized, cropped image
        img_fgd_4_combine = cv2.copyMakeBorder(img_fgd_cropped,
            top=y0, bottom=height_stabilized - y1,
            left=x0, right=width_stabilized - x1,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0])

        # cv2.imwrite("test2.png", img_fgd_4_combine)
        img_fgd_4_combine = np.ascontiguousarray(img_fgd_4_combine, dtype=np.uint8)
        # print(img_fgd_4_combine.flags['C_CONTIGUOUS'])

        print(1000*(time.time() - now))
        return (work_no, img_fgd_4_combine.numpy())


    elif preview_options == 'stitching':
        image_bgd = cv2.imread(frame['filepath_bgd'], cv2.IMREAD_COLOR)

    if preview_options == 'stabilized':
        img = img_stabilized

    return (work_no, img)