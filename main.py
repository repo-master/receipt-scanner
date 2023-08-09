# This is needed for Windows PC using scaling (150% scale) only
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(True)


import cv2
import argparse
import numpy as np
from pathlib import Path


def make_image_sharp(image, blur_amt = 0):
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

    kernel = np.array([
        [1, 2, 1],
        [2, 8, 2],
        [1, 2, 1]
    ]) / 16.0  # Normalize the kernel

    # Apply the custom kernel using filter2D
    filtered_image = cv2.filter2D(image, -1, kernel)

    return filtered_image


def enhance(img):
    kernel = np.array([
        [1, 1, 1],
        [2, 4, 2],
        [1, 1, 1]
    ]) / 16.0  # Normalize the kernel

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

    gray = 1 - gray

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    print(laplacian_var)

    gray = make_image_sharp(gray)

    kernel = np.ones((3, 3), np.uint8)
    morph = cv2.morphologyEx(gray, cv2.MORPH_ERODE, kernel, iterations=1)
    morph = cv2.morphologyEx(morph, cv2.MORPH_DILATE, kernel, iterations=2)

    # Threshold: thresh should be between 0 and 255
    _, gray = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return gray


def handle_img_file(img_file: Path):
    img = cv2.imread(str(img_file))
    cv2.imshow("Image", resize_image(img))

    preprocessed = preprocess(img)
    if preprocessed is not None:
        cv2.imshow("Preprocessed", preprocessed)

    return cv2.waitKey(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--image", action="store", type=Path, required=True, help="Image"
    )
    args = parser.parse_args()

    # Either filename or directory name passed as argument
    img_path: Path = args.image

    if img_path.is_dir():
        for i, img_file in enumerate(img_path.glob("*.jpg")):
            key = handle_img_file(img_file)
            # Quit if q key is pressed
            if key == ord('q'): break
    elif img_path.exists():
        handle_img_file(img_path)


if __name__ == "__main__":
    main()
