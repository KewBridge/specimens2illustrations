import numpy as np
import cv2
import os
import sys

def generateLabels(n:int):
    return [chr(ord('a') + i) for i in range(n)]

def writeImage(path, input_image):
    '''Writes image into path'''
    path = path + '.png'
    cv2.imwrite(path, input_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    print("Wrote Image: " + path)
    
def showImage(img, name='Image'):
    '''Shows given image. Used for debugging'''
    cv2.imshow(name, img)
    cv2.waitKey()
    cv2.destroyAllWindows()

def extractAllImages(path):
    '''
    Return all images from given path
    returns list of images and a list of their names
    '''
    images = []
    image_names = []
    
    for filename in os.listdir(path):
        
        img = cv2.imread(os.path.join(path, filename))
        
        if img is not None:
            
            images.append(img)
            image_names.append(filename)
            
    return images, image_names
        
def isGrayImage(image) -> bool:
    '''
    Given a BGR image (3 channels) split into 3
    channels and check whether they are the same.
    If they are the equivalent, it is a image consisting
    of only gray tones (1). Else, it is a proper color
    image (0).
    '''
    b,g,r = cv2.split(image)
    return np.all(b == g) and np.all(g == r)

def centerImage(image):
    '''
    Finds a no-rotation-allowed bounding box for the image,
    finds its center and translates the image so that the
    general center V<image.shape/2> is the new center of 
    the bounding box. Fills the empty part of the resulting
    image with the discarded part of the original image 
    after translation
    '''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)[1]

    w_img, h_img = thresh.shape
    x, y, w_rect, h_rect = cv2.boundingRect(thresh)

    img_center_x, img_center_y = x + w_rect / 2, y + h_rect / 2

    dx, dy = w_img / 2 - img_center_x, h_img / 2 - img_center_y
    
    # [1, 0, dx] [x]   [x + dx]
    # [1, 0, dy] [y] = [y + dy]
    #            [1]
    translation_M = np.array([[1, 0, dx], [0, 1, dy]])
    
    copy = np.copy(image)
    
    shifted_image = cv2.warpAffine(copy, translation_M, (h_img, w_img))
    
    # Fill the empty part of the image after translation with
    # the discarded part of the original image
    _dx, _dy = int(dx), int(dy)
    if dy >= 0:
        shifted_image[:_dy + 1, :] = image[-_dy - 1:, :]
    else:
        shifted_image[_dy - 1:, :] = image[:-_dy + 1, :]
    
    if dx >= 0:
        shifted_image[:, :_dx + 1] = image[:, -_dx - 1:]
    else:
        shifted_image[:, _dx - 1:] = image[:, :-_dx + 1]
        
    return shifted_image, (dx, dy)

def removePointNoise(binary_image, min_area:int=2):
    '''
    Finds all the connected components in image and
    removes all connected components with area less
    than <min_are>
    
    Keyword arguments:
    binary_image -- image with either 255 or 0
    min_area -- threshold for cc removal (default 5)
    '''
    nlabels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_image, None, None, 8, cv2.CV_32S)
    result = np.zeros((labels.shape), np.uint8)
    
    areas = stats[1:, cv2.CC_STAT_AREA]
    
    for i in range(nlabels - 1):
        if areas[i] >= min_area:
            result[labels == i + 1] = 255
        
    return result

def getVerticalLines(img, epsilon:int=5):
    '''Return all the vertical lines with error <epsilon> in image'''
    # img = cv2.imread('src.png')
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    kernel_size = 5
    blur_gray = cv2.GaussianBlur(gray,(kernel_size, kernel_size),0)
    
    low_threshold = 50
    high_threshold = 150
    edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
    
    rho = 1  # distance resolution in pixels of the Hough grid
    theta = np.pi / 180  # angular resolution in radians of the Hough grid
    threshold = 15  # minimum number of votes (intersections in Hough grid cell)
    min_line_length = 50  # minimum number of pixels making up a line
    max_line_gap = 10  # maximum gap in pixels between connectable line segments
    # line_image = np.copy(img) * 0  # creating a blank to draw lines on

    # Run Hough on edge detected image
    # Output "lines" is an array containing endpoints of detected line segments
    lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
                    min_line_length, max_line_gap)
    
    if lines is None:
        return
    
    new_lines = []
    for line in lines:
        for x1,y1,x2,y2 in line:
            # cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
            
            w, h = max(x1 - x2, 1), y1 - y2
            angle = np.degrees(np.arctan(h/w))
            
            if np.abs(angle) > 90 - epsilon:
                new_lines.append(line)
    
    # lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)
    # showImage(lines_edges)
    
    return new_lines

def clearAroundLines(image, lines, weight:int=40):
    '''
    From a list of line, changes all the pixels at most
    <weight> away from the line to white.
    
    Keyword arguments:
    image -- cv2.Image in BGR format
    lines -- list of lines - line is (x1, y1, x2, y2),
    assumes lines are vertical.
    weight -- The value to thicken the line (default 5)
    '''
    if not lines:
        return image
    
    for line in lines:
        cv2.line(image, line[0, :2], line[0, 2:], (255, 255, 255), weight)
        
    return image

def pairHeightwithLine(height_predictions, lines):
    '''
    Pair bounding box from height_predictions to
    line segment from lines one-to-one.
    
    Keyword arguments:
    height_predictions -- list of tuples of text,
    bounding-box pairs obtained from keras_ocr
    image-to-text algorithm filtered to only contain
    the height data.
    lines -- list of line segments obtained from the
    difference between main image and all the segments
    that are already classified (missing_image). Lines
    are always connected and vertical - no dotted lines!
    '''
    pass

def getScaleBars(missing, height_predictions):
    '''
    Returns contours of scale bars mathcing 1-1
    to each unique height prediction. 
    '''

def addBorders(image, border_length: int, color: int=255):
    '''Adds borders of color <color> and length <border_length>'''
    padding = (border_length, border_length)
    return np.pad(image, [padding, padding, (0,0)], constant_values=(color, color))

def undoBorders(image, border_length:int):
    '''Undo borders of length <border_length>'''
    w, h = image.shape[:2]
    start, end_w, end_h = border_length, w - border_length, h - border_length
    return image[start:end_w, start:end_h]
