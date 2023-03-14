from wand.image import Image as wand_image
from PIL import Image as pil_image
from glob import glob
from pathlib import Path
from bounded_pool_executor import BoundedProcessPoolExecutor

import os
import argparse
import traceback
import numpy as np
import multiprocessing as mp


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(description="Script to crop training files, support jpeg/png/psd")
    parser.add_argument(
        "--input_dir",
        type=str,
        default=None,
        required=True,
        help="Path to training images folder",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        required=True,
        help=(
            "Path to store cropped images, end with _cropped"
        ),
    )

    if input_args is not None:
        args = parser.parse_args(input_args)
    else:
        args = parser.parse_args()
    
    return args

def img_resize(file, size=512):
    with pil_image.open(file) as im:
        width, height = im.size
        if width < height:
            newWidth = size
            newHeight = int(height / (width / size))
            cropTop = (newHeight - size) // 2
            cropBottom = cropTop + size
            crop = (0, cropTop, size, cropBottom)
        else:
            newHeight = size
            newWidth = int(width / (height / size))
            cropLeft = (newWidth - size) // 2
            cropRight = cropLeft + size
            crop = (cropLeft, 0, cropRight, size)
        imResize = im.resize((newWidth, newHeight))
        imCrop = imResize.crop(crop)
        basename = file.split('/')[-1].split('.')[0]
        
        imCrop.save(os.path.join(output_dir, "{}_cropped.jpeg".format(basename)))

def psd_resize(file, size=512):
    myImage = wand_image(filename="{}[0]".format(file))
    myImage.format = "png"

    width, height = myImage.size
    if width < height:
        newWidth = size
        newHeight = int(height / (width / size))
    else:
        newHeight = size
        newWidth = int(width / (height / size))

    myImage.resize(newWidth, newHeight)
    # print(newWidth, newHeight)
    myImage.crop(width=size, height=size, gravity="center")
    basename = file.split('/')[-1].split('.')[0]
    
    myImage.save(filename=os.path.join(output_dir, "{}_cropped.png".format(basename)))

def handler(file_list):
    for f in file_list:
        try:
            postfix = f.split('.')[-1]
            if postfix == 'jpeg' or postfix == 'jpg' or postfix == 'png':
                img_resize(f)
            elif postfix == 'psd':
                psd_resize(f)
        except Exception:
            print(postfix, f)
            print(traceback.format_exc())

def batch_run(file_list):
    _PARALLEL = mp.cpu_count()
    _LEN = len(file_list)
    if _PARALLEL > _LEN:
        _PARALLEL = _LEN

    file_list_split = np.array_split(file_list, _PARALLEL)

    with BoundedProcessPoolExecutor(max_workers=(_PARALLEL)) as executor:
        _ = executor.map(handler, file_list_split)


if __name__ == '__main__':
    args = parse_args()

    input_path = args.input_dir
    output_dir = args.output_dir

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    file_list = glob(os.path.join(input_path, '*'))
    print(file_list)
    
    batch_run(file_list)




