#!/usr/bin/env python3

# Test script to identify rectangles (GUI buttons) in an image.

import cv2

oim = im = cv2.imread('screenshot.png')
for gray in cv2.split(im):
    ret, thresh = cv2.threshold(gray, 127, 255, 0)
    contours, h = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if 20 < w < 200 and 20 < h < 200:
            cv2.rectangle(oim, (x, y), (x + w, y + h), (0, 255, 0), 2)
cv2.imwrite('mod.png', oim)
