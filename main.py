# This is needed for Windows PC using scaling (150% scale) only
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(True)

import cv2
import argparse
import numpy as np
from pathlib import Path
from typing import Optional
import pandas as pd

import json

from model.textract import extract_text_from_image


def resize_image(image, fixed_height: int = 500):
    aspect_ratio = image.shape[:2][1] / image.shape[:2][0]
    new_width = int(fixed_height * aspect_ratio)
    return cv2.resize(image, (new_width, fixed_height))




def handle_img_file(img_file: Path, save_path: Optional[Path] = None):
    img = cv2.imread(str(img_file))
    print("reading : ", str(img_file))

    if img is None:
        print("Skipping %s as it is not a valid image." % str(img_file))
        return
    
    # processed_image = preprocess(img)

    table_csv = extract_text_from_image(img)

    file_name = str(img_file).split('\\')[1]
    with open(f'./output/textract/Final_{file_name}.json', 'w') as fout:
        print("saving : ", file_name)
        json.dump(table_csv, fout)


    should_display = True
    if save_path is not None:
        should_display = False

    if should_display:
        cv2.imshow("Image", resize_image(img))


    if should_display:
        return cv2.waitKey(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--image",
        action="store",
        type=Path,
        required=True,
        help="Image file/directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        help="If used, output directory to save preprocessed images (disables window output)",
    )
    args = parser.parse_args()

    # Either filename or directory name passed as argument
    img_path: Path = args.image
    save_path: Optional[Path] = args.output

    if img_path.is_dir():
        for img_file in img_path.glob("*"):
            key = handle_img_file(img_file, save_path)
            # Quit if q key is pressed
            if key == ord("q"):
                break
            # break
    elif img_path.exists():
        handle_img_file(img_path, save_path)


if __name__ == "__main__":
    main()


