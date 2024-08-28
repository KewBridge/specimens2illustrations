'''Set of fuctions for image-to-text and assigning contours to closest label centres.'''

import cv2
import numpy as np
import re 

import sys
FUNCTIONS_PATH = 'C:/Users/eka10kg/OneDrive - The Royal Botanic Gardens, Kew/functions'
if FUNCTIONS_PATH not in sys.path:
    sys.path.append(FUNCTIONS_PATH)
    
from boundingBoxFunctions import mergeBoxes, clearAroundBoundingBox, getAreaofBox
from imageFunctions import getVerticalLines, clearAroundLines, removePointNoise
   
def filterPredictions(predictions, labels, test:bool=False, weight:int=10) -> list[tuple]:
    '''Filter all predictions that are not in labels.'''
    filtered_predictions = []
    for prediction in predictions[0]:
        
        if prediction[0] in labels and len(prediction[0]) == 1:
            pass
        # Condition for detecting 'es' or other real label bounding boxes
        # that are misidentified by the keras_ocr pipeline
        elif prediction[0][0] in labels and prediction[0][1] != 'm':
            pass
        else:
            continue
        
        label, _box = prediction
        box = np.copy(_box)
        
        max_xs = np.sort(box[:, 0])[2:]
        max_ys = np.sort(box[:, 1])[2:]
        
        for i, point in enumerate(box):
            if point[0] in max_xs:
                box[i] += np.array([weight, 0])
            if point[1] in max_ys:
                box[i] += np.array([0, weight])
        
        filtered_predictions.append((label, box))
    
    filtered_predictions.sort(key = lambda elem: elem[0])
    
    if test:
        assert len(filtered_predictions) == len(labels), 'Error in predictions!'
        
    return filtered_predictions

def reFilterPredictions(predictions, regex:str='[cm]m', max_distance:int=100):
    '''
    Find all the height data bounding boxes, usually in format
    single int for height data and 'mm' or 'cm' for unit. If 
    those two are seperate bounding boxes, merge the labels and
    find the new bounding box encapsulating their two bounding
    boxes. If they are together, continue.
    '''
    unit_predictions = []
    height_predictions = []
    
    filtered_predictions = []
    
    for prediction in predictions[0]:
        
        if re.search(regex, prediction[0]):    
            unit_predictions.append(prediction)
        
        elif prediction[0].isdigit():

            height_predictions.append(prediction)
        
    for label, box in unit_predictions:
        center = np.sum(box, axis=0) / 4
        is_merged = False
        
        for _label, _box in height_predictions:
            
            if is_merged:
                continue
            
            _center = np.sum(_box, axis=0) / 4
            dist = np.linalg.norm(center - _center)
            
            if dist < max_distance:
                is_merged = True

                x,y,w,h = mergeBoxes((box, _box))
                new_box = cv2.boxPoints(((x + w/2, y + h/2), (w, h), 0))
                new_box = np.intp(new_box)
                
                new_label = f'{_label} {label}'
                filtered_predictions.append((new_label, new_box))
        
        # In case digit and unit are not seperate predictions
        if not is_merged:
            filtered_predictions.append((label, box))    
            
    return filtered_predictions

def getHeightandVerticalLine(contours, height_predictions, x_increase:int=25, y_increase:int=0):
    boxes = []
    for (label, _box) in height_predictions:
        box = np.copy(_box)
        
        sorted_x = np.sort(box[:, 0])
        min_xs = sorted_x[:2]
        
        sorted_y = np.sort(box[:, 1])
        min_ys = sorted_y[:2]
        # max_ys = sorted_y[2:]
        
        for i, point in enumerate(box):
            # new_box = np.copy(box)
            if point[0] in min_xs:
                box[i] = point - np.array([x_increase, 0])
            if point[1] in min_ys:
                box[i] = point - np.array([0, y_increase])
        
        boxes.append(box)
        
    distance_array = getDistanceArrays(contours, height_predictions, mode='height')
    min_distances = np.argmin(distance_array, axis=0) 
    
    return min_distances, boxes

def getkMinIndex(array, k:int):
    mins = []
    for i in range(array.shape[1]):
        idx = np.argpartition(array[:, i], k)
        mins.append(idx[:k])
    
    return np.array(mins).T
        
def contours2Label(contours, predictions, labels, dotted_line_pairs = []):
    '''
    Categorizes each segment to a labelling letter
    based on the minimum of shortest distance between
    contours to prediction centres.
    
    Keyword arguments:
    segments -- segments of the main image
    predictions -- result of image-to-text algorithm
    assumed to only contain label letters and height data
    labels -- set of letters used as labels in illustration
    dotted_line_pairs -- 2D array of shape (#dotted_line, 2)
    where each element is a pari of contour indexes connected
    by dotted_lines
    '''
    label_predictions = filterPredictions(predictions, labels)
    distance_array = getDistanceArrays(contours, label_predictions)
    min_distances = np.argmin(distance_array, axis=0)
    
    label_contour_map = {}
    bounding_box_added = [0] * len(label_predictions)
    
    is_contour_added = np.zeros(len(contours), dtype='bool')
    
    for i, (idx, cnt) in enumerate(zip(min_distances, contours)):
        
        # Skip to next iteration if contour is already classified
        if is_contour_added[i]:
            continue
        
        label = labels[idx]
        
        cnts = label_contour_map.get(label, [])
        cnts.append((i, cnt))
        
        is_contour_added[i] = True
        
        # Condition for next iteration if dotted_line_pairs does not exist
        if len(dotted_line_pairs) != 0:
            # Find all index occurences of current contour index in dotted_line_pairs
            # This is done on the first entry of each element as that is the main
            # segment in a dotted_line_pair
            pair_indexes = np.where(dotted_line_pairs[:, 0] == i)[0]
            
            for j in pair_indexes:
                # Get the sub segment in the dotted_line_pair
                _i = dotted_line_pairs[j, 1]
                cnts.append((_i, contours[_i]))
                
                is_contour_added[_i] = True
            
        # cnts.append(cnt)

        if not bounding_box_added[idx]:
            # Prediction is sorted and lowercase
            box = label_predictions[ord(label) - ord('a')][1]
            box = np.intp(box)
            cnts.append(box)
            bounding_box_added[idx] = True
            
        label_contour_map[label] = cnts
    
    
    # Should only happen with intersections
    for i, _bool in enumerate(bounding_box_added):
        if not _bool:
            cnts = label_contour_map.get(labels[i], [])
            
            box = label_predictions[ord(label) - ord('a')][1]
            box = np.intp(box)
            cnts.append(box)
            
    return label_contour_map

def getDistanceArrays(contours, predictions, mode='default'):
    '''
    Get the shortest distance between every contour and
    every predeiction bounding box center. There are three
    modes: 'default' is for mapping contours to predictions
    'height' is for mapping height predictions to contours
    and 'dotted_line' is for mapping dotted_lines to contours.
    '''
    distance_array = np.zeros((len(predictions), len(contours)))
    
    for i, prediction in enumerate(predictions):
        
        if mode == 'dotted_line':
            box = np.reshape(prediction, (prediction.shape[0], prediction.shape[-1]))
        else:
            label, box = prediction
        
        center = np.sum(box/box.shape[0], axis=0)
        
        for j, cnt in enumerate(contours):
            
            distance = cv2.pointPolygonTest(cnt, center, measureDist=True)
            if distance < 0:
                distance_array[i, j] = -distance
    
    distance_array = distance_array if mode == 'default' else distance_array.T
    return distance_array

def getDottedLinesasContour(missing_image, label_prediction, min_area=10):
    '''
    Using label positioning and line detection find all dotted lines
    (all objects undetected by both algorithms) in image, usually
    all uncategorized parts of main_image after segmentation
    
    IMPORTANT: PUT COPY IMAGE AS INPUT
    '''
    bboxes = [box for _, box in label_prediction]
    image = clearAroundBoundingBox(missing_image, bboxes, weight=25)
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    binary_image = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
    
    binary_image = removePointNoise(binary_image, min_area=min_area)
    
    #Dialte image to connect dotted lines 
    image_dilation = cv2.dilate(binary_image, np.ones((5,5)))
    
    contours = cv2.findContours(image_dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    
    return contours

def getSegmentPairbyDottedLine(contours, line_contours):
    '''
    Pairs up two segments by the location of dotted lines
    and returns the indexes of contours that are paired up
    with the first being main segment (always segment with 
    bigger area) and second being sub-segment.
    '''
    # TODO: find two contours closest to dotted lines center
    # which should be sum(X) / len, sum(Y) / len and pointPolygonTest
    # Compare areas add to list idx big one first then small
    # [(1,2), (5,12)] etc. in testf seperate second indexes and
    # draw them together with the first indexes. 
        
    distance_array = getDistanceArrays(contours, line_contours, mode='dotted_line')
    min_distances = getkMinIndex(distance_array, k=2)
    
    min_distances = np.sort(min_distances, axis=0)
    
    return min_distances.T

# def mergeSegmentsbyDottedLines(segments, rects, dotted_lines):
#     '''
#     Merge two segment pairs and their corresponding bounding boxes per
#     dotted_line in dotted_lines.
    
#     Keyword arguments:
#     segments -- list of segment images in BRG format
#     rects -- list of bounding boxes as (center), (dim), angle
#     dotted_lines -- list of bounding boxes representing
#     dotted lines in main image
#     '''
#     minimum_dist = []
#     # dotted_line is rect, not line!
#     for dotted_line in dotted_lines:
#         break
    
#     return 1
