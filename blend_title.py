from pprint import pprint
import signal
from processing.effects import blend_images
from utils.images_io import load_image_fp32, write_image
import numpy as np

from utils.np_dtypes import np_to_float32, np_to_uint8


def main():
    text: np.ndarray = load_image_fp32(filepath="~/mco/inputs/g_fin_01.png")
    background: np.ndarray = load_image_fp32(filepath="~/mco/inputs/j_ep99__j__c37d117_1080p_03426.png")


    # merged: np.ndarray = blend_images(
    #     in_img=background,
    #     layer=text,
    #     opacity0=1,
    #     opacity1=blend_factor
    # )
    rgb_text = text[:,:,:3]
    alpha_text = text[:,:,3:]
    print(f"alpha shape: {alpha_text.shape}")
    merged: np.ndarray = np_to_uint8(
        (1.0 - alpha_text) * background
        + alpha_text * rgb_text
    )

    write_image(
        filepath="~/mco/inputs/merged.png",
        img=merged
    )


    # ffmpeg -i g_fin_bgd.mkv -i g_fin_01.png -filter_complex "[0:v][1:v]overlay=enable='between(t,2,5)'[outv]" -map "[outv]" -pix_fmt yuv420p -vcodec libx264 g_fin_overlayed.mkv -y


    # ffmpeg -i g_fin_bgd.mkv -i g_fin_01.png -i g_fin_02.png -filter_complex "[0:v][1:v]overlay=enable='between(t,2,5)'[1v];[1v][2:v]overlay=enable='between(t,8,9)'[outv]" -map "[outv]" -pix_fmt yuv420p -vcodec libx264 g_fin_overlayed_double.mkv -y


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
