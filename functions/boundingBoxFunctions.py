import cv2
import numpy as np
import os

def colorLogic(n: int) -> list[list[int]]:
    '''Returns the first n colors of the rainbow in BGR format.'''
    res = [[2, 0, 0]]
    
    current2idx = next_idx = 0
    
    while n != 1:
        new_item = [i for i in res[-1]]
        
        if new_item[current2idx] == 0:
            current2idx = next_idx
        
        next_idx = (current2idx + 1) % 3
        
        if new_item[next_idx] == 2:
            new_item[current2idx] -= 1
        else:
            new_item[next_idx] += 1
        
        res.append(new_item)
        n -= 1
        
    return [[(255, 127, 0)[j] for j in i] for i in res]

def boundingBoxSegments(segments):
    '''
    Returns the minimum area bounding box for every segment in segments
    and the color it should be shown in
    '''
    colors = colorLogic(len(segments))
    
    # boxes = np.empty((len(segments), 4, 2), dtype=np.float32)
    rects = []
    
    #zip includes color for decommenting line 59 easily for testing
    for i, (color, segment) in enumerate(zip(colors, segments)): 
        gray = cv2.cvtColor(segment, cv2.COLOR_BGR2GRAY)
        
        _, thresh = cv2.threshold(gray, 250, 255, 1)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        proper_contours = []
        
        for cnt in contours:
            for point in cnt:
                proper_contours.append(point)
                
        proper_contours = np.array(proper_contours)
        
        rect = cv2.minAreaRect(proper_contours)
        rects.append(rect)
        
        # box = cv2.boxPoints(rect)
        # box = np.intp(box)
        
        # boxes[i] = box
        # copy = cv2.drawContours(copy, [box], 0, color, 2)
    return rects, colors

def findHorizontalSimilarBBoxes(rects, segments, epsilon_angle = 2, epsilon_distance = 100, epsilon_area = 0.2):
    '''
    Finds all the rectangles with given angle, distance, and area constrictions.
    Merges the rectangles, and return new_rects that is rects but with merged 
    rectangles removed and the merged_rects added
    '''
    # rect is in the form (center), (dimensions), angle
    
    min_area_ratio, max_area_ratio = 1 / (1 + epsilon_area), 1 + epsilon_area
    
    possible_group = []
    for i, rect in enumerate(rects):
        angle = rect[2]
        
        if angle >= 90 - epsilon_angle or angle < epsilon_angle:
            possible_group.append((i, rect))
    
    # print([i for i, rect in possible_group])
    
    # find the rectangle pair that are seperated by less than epsilon_disance
    edges = set()
    for i, rect in enumerate(rects):
        
        center = np.array(rect[0])
        w,h = rect[1]
        area = w * h
        angle = rect[2]

        add_matrix = np.array((w/2, 0)) if angle < abs(90-angle) else np.array((h/2, 0))
        
        for _i, _rect in enumerate(rects[i+1:]):
            _i = _i + i + 1
            _center = np.array(_rect[0])
            _w, _h = _rect[1]
            _area = _w * _h
            _angle = _rect[2]
            
            if abs(angleToZero(angle) - angleToZero(_angle)) > 2 * epsilon_angle \
                or angleToZero(angle) < 90 - epsilon_angle and angleToZero(angle) > epsilon_angle:
                # print(f'Angle Check: {i}-{_i}')
                continue
            
            _add_matrix = np.array((_w/2, 0)) if _angle < abs(90-_angle) else np.array((_h/2, 0))
            if center[0] < _center[0]:
                edge = center + add_matrix
                _edge = _center - _add_matrix
                
            else:
                edge = center - add_matrix
                _edge = _center + _add_matrix

            distance_x = abs(edge[0] - _edge[0])
            distance_y = abs(edge[1] - _edge[1])
            if distance_x > epsilon_distance or distance_y > epsilon_distance:

                # print(f'Distance Check: {i}-{_i}, {distance_x} {distance_y}')
                # print(f'{rect}\n{_rect}\n')
                continue
                
            ratio = area / _area
            
            if (ratio > max_area_ratio or ratio < min_area_ratio) \
                and (distance_x > epsilon_distance / 10 or distance_y > epsilon_distance / 10):
                # print(f'Area Check: {i}-{_i}, {ratio}')
                # print(f'{distance_x}, {distance_y}')
                continue
            
            edges.add((i, _i))
            
    if not edges:
        return rects, segments
    
    new_rects = []
    new_segments = []
    
    connected_rects = getConnectedComponents(edges, len(rects))
    for connected_rect in connected_rects:
        if len(connected_rect) == 1:
            new_rects.append(rects[connected_rect[0]])
            new_segments.append(segments[connected_rect[0]])
            continue
        
        merged_rects = []
        merged_segments = []
        for idx in connected_rect:
            merged_rects.append(rects[idx])
            merged_segments.append(segments[idx])
            
        merged_rect = mergeRects(merged_rects)
        new_rects.append(merged_rect)
        
        merged_segment = mergeSegments(merged_segments)
        new_segments.append(merged_segment)
    
    return new_rects, new_segments

def angleToZero(angle):
    '''
    Retunrs angle expressed between 0-45 by the closes angle it makes with
    any 4 cardinal directions in cartesian plane
    '''
    if angle > 45:
        return abs(90 - angle)
    
    return angle

def mergeSegments(segments):
    '''
    Returns overlay of all segments on top of one another,
    assumes segments are non-intersecting
    '''
    merged = np.subtract(255, segments[0])
    
    for segment in segments[1:]:
        segment = np.subtract(255, segment)
        merged = cv2.addWeighted(merged, 1, segment, 1, 0)
    
    return np.subtract(255, merged)
  
def mergeRects(rects):
    '''
    Returns the minimum bounding box in rect form of the given set of rectangles
    '''
    points = []    
    for rect in rects:
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        for point in box:
            points.append(point)
    # print(points)
    new_rect = cv2.minAreaRect(np.array(points))
    
    return new_rect

def mergeBoxes(boxes):
    '''
    Return the combined no rotation bounding rectangle from set 
    of bounding boxes. The result is the format of x, y, w, h
    where (x, y) is the top-left corner and w, h are dimensions.
    '''
    points = np.concatenate(boxes)
    rect = cv2.boundingRect(points)
    
    return rect

def clearAroundBoundingBox(image, bboxes, weight:int=5):
    '''
    From a list of bounding boxes, changes all the pixels 
    at most <weight> away from the line to white.
    
    Keyword arguments:
    image -- cv2.Image in BGR format
    bboxes -- list of bounding boxes
    weight -- The value to thicken the line (default 5)
    '''
    if not bboxes:
        return image
    
    for box in bboxes:
        box = np.intp(box)
        
        left_up = (np.min(box[:, 0]) - weight, np.min(box[:, 1]) - weight)
        right_down = (np.max(box[:, 0]) + weight, np.max(box[:, 1]) + weight)
        
        cv2.rectangle(image, left_up, right_down, (255, 255, 255), thickness=cv2.FILLED)
    
    return image
    
def getConnectedComponents(edges: list[tuple], length: int) -> list[list]:
    '''
    Standart edges to connected components graph theory function that appends
    list of connected edge indexes for every connected component and appends
    [idx] if no edge connection exists.
    '''
    visited = [False for _ in range(length)]
    
    adjacents = [[[vertex for vertex in edge if vertex != idx][0] \
                  for edge in edges if idx in edge] \
                 for idx in range(length)]
    
    def DFS(temp, v, visited):
        visited[v] = True
        
        temp.append(v)
        
        for i in adjacents[v]:
            
            if not visited[i]:
                
                temp = DFS(temp, i, visited)
        return temp
    
    cc = []
    
    for v in range(length):
        if not visited[v]:
            temp = []
            cc.append(DFS(temp, v, visited))
    
    return cc
                

    
    # # len(colors) >= len(rects) so zip is not strict
    # for rect, color in zip(rects, colors, strict=False):
        
    #     box = cv2.boxPoints(rect)
    #     box = np.intp(box)
        
    #     copy = cv2.drawContours(copy, [box.astype(int)], 0, color, 2)
    
    # showImage(copy, name=image_name)

def getAreaofBox(box):
    return np.linalg.norm(box[0] - box[2]) * np.linalg.norm(box[1] - box[3])

def isRectanglesIntersecting(rect1, rect2) -> bool:
    '''
    Check whether any vertex of rect2 is encapsulated
    by rect1. Equavilent to interesction between two
    rotated rectangles.
    
    IMPORTANT NOTE:
    If one rect is completely encapsulated by the other, result will 
    be false.If this is a desired check make sure:
    A(rect2) > A(rect1)
    
    Keyword arguements:
    rect1 -- rectangle of format [p1, p2, p3, p4]
    rect2 -- rectangle of farmat [p1, p2, p3, p4]
    where p_i is (i_x_pos, i_y_pos)
    '''
    for vertex in rect2:
        if cv2.pointPolygonTest(rect1, vertex, measureDist=False) >= 0:
            return True
    
    return False
