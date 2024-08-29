import numpy as np
import cv2
import imageio
import os

import sys
from functions.imageFunctions import addBorders, undoBorders, showImage
from functions.image2textFunctions import (contours2Label, getHeightandVerticalLine,reFilterPredictions, getSegmentPairbyDottedLine, getDottedLinesasContour, filterPredictions)

# Find the biggest segment of the image --helper
def findBiggestSegment(input_image):
    '''
    Finds the contour with the biggest area and
    returns it drawn to a white background.
    '''
    # Store a copy of the input image:
    biggest_segment = input_image.copy()
    # Set initial values for the
    # largest contour:
    largest_area = 0
    largest_contour_index = 0

    # Find the contours on the binary image:
    contours, hierarchy = cv2.findContours(input_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # Get the largest contour in the contours list:
    for i, cc in enumerate(contours):
        # Find the area of the contour:
        area = cv2.contourArea(cc)
        # Store the index of the largest contour:
        if area > largest_area:
            largest_area = area
            largest_contour_index = i

    # Once we get the biggest blob, paint it black:
    temp_mat = input_image.copy()
    cv2.drawContours(temp_mat, contours, largest_contour_index,(0, 0, 0), -1, 8, hierarchy)
    # Erase smaller blobs:
    biggest_segment = biggest_segment - temp_mat

    return biggest_segment, largest_area



# Segments the image and returns all segmented parts
def segmentColorImage(_image, padding: int = 50, min_area_ratio: float = 0.05):
    if padding:
        image = addBorders(_image, padding)
    else:
        image = _image.copy()

    # Turn the image into gray_scale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, binary_image = cv2.threshold(
        gray_image, 250, 255, cv2.THRESH_BINARY_INV)

    no_label_segments = []
    w, h, _ = _image.shape

    min_area = min_area_ratio * w * h

    contours = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = [c for c in contours if cv2.contourArea(c) > min_area]

    for contour in contours:
        segment = image.copy()
        (x, y, _w, _h) = cv2.boundingRect(contour)

        mask = np.zeros_like(binary_image)
        mask[y:y+_h, x:x+_w] = 255

        segment = cv2.bitwise_and(segment, segment, mask=mask)

        if padding:
            segment = undoBorders(segment, padding)

        no_label_segments.append((segment, (x,y)))
        
    
    key = lambda n: n[1][0] * w + n[1][1]
    no_label_segments = sorted(no_label_segments, key=key)
    
    segments = {}
    
    for i, segment in enumerate(no_label_segments):

        segment = segment[0]    
        label = chr(97 + i)
        segments[label] = segment

    return segments
    


def getMissingImage(image, _predictions, labels, min_area=500):
    predictions = _predictions.copy()
    gray = cv2.cvtColor(image, 6)

    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    max_contours = [cc for cc in contours if cv2.contourArea(cc) > min_area]
    max_contours.sort(key=lambda cc: cv2.contourArea(cc), reverse=True)

    label_contour_map = contours2Label(max_contours, predictions, labels)
    # colors = colorLogic(len(label_contour_map))
    height_predictions = reFilterPredictions(predictions)
    min_distances, boxes = getHeightandVerticalLine(max_contours, height_predictions)

    kernel_size = 3
    op_iterations = 3
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    fill_position = (0, 0)
    fill_color = (255, 255, 255)
    color_tolerance = (0, 0, 0)

    copy = np.copy(image)

    segments = []

    for i, key in enumerate(label_contour_map):
        # color = colors[i]
        binary_copy = np.copy(binary)
        for j, cnt in enumerate(label_contour_map.get(key, [])):

            idx = -1
            if len(cnt) == 2:
                idx, cnt = cnt
            height_idx = np.where(min_distances == idx)[0]

            if height_idx.shape[0]:
                box = boxes[height_idx[0]]
                box = np.intp(box)
                cv2.drawContours(binary_copy, [box], 0, (0, 0, 0), -1, 8)

            cv2.drawContours(binary_copy, [cnt], 0, (0, 0, 0), -1, 8)

        segment = binary - binary_copy

        binary_mask = cv2.morphologyEx(segment, cv2.MORPH_DILATE, morph_kernel, None, None, op_iterations, cv2.BORDER_REFLECT101)

        blob_mask = cv2.bitwise_and(copy, copy, mask=binary_mask)

        cv2.floodFill(blob_mask, None, fill_position, fill_color, color_tolerance, color_tolerance)

        masked_image = cv2.bitwise_or(image, blob_mask)

        #binary = binary - segment
        # showImage(masked_image)
        segments.append(masked_image)

    missing = highlightMissing(image, segments, 0)
    return missing, max_contours, segments


def getDottedLinePairs(missing, contours, label_prediction, min_area):
    gray = cv2.cvtColor(missing, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 250, 255, 1)
    showImage(binary)

    min_contours = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    max_contour = max(min_contours, key=lambda cc: cv2.contourArea(cc))

    # Imzadan kurlutmak icin bbox bul sonra rotated rect bul ve w-h oranina gore imzayi al

    missing = cv2.drawContours(missing, [max_contour], 0, (255, 255, 255), -1, 8)

    dotted_lines = getDottedLinesasContour(missing, label_prediction, min_area=min_area)

    white_image = np.copy(missing)
    cv2.drawContours(white_image, dotted_lines, -1, (0, 0, 255), 1)
    showImage(white_image)

    min_distances = getSegmentPairbyDottedLine(contours, dotted_lines)

    return np.array(min_distances)


def segmentGrayImage(image, predictions, labels, min_contour_area=500, min_noise_area=10):
    _predictions = predictions.copy()
    missing, contours, _ = getMissingImage(image, _predictions, labels, min_area=min_contour_area)

    #TODO: Fix these
    #label_prediction = filterPredictions(_predictions, labels)
    # getDottedLinePairs(missing, contours, label_prediction, min_area=min_noise_area)
    dotted_line_pairs = []

    label_contour_map = contours2Label(contours, _predictions, labels, dotted_line_pairs=dotted_line_pairs)

    height_predictions = reFilterPredictions(_predictions)
    min_distances, boxes = getHeightandVerticalLine(contours, height_predictions)

    kernel_size = 3
    op_iterations = 3
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    fill_position = (0, 0)
    fill_color = (255, 255, 255)
    color_tolerance = (0, 0, 0)

    copy = np.copy(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    segments = {}

    for i, key in enumerate(label_contour_map):
        # color = colors[i]
        binary_copy = np.copy(binary)
        for j, cnt in enumerate(label_contour_map.get(key, [])):

            idx = -1
            if len(cnt) == 2:
                idx, cnt = cnt
            height_idx = np.where(min_distances == idx)[0]

            if height_idx.shape[0]:
                box = boxes[height_idx[0]]
                box = np.intp(box)
                cv2.drawContours(binary_copy, [box], 0, (0, 0, 0), -1)

            cv2.drawContours(binary_copy, [cnt], 0, (0, 0, 0), -1, 8)

        segment = binary - binary_copy
        # showImage(segment)
        binary_mask = cv2.morphologyEx(segment, cv2.MORPH_DILATE, morph_kernel, None, None, op_iterations, cv2.BORDER_REFLECT101)

        blob_mask = cv2.bitwise_and(copy, copy, mask=binary_mask)

        cv2.floodFill(blob_mask, None, fill_position, fill_color, color_tolerance, color_tolerance)

        masked_image = cv2.bitwise_or(image, blob_mask)

        binary = binary - segment

        segments[key] = masked_image

    return segments


# Creates a gif video of image and highlights different segments sequentially
def segments2gif(image, segments, image_name, output_path, alpha=0.2, duration=1):
    highlighted_images = []
    for segment in segments:
        _segment = highlightSegments(image, segment)
        highlighted_images.append(_segment)

    path = os.path.join(output_path, f"{image_name}.gif")
    imageio.mimsave(path, highlighted_images, duration=duration)
    print(f"Wrote Video: {path}")

# Helper function for segments2gif: Highlights the intersection of original_image and segment
# with a saturation of aplpha for non-intersected parts


def highlightSegments(original_image, segment, alpha=0.3):
    '''
    Returns an image with intersection of original_image and segment with normal opacity
    and the rest with alpha opacity
    '''
    highlighted_image = cv2.addWeighted(original_image, alpha, segment, 1-alpha, 0)
    return highlighted_image

# Highlights the segments of that are missing from original_image after the segmentation
# is applied


def highlightMissing(original_image, segments, alpha=0.3):
    '''
    Returns an image with non-intersecting parts of original_image and segments
    with normal opacity and rest with alpha opacity
    '''
    missing_segments = original_image.copy()

    for segment in segments:
        no_segment = cv2.bitwise_not(segment)
        missing_segments = cv2.bitwise_or(missing_segments, no_segment)

    return highlightSegments(original_image, missing_segments, alpha)
