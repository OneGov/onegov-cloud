import cv2 as cv
import numpy as np
from onegov.core.utils import module_path


def crop_to_portrait_with_face_detection(image):
    """Detects faces in the input image using OpenCV's Haar cascade
    classifier,
    crops the image to focus on the face(s), and expands the image by 20%
    in each dimension. Finally, resizes the image to 1:1 aspect ratio.

    Returns: The png-encoded image as bytes, or None
        Quadratic crop of the input image, or None if no faces are detected.
    """
    img = cv.imread(str(image))
    path = "haarcascade_frontalface_alt.xml"
    path = module_path("onegov.people", f"static/cascades/{path}")
    cascade = cv.CascadeClassifier(path)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gray = cv.equalizeHist(gray)
    rects = detect(gray, cascade)
    snippets = crop_rects(rects, img)

    if snippets:
        img = crop_with_padding(img, rects, snippets, scale=1.2)
        w, h = img.shape[:2]
        if not w == h:
            # Resize the image to 1:1 aspect ratio
            side = min(w, h)
            img = crop_square(img, side)
        # Encode the image as PNG and get the bytes in memory
        retval, buffer = cv.imencode('.png', img)
        return np.array(buffer).tobytes() if retval else None
    else:
        return None


def detect(img, cascade):
    rects = cascade.detectMultiScale(
        img,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100),
        flags=cv.CASCADE_SCALE_IMAGE,
    )
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects


def draw_rectangles(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv.rectangle(img, (x1, y1), (x2, y2), color, 2)


def crop_rects(rects, img):
    """
    Cuts mutiple rectangles from the image.
    Rects has to be an iterable of opencv rectangles. (which are simply
    numpy arrays)
    rect = [x1, y2, x2, y2]

    (x1,y1)
        ┌──────────┐
        │          │
        │          │
        └──────────┘
                (x2,y2)

    """
    try:
        rectangle_snippets = []
        for x1, y1, x2, y2 in rects:
            roi = crop_rect_from_image(x1, y1, x2, y2, img)
            rectangle_snippets.append(roi)
        return rectangle_snippets
    except (TypeError, ValueError):
        return []


def crop_rect_from_image(x1, y1, x2, y2, im):
    roi = im[y1:y2, x1:x2]
    return roi


def is_quadratic(rect):
    try:
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1
        return width == height
    except (TypeError, ValueError):
        return False


def find_biggest_rectangle(rects):
    """Finds the rectangle with maximum area, which seems most likely to
    yield a good clipping.

    Returns the rectangle, type np.ndarray."""

    max_rectangle = rects[0]
    max_area = -1
    for x1, y1, x2, y2 in rects:
        width = x2 - x1
        height = y2 - y1
        area = width * height
        if area > max_area:
            max_area = area
            max_rectangle = np.array([x1, y1, x2, y2])
    return max_rectangle


def crop_with_padding(img, rects, snippets, scale=1.2):
    """Select a rectangle and crop the image.
    The optional parameter scale can be set to increase the size of the crop.
    """

    # if exactly one rectangle is found, select it.
    if len(snippets) == 1:
        rect = rects[0]

    # if multiple detections are found, select the largest
    elif len(snippets) > 1:
        rect = find_biggest_rectangle(rects)
    else:
        return None

    x1, y1, x2, y2 = rect
    width = x2 - x1
    # Heuristically make the rectangle larger by some constant factor
    enlarge_by = int((width / 3) * scale)

    # Secure against numbers that are outside the coordinate system
    scaled_x1 = max(x1 - enlarge_by, 0)
    scaled_y1 = max(y1 - enlarge_by, 0)

    # todo: take the min here to prevent overflow of the cropped area
    # _, _, ix2, iy2 = img
    # scaled_x2 = min(x2 + enlarge_by , ix2)
    # scaled_y2 = min(y2 + enlarge_by, iy2)

    scaled_x2 = x2 + enlarge_by
    scaled_y2 = y2 + enlarge_by

    img = crop_rect_from_image(scaled_x1, scaled_y1, scaled_x2, scaled_y2, img)
    return img


def crop_square(img, size, interpolation=cv.INTER_AREA):
    h, w = img.shape[:2]
    min_size = np.amin([h, w])

    # Centralize and crop
    crop_img = img[
        int(h / 2 - min_size / 2):int(h / 2 + min_size / 2),
        int(w / 2 - min_size / 2):int(w / 2 + min_size / 2),
    ]
    return cv.resize(crop_img, (size, size), interpolation=interpolation)
