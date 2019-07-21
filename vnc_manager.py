import atexit
import os
import io
import time
import cv2
import logging
import numpy

from vncdotool import api


def retry(retries=3, wait=1):
    """
    Retry a method until it returns true or a specified number of iterations is met.
    """
    def outer_wrapper(func):
        def wrapper(self, *args, **kwargs):
            nonlocal retries, wait
            local_retries = kwargs.get("retry", retries)
            wait = kwargs.get("wait", wait)
            if local_retries < 0:
                return False
            if "retry" in kwargs:
                del kwargs["retry"]
            if "wait" in kwargs:
                del kwargs["wait"]
            if func(self, *args, **kwargs):
                return True
            else:
                time.sleep(wait)
                kwargs["retry"] = local_retries - 1
                return wrapper(self, *args, **kwargs)
        return wrapper
    return outer_wrapper


def add_threshold(func):
    """
    Add the default threshold as an argument if none is specified.
    """
    def wrapper(self, *args, **kwargs):
        if "threshold" not in kwargs:
            kwargs["threshold"] = self._threshold
        return func(self, *args, **kwargs)
    return wrapper


class VNCManager(object):
    """
    Manages connecting to the Docker instance via VNC and performing computer vision to detect where to click.
    """
    def __init__(self, port, threshold=0.12):
        self._port = port
        self._image_paths = []
        self._logger = logging.getLogger(self.__class__.__name__)
        self._threshold = threshold
        self._conn = api.connect('127.0.0.1::{}'.format(self._port), password=None)
        atexit.register(self.cleanup)

    def add_image_path(self, path):
        self._image_paths.append(path)

    def cleanup(self):
        self._conn.disconnect()

    def click(self, x, y, btn):
        x, y = int(x), int(y)
        self._conn.mouseMove(x, y)
        self._conn.mousePress(btn)

    def left_click(self, x, y):
        self._logger.debug("Left clicking ({}, {})".format(x, y))
        self.click(x, y, 1)

    def right_click(self, x, y):
        self._logger.debug("Right clicking ({}, {})".format(x, y))
        self.click(x, y, 2)

    def get_image_path(self, name):
        for path in reversed(self._image_paths):
            full_path = os.path.join(path, "{}.png".format(name))
            if os.path.isfile(full_path):
                return full_path
        raise ValueError("Could not find '{}' in image paths: []".format(name, self._image_paths))

    def get_cv_results(self, other_image):
        bio = io.BytesIO()
        bio.name = "screenshot.png"
        self._conn.captureScreen(bio)
        bio.seek(0)
        haystack = cv2.imdecode(numpy.frombuffer(bio.getbuffer(), numpy.uint8), -1)
        needle = cv2.imread(self.get_image_path(other_image))
        result = cv2.matchTemplate(needle, haystack, cv2.TM_SQDIFF_NORMED)
        mn, _, mnLoc, _ = cv2.minMaxLoc(result)
        return mn, mnLoc, needle.shape[0], needle.shape[1]

    def save_screenshot(self, path):
        self._conn.captureScreen(path)

    @add_threshold
    @retry()
    def left_click_image(self, image, threshold):
        mn, mnLoc, trows, tcols = self.get_cv_results(image)
        if mn > threshold:
            self._logger.info("Could not click {}, min: {}".format(image, mn))
            return False
        mpx, mpy = mnLoc
        self.left_click(mpx + tcols / 2, mpy + trows / 2)
        self._logger.info("Clicked {}, min: {}".format(image, mn))
        return True

    @add_threshold
    def has_image(self, image, threshold):
        mn, _, _, _ = self.get_cv_results(image)
        out = mn < threshold
        self._logger.info("Image check on {}: {} (min: {})".format(image, out, mn))
        return out

    @retry(retries=100)
    def wait_for_image(self, image):
        return self.has_image(image)

    @retry(retries=100)
    def wait_for_no_image(self, image):
        return not self.has_image(image)

    def left_click_image_until_gone(self, *args, **kwargs):
        while self.left_click_image(*args, **kwargs):
            time.sleep(1)

    def send_key(self, key):
        self._logger.info("Sending key {}".format(key))
        self._conn.keyPress(ch)

    def send_text(self, text, private=False, enter=False):
        self._logger.info("Typing {}".format("*" * len(text) if private else text))
        for ch in text:
            time.sleep(0.02)
            self._conn.keyPress(ch)

        if enter:
            time.sleep(0.02)
            self._conn.keyPress("enter")
