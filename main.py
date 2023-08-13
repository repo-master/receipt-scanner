# This is needed for Windows PC using scaling (150% scale) only
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(True)


import cv2
import argparse
import numpy as np
from pathlib import Path
from typing import Optional


def make_image_sharp(image, blur_amt=0):
    # tune to get better result

    # fmt: off
    kernel = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ])
    # fmt: on
    image = cv2.filter2D(image, -1, kernel)
    # image = cv2.GaussianBlur(image, (1, 1), blur_amt)

    kernel = np.array([[1, 2, 1], [2, 8, 2], [1, 2, 1]]) / 16.0  # Normalize the kernel

    # Apply the custom kernel using filter2D
    filtered_image = cv2.filter2D(image, -1, kernel)

    return filtered_image


def enhance(img):
    kernel = np.array([[1, 1, 1], [2, 4, 2], [1, 1, 1]]) / 16.0  # Normalize the kernel

    # # Apply the custom kernel using filter2D
    # filtered_image = cv2.filter2D(img, -1, kernel)
    return cv2.dilate(img, kernel, iterations=1)


def resize_image(image, fixed_height: int = 500):
    aspect_ratio = image.shape[:2][1] / image.shape[:2][0]
    new_width = int(fixed_height * aspect_ratio)
    return cv2.resize(image, (new_width, fixed_height))


def preprocess(img):
    p_img = img

    gray = cv2.cvtColor(p_img, cv2.COLOR_BGR2GRAY)

    # gray = 1 - gray

    # laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # print("Laplacian:", laplacian_var)

    # gray = make_image_sharp(gray)

    # kernel = np.ones((3, 3), np.uint8)
    # morph = cv2.morphologyEx(gray, cv2.MORPH_ERODE, kernel, iterations=1)
    # morph = cv2.morphologyEx(morph, cv2.MORPH_DILATE, kernel, iterations=2)

    # Threshold: thresh should be between 0 and 255
    # _, gray = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    th3 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 63, 24
    )

    return th3


def handle_img_file(img_file: Path, save_path: Optional[Path] = None):
    img = cv2.imread(str(img_file))
    if img is None:
        print("Skipping %s as it is not a valid image." % str(img_file))
        return

    print(img_file, end=": ")

    should_display = True
    if save_path is not None:
        should_display = False

    if should_display:
        cv2.imshow("Image", resize_image(img))

    preprocessed = preprocess(img)

    if should_display and preprocessed is not None:
        cv2.imshow("Preprocessed", preprocessed)

    if save_path is not None:
        img_save_path = save_path.joinpath(img_file.name)
        save_path.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(img_save_path), preprocessed)

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
    elif img_path.exists():
        handle_img_file(img_path, save_path)


if __name__ == "__main__":
    main()
