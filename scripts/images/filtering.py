# -*- coding: utf-8 -*-
import sys
from copy import deepcopy
import cv2
import numpy as np

from skimage import data
from skimage.filters import unsharp_mask
from skimage.util import img_as_ubyte
from skimage.util import img_as_float
# from skimage.io import imshow, imread
# from skimage.color import rgb2yuv, rgb2hsv, rgb2gray, yuv2rgb, hsv2rgb
# from skimage.restoration import denoise_tv_bregman
from skimage.restoration import (calibrate_denoiser,
                                 denoise_wavelet,
                                 denoise_tv_chambolle,
                                 denoise_nl_means,
                                 denoise_bilateral,
                                 estimate_sigma)
# from functools import partial
from pprint import pprint
from skimage import color
from skimage import restoration

from parsers.parser_stitching import STICTHING_FGD_PAD
from utils.common import get_dimensions_from_crop_values


def filter_denoise(frame, img):
    # print("denoise: %s -> %s" % (frame['filepath']['upscale'], frame['filepath']['denoise']))
    if 'denoise' not in frame['filters']['opencv'].keys():
        print("Warning: no denoise filter defined")
        return None

    if frame['filters']['opencv']['denoise'] is not None:
        return filters_opencv(img, frame['filters']['opencv']['denoise'], multi=False)


    # elif frame['filters']['ffmpeg']['denoise'] is not None:
    #     print("Error: FFMPEG denoise filter shall be implemented before this function call")
    # else:
    #     print("warning: no denoise filter defined")
    return None


def filter_bgd(frame, img):
    # if 'bgd' in frame['filepath']:
    print("filter_bgd: apply RGB curve %s -> %s" % (frame['filepath']['denoise'], frame['filepath']['bgd']))
    return img


def filter_sharpen(frame, img):
    # print("sharpen: %s -> %s" % (frame['filepath']['stitching'], frame['filepath']['sharpen']))
    if frame['filters']['opencv']['sharpen'] is not None:
        imgTmp = filters_opencv(img, frame['filters']['opencv']['sharpen'], multi=False)
        return imgTmp
    # else:
    #     print("warning: no sharpen filter defined")
    return None


def filter_upscale(frame, img):
    # print("upscale: %s -> %s" % (frame['filepath']['pre_upscale'], frame['filepath']['upscale']))
    filter_array = frame['filters']['opencv']['upscale']
    if filter_array is not None:
        width = frame['dimensions']['upscale']['w']
        height = frame['dimensions']['upscale']['h']
        for i in range(len(filter_array)):
            filter_array[i] = filter_array[i].replace("height_upscale", "%d" % (height))
            filter_array[i] = filter_array[i].replace("width_upscale", "%d" % (width))
        imgTmp = filters_opencv(img, filter_array, multi=False)
        return imgTmp
    else:
        raise Exception("error: opencv: no upscale filter defined to generate %s" % (frame['filepath']['upscale']))
    return None




def filter_rgb(frame, img):
    # print("rgb: %s -> %s" % (frame['filepath']['sharpen'], frame['filepath']['rgb']))
    b, g, r = cv2.split(img)

    matrix_r = frame['curves']['lut']['r']
    matrix_g = frame['curves']['lut']['g']
    matrix_b = frame['curves']['lut']['b']

    rrp = matrix_r[r.flat].reshape(r.shape)
    ggp = matrix_g[g.flat].reshape(g.shape)
    bbp = matrix_b[b.flat].reshape(b.shape)

    img_rgb = cv2.merge((bbp, ggp, rrp))
    return img_rgb


def stabilize_image(frame, img):
    img_stabilized = img
    if frame['stabilization']['dx_dy'] is not None:
        if frame['stabilization']['dx_dy'][1] >= 1:
            # Add padding
            dy = abs(int(frame['stabilization']['dx_dy'][1]))

            img_tmp = img[
                0:img.shape[0] - dy,
                0:img.shape[1]
            ]
            img_stabilized = cv2.copyMakeBorder(img_tmp,
                top=dy, bottom=0,
                left=0, right=0,
                borderType=cv2.BORDER_CONSTANT,
                value=[0, 0, 0])
        elif frame['stabilization']['dx_dy'][1] <= -1:
            dy = abs(int(frame['stabilization']['dx_dy'][1]))
            # Remove
            img_tmp = img[
                dy:img.shape[0],
                0:img.shape[1]
            ]
            img_stabilized = cv2.copyMakeBorder(img_tmp,
                top = 0, bottom=dy,
                left=0, right=0,
                borderType=cv2.BORDER_CONSTANT,
                value=[0, 0, 0])

    return img_stabilized


def filter_geometry(frame, img):
    # print("crop and resize: %s -> %s" % (frame['filepath']['sharpen'], frame['filepath']['geometry']))
    h, w, c = img.shape

    # print("------------------")
    # pprint(frame['geometry'])
    # print(img.shape)
    if (frame['geometry'] is None
    or (frame['geometry']['part'] is None and frame['geometry']['custom'] is None)):
        print("Error: no geometry defined, cannot modify the image")
        return None


    # Crop
    if frame['geometry'] is not None:
        c_t_p, c_b_p, c_l_p, c_r_p, c_w_p, c_h_p = get_dimensions_from_crop_values(w, h, frame['geometry']['part']['crop'])
        if ('custom' in frame['geometry'].keys()
            and frame['geometry']['custom'] is not None):
            # Use the customized geometry
            # print("use the customized geometry")
            c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w, h, frame['geometry']['custom']['crop'])
        else:
            # Use the part geometry
            # print:("use the part geometry")
            c_t, c_b, c_l, c_r, c_w, c_h = get_dimensions_from_crop_values(w, h, frame['geometry']['part']['crop'])
            # print("\t-> use the part geometry %d:%d:%d:%d  %dx%d" % (c_t, c_b, c_l, c_r, c_w, c_h))

        # Crop the image
        img = np.ascontiguousarray(img[c_t:h-c_b, c_l:w-c_r], dtype=np.uint8)

    # Final width and height
    w_final = frame['dimensions']['final']['w']
    h_final = frame['dimensions']['final']['h']

    # Calculate resized width for both part and (part or custom)
    w_p_tmp = int((c_w_p * h_final) / float(c_h_p))
    w_tmp = int((c_w * h_final) / float(c_h))
    # print("cropped image: ", img.shape)
    # pprint("w_p_tmp=%d, w_tmp=%d" % (w_p_tmp, w_tmp))
    # pprint("h_final=%d" % (h_final))

    # Resize
    img_resized = cv2.resize(img,
        (w_tmp, h_final),
        interpolation=cv2.INTER_LANCZOS4)
    # print("img_resized before adjustments: ", img_resized.shape)

    # Verify custom vs part cropped and resized image
    if w_tmp != w_p_tmp:
        # This is a custom geometry, width shall be the same as the part's one
        # It is done AFTER resizing because the resize may be different:
        #   i.e. when keep_ratio is disabled (custom width)
        if w_tmp > w_p_tmp:
            # Crop the image
            # Calculate the position of the left crop of the part after resizing
            c_l_p_resized = int(((c_l_p) * h_final) / float(c_h_p))
            c_l_resized = int(((c_l) * h_final) / float(c_h))
            x0 = c_l_resized - c_l_p_resized
            x1 = w_p_tmp + x0
            # print("crop the image: x0=%d, x1=%d, (w_tmp + x0)=%d" % (x0, x1, w_tmp+x0))
            if x1 > w_tmp:
                # Crop is too big on the left
                # print("crop is too big")
                x0 = w_tmp - w_p_tmp
                x1 = w_tmp
            # print("crop the image: c_l_p_resized=%d, c_l_resized=%d, x0=%d, x1=%d -> new resized width=%d" % (
                # c_l_p_resized, c_l_resized, x0, x1, x1 - x0))
            img_resized_final = np.ascontiguousarray(img_resized[0:h_final,  x0:x1,])
        elif w_p_tmp > w_tmp:
            # Add RED padding, for debug
            print("Error: custom geometry is incorrect")
            raise Exception("Error: custom geometry is incorrect")
            # TODO: exit?
            pad_left = int((w_p_tmp - w_tmp)/2)
            pad_right = w_p_tmp - w_tmp - pad_left
            img_resized_final = np.ascontiguousarray(cv2.copyMakeBorder(img_resized, 0, 0, pad_left, pad_right,
                cv2.BORDER_CONSTANT, value=[255, 0, 0]))
    else:
        img_resized_final = img_resized

    # print("img_resized after adjustments: ", img_resized_final.shape)
    # print("   w_resized should be: %s" % (w_p_tmp))

    # Add padding to the cropped & resized image
    pad_left = int(((w_final - w_p_tmp) / 2) + 0.5)
    pad_right = w_final - (w_p_tmp + pad_left)
    img_finalized = cv2.copyMakeBorder(img_resized_final, 0, 0, pad_left, pad_right,
        cv2.BORDER_CONSTANT, value=[0, 0, 0])

    # print("img_finalized: ", img_finalized.shape)
    # sys.exit()

    return img_finalized



def filter_richardson_lucy(img, psf=None, num_iter=30):
    if psf is None:
        psf = np.ones((5, 5)) / 25
    # data = convolve2d(img, psf, 'auto')
    # tmp = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
    # tmp2 = img_as_float(tmp)
    tmp = restoration.richardson_lucy(img, psf)
    img_out = img_as_ubyte(tmp)
    return img_out


def filter_nlmeans(img):
    # psf = np.ones((5, 5)) / 25
    # tmp = restoration.wiener(img,psf,1100)

    # sigma_est = estimate_sigma(img, channel_axis=-1, average_sigmas=True)
    # tmp = denoise_wavelet(img, channel_axis=-1)

    sigma = 0.05
    tmp = restoration.denoise_nl_means(img,
        3, 3, 0.2,
        fast_mode=True,
        channel_axis=-1,
        sigma=sigma)
    img_out = img_as_ubyte(tmp)
    return img_out


def filters_bilateral_sk(img, sigma_color, sigma_spatial):
    # graySrc = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # tmp = img_as_float(img)
    tmp = denoise_bilateral(img,
        sigma_color=sigma_color,
        sigma_spatial=sigma_spatial,
        channel_axis=-1)
    img_out = img_as_ubyte(tmp)
    return img_out


def filter_brightness_contrast(input_img, brightness = 255, contrast = 127):
    brightness = map(brightness, 0, 510, -255, 255)
    contrast = map(contrast, 0, 254, -127, 127)
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    if contrast != 0:
        f = float(131 * (contrast + 127)) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
    # cv2.putText(buf,'B:{},C:{}'.format(brightness,contrast),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return buf



def filters_scale_opencv(image, width, height, interpolation):
    # print("upscale image to %dx%d, inter=%s" % (width, height, interpolation))
    if interpolation == 'bicubic':
        cv2_interpolation = cv2.INTER_CUBIC
    else:
        cv2_interpolation = cv2.INTER_LANCZOS4
    return cv2.resize(image, (width, height), interpolation=cv2_interpolation)



def mco_unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    # For details on unsharp masking, see:
    # https://en.wikipedia.org/wiki/Unsharp_masking
    # https://homepages.inf.ed.ac.uk/rbf/HIPR2/unsharp.htm
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened



def map(x, in_min, in_max, out_min, out_max):
    return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)


def filters_brightnessAndContrast(input_img, brightness = 255, contrast = 127):
    brightness = map(brightness, 0, 510, -255, 255)
    contrast = map(contrast, 0, 254, -127, 127)
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    if contrast != 0:
        f = float(131 * (contrast + 127)) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)
    # cv2.putText(buf,'B:{},C:{}'.format(brightness,contrast),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return buf



def filters_opencv(images, filters, multi=True):
    if not multi:
        if type(images) is list:
            image = images[0]
        else:
            image = images

    for f in filters:
        if f == '':
            continue
        args = f.split('=')
        function = args[0]
        args = args[1].split(':')

        if function == 'fastNlMeansDenoisingColored':
            image = filters_fastNlMeansDenoisingColored(image,
                h=int(args[0]),
                hColor=int(args[1]),
                templateWindowSize=int(args[2]),
                searchWindowSize=int(args[3]))

        elif function == 'fastNlMeansDenoisingColoredMulti':
            if not multi:
                print("Error, multiples/single images in filters_opencv")
                sys.exit()
            image = filters_fastNlMeansDenoisingColoredMulti(images,
                imgToDenoiseIndex=1,
                temporalWindowSize=3,
                h=int(args[0]),
                hColor=int(args[1]),
                templateWindowSize=int(args[2]),
                searchWindowSize=int(args[3]))

        elif function == 'gaussianBlur':
            image = filters_gaussianBlur(image,
                radius=int(args[0]),
                sigma=float(args[1]))

        elif function == 'unsharp_mask':
            image = filters_unsharp_mask(image,
                radius=int(args[0]),
                amount=float(args[1]))

        elif function == 'bilateralFilter':
            image = filters_bilateralFilter(image,
                diameter=int(args[0]),
                sigmaColor=float(args[1]),
                sigmaSpace=float(args[2]))

        elif function == 'bilateral_sk':
            image = filters_bilateral_sk(image,
                sigma_color=float(args[0]),
                sigma_spatial=float(args[1]))

        elif function == 'morphologyEx':
            image = filters_morphologyEx(image,
                type=args[0],
                radius=int(args[1]),
                iterations=int(args[2]))

        elif function == 'dilate':
            image = filters_dilate(image,
                radius=int(args[0]))

        elif function == 'erode':
            image = filters_erode(image,
                radius=int(args[0]))

        elif function == 'addGaussNoise':
            image = filters_addGaussNoise(image,
                mean=float(args[0]),
                var=float(args[1]),
                sigma=float(args[2]))

        elif function == 'brightness_contrast':
            image = filter_brightness_contrast(image,
                brightness=int(args[0]),
                contrast=int(args[1]))

        elif function == 'richardson_lucy':
            image = filter_richardson_lucy(image,
                num_iter=int(args[0]))

        elif function =='nl_means':
            image = filter_nlmeans(image)
        # elif function == 'denoise_tv_bregman':
        #     image = filters_denoise_tv_bregman(image,
        #         weight=float(args[0]),
        #         eps=float(args[1]),
        #         max_iter=int(args[2]))

        # elif function == 'wavelet':
        #     image = filters_wavelet(image)

        elif function == 'bm3d':
            image = filters_bm3d(image,
                sigma=float(args[0]))

        elif function == 'scale':
            image = filters_scale_opencv(image,
                width=int(args[0]),
                height=int(args[1]),
                interpolation=args[2])

    return image


# def filters_bm3d(image, sigma):
#     tmp = img_as_float(image)
#     tmp2 = bm3d.bm3d_rgb(tmp, sigma)
#     return img_as_ubyte(tmp2)



# def filters_wavelet(image):
#     tmp = img_as_float(image)

#     _denoise_wavelet = partial(denoise_wavelet, rescale_sigma=True)
#     parameter_ranges = {'sigma': np.arange(0.1, 0.3, 0.02),
#                         'wavelet': ['db1', 'db2'],
#                         'convert2ycbcr': [True, False],
#                         'multichannel': [True]}

#     # Calibrate denoiser
#     calibrated_denoiser = calibrate_denoiser(tmp,
#                                             _denoise_wavelet,
#                                             denoise_parameters=parameter_ranges
#                                             )

#     # Denoised image using calibrated denoiser
#     tmp = calibrated_denoiser(tmp)
#     tmp = np.clip(tmp, 0.0, 1.0)
#     return img_as_ubyte(tmp)




# def filters_denoise_tv_bregman(image, weight, eps, max_iter):
#     tmp = img_as_float(image)
#     tmp = denoise_tv_bregman(tmp,
#         weight=weight,
#         max_iter=max_iter,
#         eps=eps,
#         isotropic=True,
#         multichannel=True)
#     tmp = np.clip(tmp, 0.0, 1.0)
#     return img_as_ubyte(tmp)






def filters_fastNlMeansDenoisingColoredMulti(images, imgToDenoiseIndex, temporalWindowSize, h, hColor, templateWindowSize, searchWindowSize):
    return cv2.fastNlMeansDenoisingColoredMulti(
                                srcImgs=images,
                                imgToDenoiseIndex=imgToDenoiseIndex,
                                temporalWindowSize=temporalWindowSize,
                                h=h,
                                hColor=hColor,
                                templateWindowSize=templateWindowSize,
                                searchWindowSize=searchWindowSize)


def filters_fastNlMeansDenoisingColored(image, h, hColor, templateWindowSize, searchWindowSize):
    return cv2.fastNlMeansDenoisingColored(
                                image,
                                None,
                                h,
                                hColor,
                                templateWindowSize,
                                searchWindowSize)


def filters_unsharp_mask(image, radius, amount):
    if False:
        tmp = img_as_float(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
        h = tmp[:, :, 0]
        s = tmp[:, :, 1]
        v = tmp[:, :, 2]
        v1 = unsharp_mask(v,
            radius,
            amount,
            preserve_range=False,
            channel_axis=3)
        zipped = np.dstack((h, s, v1))
        return cv2.cvtColor(img_as_ubyte(zipped), cv2.COLOR_HSV2BGR)
    else:
        tmp = img_as_float(image)
        tmp = unsharp_mask(tmp,
            radius,
            amount,
            preserve_range=False,
            channel_axis=2)
        return img_as_ubyte(tmp)


def  filters_morphologyEx(image, type, radius, iterations):
    if type == 'MORPH_RECT':
        kernelType = cv2.MORPH_RECT
    elif type == 'MORPH_ELLIPSE':
        kernelType = cv2.MORPH_ELLIPSE
    else:
        print("Error: unrecognized kernel type")
        sys.exit()

    kernel = cv2.getStructuringElement(kernelType, (radius, radius))
    return cv2.morphologyEx(
        image,
        cv2.MORPH_OPEN,
        kernel,
        iterations)


def filters_bilateralFilter(img, diameter, sigmaColor, sigmaSpace):
    return cv2.bilateralFilter(img, diameter, sigmaColor, sigmaSpace)

def filters_gaussianBlur(image, radius, sigma):
    return cv2.GaussianBlur(image, (radius, radius), sigma)

def filters_dilate(image, radius):
    kernel = np.ones((radius, radius), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)

def filters_erode(image, radius):
    kernel = np.ones((radius, radius), np.uint8)
    return cv2.erode(image, kernel, iterations=1)

# def multi_convolver(image, kernel, iterations):
#     for i in range(iterations):
#         image = convolve2d(image, kernel, 'same', boundary = 'fill',
#                            fillvalue = 0)
#     return image

# def convolver_rgb(image, kernel, iterations = 1):
#     convolved_image_r = multi_convolver(image[:,:,0], kernel, iterations)
#     convolved_image_g = multi_convolver(image[:,:,1], kernel, iterations)
#     convolved_image_b  = multi_convolver(image[:,:,2], kernel, iterations)

#     reformed_image = np.dstack((np.rint(abs(convolved_image_r)),
#                                 np.rint(abs(convolved_image_g)),
#                                 np.rint(abs(convolved_image_b)))) / 255


#     return np.array(reformed_image).astype(np.uint8)

def filters_addGaussNoise(image, mean, var, sigma):
    gaussian = np.random.normal(mean, var**sigma, image.shape).astype(np.float)
    gaussian_img = gaussian + img_as_float(image)
    gaussian_img = np.clip(gaussian_img, 0.0, 1.0)
    return img_as_ubyte(gaussian_img)


def gaussian_kernel(size, size_y=None):
    size = int(size)
    if not size_y:
        size_y = size
    else:
        size_y = int(size_y)
    x, y = np.mgrid[-size:size+1, -size_y:size_y+1]
    g = np.exp(-(x**2/float(size)+y**2/float(size_y)))
    return g / g.sum()


def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)
	# return the edged image
	return edged

def strokeEdges(src, dst, blurKsize = 7, edgeKsize = 5):
   if blurKsize >= 3:
       blurredSrc = cv2.medianBlur(src, blurKsize)
       graySrc = cv2.cvtColor(blurredSrc, cv2.COLOR_BGR2GRAY)
   else:
       graySrc = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
   cv2.Laplacian(graySrc, cv2.CV_8U, graySrc, ksize = edgeKsize)
   normalizedInverseAlpha = (1.0 / 255) * (255 - graySrc)
   channels = cv2.split(src)
   for channel in channels:
       channel[:] = channel * normalizedInverseAlpha
   cv2.merge(channels, dst)






def calculate_stitching_values(frame:dict):
    """ Calculate homography values for stitching.
    """
    print("calculate_stitching_values %d" % (frame['index']), flush=True)
    # now = time.time()

    filepath_bgd = frame['filepath_bgd']
    img_bgd = cv2.imread(filepath_bgd, cv2.IMREAD_COLOR)

    stitching_parameters = frame['stitching']['parameters']

    # ROI used for stitching
    roi_top, roi_bottom, roi_left, roi_right = stitching_parameters['roi']
    height_fgd, width_fgd, channels_fgd = frame['cache_fgd'].shape
    y0 = roi_top
    y1 = height_fgd - roi_bottom
    x0 = roi_left
    x1 = width_fgd - roi_right

    if True:
        # Sharpen images
        radius = stitching_parameters['sharpen'][0]
        amount = stitching_parameters['sharpen'][1]

        tmp1 = img_as_float(cv2.cvtColor(frame['cache_fgd'], cv2.COLOR_RGB2GRAY))
        tmp2 = unsharp_mask(tmp1,
            radius=radius,
            amount=amount,
            preserve_range=False)
        img_fgd_gray = img_as_ubyte(tmp2)


        tmp3 = img_as_float(cv2.cvtColor(img_bgd, cv2.COLOR_RGB2GRAY))
        tmp4 = unsharp_mask(tmp3,
            radius=radius,
            amount=amount,
            preserve_range=False)
        img_bgd_gray = img_as_ubyte(tmp4)
    else:
        img_fgd_gray = cv2.cvtColor(frame['cache_fgd'], cv2.COLOR_RGB2GRAY)
        img_bgd_gray = cv2.cvtColor(img_bgd, cv2.COLOR_RGB2GRAY)


    if (roi_top != 0 or roi_bottom != 0
    or roi_left != 0 or roi_right != 0):
        print("use cropped roi")
        img_fgd_gray_cropped = img_fgd_gray[y0:y1, x0:x1]
    else:
        img_fgd_gray_cropped = img_fgd_gray

    img_fgd_borders_gray = cv2.copyMakeBorder(img_fgd_gray_cropped,
        top=STICTHING_FGD_PAD[0] + roi_top,
        bottom=STICTHING_FGD_PAD[1] + roi_bottom,
        left=STICTHING_FGD_PAD[2] + roi_left,
        right=STICTHING_FGD_PAD[3] + roi_right,
        borderType=cv2.BORDER_CONSTANT,
        value=[0, 0, 0])

    # parameters from file
    feature_extractor = stitching_parameters['extractor']
    feature_matching = stitching_parameters['matching']

    # detect and describe points
    kps_fgd, features_fgd = detectAndDescribe(img_fgd_borders_gray, method=feature_extractor)
    kps_bgd, features_bgd = detectAndDescribe(img_bgd_gray, method=feature_extractor)

    # find matching points between fgd and bgd
    if feature_matching == 'bf':
        matches = matchKeyPointsBF(features_bgd, features_fgd, method=feature_extractor)
    elif feature_matching == 'knn':
        matches = matchKeyPointsKNN(features_bgd, features_fgd, ratio=stitching_parameters['knn_ratio'], method=feature_extractor)

    # Calculate homography matrix
    result = getHomography(
        kps_bgd, kps_fgd,
        features_bgd, features_fgd,
        matches,
        method_str=stitching_parameters['method'],
        ransacReprojThresh=stitching_parameters['reproj_threshold'])
    if result is None:
        print("Error!")
    (matches, M, status) = result

    return (frame['index'], M)





def detectAndDescribe(image, method=None):
    """
    Compute key points and feature descriptors using an specific method
    """

    assert method is not None, "You need to define a feature detection method. Values are: 'sift', 'surf'"

    # detect and extract features from the image
    if method == 'sift':
        descriptor = cv2.SIFT_create()
    elif method == 'surf':
        descriptor = cv2.xfeatures2d.SURF_create()
    elif method == 'brisk':
        descriptor = cv2.BRISK_create()
    elif method == 'orb':
        descriptor = cv2.ORB_create()

    # get keypoints and descriptors
    (kps, features) = descriptor.detectAndCompute(image, None)

    return (kps, features)




def createMatcher(method,crossCheck):
    "Create and return a Matcher Object"

    if method == 'sift' or method == 'surf':
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
        # bf = cv2.BFMatcher(cv2.NORM_L2SQR, crossCheck=crossCheck)
    elif method == 'orb' or method == 'brisk':
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)
    return bf


def matchKeyPointsBF(featuresA, featuresB, method):
    bf = createMatcher(method, crossCheck=True)

    # Match descriptors.
    best_matches = bf.match(featuresA,featuresB)

    # Sort the features in order of distance.
    # The points with small distance (more similarity) are ordered first in the vector
    rawMatches = sorted(best_matches, key = lambda x:x.distance)
    # print("Raw matches (Brute force):", len(rawMatches))
    return rawMatches


def matchKeyPointsKNN(featuresA, featuresB, ratio, method):
    bf = createMatcher(method, crossCheck=False)
    # compute the raw matches and initialize the list of actual matches
    rawMatches = bf.knnMatch(featuresA, featuresB, 2)
    print("Raw matches (knn):", len(rawMatches))
    matches = []

    # loop over the raw matches
    for m,n in rawMatches:
        # ensure the distance is within a certain ratio of each
        # other (i.e. Lowe's ratio test)
        if m.distance < n.distance * ratio:
            matches.append(m)
    return matches





# def findHomography(srcPoints, dstPoints, method=None, ransacReprojThreshold=None, mask=None, maxIters=None, confidence=None, /) -> retval, mask
# findHomography(srcPoints, dstPoints[, method[, ransacReprojThreshold[, mask[, maxIters[, confidence]]]]]) -> retval, mask
# .   @brief Finds a perspective transformation between two planes.
# .
# .   @param srcPoints Coordinates of the points in the original plane, a matrix of the type CV_32FC2
# .   or vector\<Point2f\> .
# .   @param dstPoints Coordinates of the points in the target plane, a matrix of the type CV_32FC2 or
# .   a vector\<Point2f\> .
# .   @param method Method used to compute a homography matrix. The following methods are possible:
# .   -   **0** - a regular method using all the points, i.e., the least squares method
# .   -   @ref RANSAC - RANSAC-based robust method
# .   -   @ref LMEDS - Least-Median robust method
# .   -   @ref RHO - PROSAC-based robust method
# .   @param ransacReprojThreshold Maximum allowed reprojection error to treat a point pair as an inlier
# .   (used in the RANSAC and RHO methods only). That is, if
# .   \f[\| \texttt{dstPoints} _i -  \texttt{convertPointsHomogeneous} ( \texttt{H} * \texttt{srcPoints} _i) \|_2  >  \texttt{ransacReprojThreshold}\f]
# .   then the point \f$i\f$ is considered as an outlier. If srcPoints and dstPoints are measured in pixels,
# .   it usually makes sense to set this parameter somewhere in the range of 1 to 10.
# .   @param mask Optional output mask set by a robust method ( RANSAC or LMeDS ). Note that the input
# .   mask values are ignored.
# .   @param maxIters The maximum number of RANSAC iterations.
# .   @param confidence Confidence level, between 0 and 1.
# .
# .   The function finds and returns the perspective transformation \f$H\f$ between the source and the
# .   destination planes:
# .
# .   \f[s_i  \vecthree{x'_i}{y'_i}{1} \sim H  \vecthree{x_i}{y_i}{1}\f]
# .
# .   so that the back-projection error
# .
# .   \f[\sum _i \left ( x'_i- \frac{h_{11} x_i + h_{12} y_i + h_{13}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2+ \left ( y'_i- \frac{h_{21} x_i + h_{22} y_i + h_{23}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2\f]
# .
# .   is minimized. If the parameter method is set to the default value 0, the function uses all the point
# .   pairs to compute an initial homography estimate with a simple least-squares scheme.
# .
# .   However, if not all of the point pairs ( \f$srcPoints_i\f$, \f$dstPoints_i\f$ ) fit the rigid perspective
# .   transformation (that is, there are some outliers), this initial estimate will be poor. In this case,
# .   you can use one of the three robust methods. The methods RANSAC, LMeDS and RHO try many different
# .   random subsets of the corresponding point pairs (of four pairs each, collinear pairs are discarded), estimate the homography matrix
# .   using this subset and a simple least-squares algorithm, and then compute the quality/goodness of the
# .   computed homography (which is the number of inliers for RANSAC or the least median re-projection error for
# .   LMeDS). The best subset is then used to produce the initial estimate of the homography matrix and
# .   the mask of inliers/outliers.
# .
# .   Regardless of the method, robust or not, the computed homography matrix is refined further (using
# .   inliers only in case of a robust method) with the Levenberg-Marquardt method to reduce the
# .   re-projection error even more.
# .
# .   The methods RANSAC and RHO can handle practically any ratio of outliers but need a threshold to
# .   distinguish inliers from outliers. The method LMeDS does not need any threshold but it works
# .   correctly only when there are more than 50% of inliers. Finally, if there are no outliers and the
# .   noise is rather small, use the default method (method=0).
# .
# .   The function is used to find initial intrinsic and extrinsic matrices. Homography matrix is
# .   determined up to a scale. Thus, it is normalized so that \f$h_{33}=1\f$. Note that whenever an \f$H\f$ matrix
# .   cannot be estimated, an empty one will be returned.
# .
# .   @sa
# .   getAffineTransform, estimateAffine2D, estimateAffinePartial2D, getPerspectiveTransform, warpPerspective,
# .   perspectiveTransform
def getHomography(kpsA, kpsB, featuresA, featuresB, matches, method_str='RHO', ransacReprojThresh=None):
    # convert the keypoints to numpy arrays
    kpsA = np.float32([kp.pt for kp in kpsA])
    kpsB = np.float32([kp.pt for kp in kpsB])

    if len(matches) > 4:

        # construct the two sets of points
        ptsA = np.float32([kpsA[m.queryIdx] for m in matches])
        ptsB = np.float32([kpsB[m.trainIdx] for m in matches])

        if method_str.upper() == 'RHO':
            method = cv2.RHO
        elif method_str.upper() == 'RANSAC':
            method = cv2.RANSAC
        elif method_str.upper() == 'LMEDS':
            method = cv2.LMEDS

        # estimate the homography between the sets of points
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, reprojThresh)
        # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.LMEDS, reprojThresh)
        (H, status) = cv2.findHomography(ptsA, ptsB, method, ransacReprojThresh)

        return (matches, H, status)
    else:
        return None
