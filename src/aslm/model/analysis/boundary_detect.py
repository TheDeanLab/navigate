from skimage import filters
from skimage.transform import downscale_local_mean
import numpy as np
import math

def has_tissue(image_data, x, y, width):
    # TODO: threshold value, other is_tissue() method
    threshold_value = 1000
    return np.any(image_data[x*width:(x+1)*width, y*width:(y+1)*width] > threshold_value)

def find_tissue_boundary_2d(image_data, mag_ratio):
    ds_img = downscale_local_mean(image_data, (mag_ratio, mag_ratio))
    # Threshold
    thresh_img = ds_img > filters.threshold_otsu(image_data)
    idx_x, idx_y = np.where(thresh_img)
    m = math.ceil(image_data.shape[0] / mag_ratio)
    n = math.ceil(image_data.shape[1] / mag_ratio)
    boundary = [None] * m
    for x, y in zip(idx_x, idx_y):
        if boundary[x] == None:
            boundary[x] = [y, y]
        else:
            boundary[x][1] = y
    return boundary

def binary_detect(img_data, boundary, width=1):
    m, n = img_data.shape
    m = math.ceil(m / width)
    n = math.ceil(n / width)

    def binary_search_func_left(row, left, right):
        while left < right:
            mid = (left + right) // 2
            if has_tissue(img_data, row, mid, width):
                right = mid
            else:
                left = mid + 1
        return right

    def binary_search_func_right(row, left, right):
        while left < right:
            mid = (left + right) // 2
            if has_tissue(img_data, row, mid, width):
                left = mid + 1
            else:
                right = mid
        return right - 1

    def find_tissue_range(row, left, right):
        temp = [(left, right)]
        while temp:
            temp2 = []
            for l, r in temp:
                mid = (l+r) // 2
                if has_tissue(img_data, row, mid, width):
                    return l, mid, r
                if mid > l+1:
                    temp2.append((l, mid))
                if r > mid+1:
                    temp2.append((mid, r))
            temp = temp2
        return -1, -1, -1

    def detect_row_boundary(row_id, left, right):
        is_tissue_left = has_tissue(img_data, row_id, left, width)
        is_tissue_right = has_tissue(img_data, row_id, right, width)

        if is_tissue_left and is_tissue_right:
            left_l, left_r = 0, left
            right_l, right_r = right, n
        elif is_tissue_left:
            left_l, left_r = 0, left
            right_l, right_r = left, right
        elif is_tissue_right:
            left_l, left_r = left, right
            right_l, right_r = right, n
        else:
            l, mid, r = find_tissue_range(row_id, left, right)     
            left_l, left_r = l, mid
            right_l, right_r = mid, r
        
        if left_l == -1:
            return None, None
        return binary_search_func_left(row_id, left_l, left_r), binary_search_func_right(row_id, right_l, right_r)

    def expand_row(row_id, limits, direction, boundary):
        for i in range(row_id, limits, direction):
            left, right = boundary[i][0], boundary[i][1]
            left = left-1 if left > 0 else 0
            right = right+1 if (right+1) < (n-1) else (n-1)
            l, r = detect_row_boundary(i+direction, left, right)
            if l == None:
                boundary[i+direction] = None
                break
            boundary[i+direction] = [l, r]


    new_boundary = boundary[:]
    top, bottom = None, None
    expand_top, expand_bottom = True, True

    for i, row in enumerate(new_boundary):
        if row is None:
            continue
        if expand_bottom == False:
            new_boundary[i] = None
            continue
        if len(row) < 2:
            row.append(row[0])
        left, right = detect_row_boundary(i, row[0], row[1])
        if left == None:
            new_boundary[i] = None
            if top == None:
                expand_top = False
            if bottom != None:
                expand_bottom = False
        else:
            new_boundary[i] = [left, right]

        if top == None:
            top = i
        bottom = i

    
    # detect top/bottom if necessary
    if expand_top:
        expand_row(top, 0, -1, new_boundary)

    if expand_bottom:
        expand_row(bottom, n-1, 1, new_boundary)

    return new_boundary


def map_boundary(boundary, direction=True):
    if direction:
        start, end, step = 0, len(boundary), 1
        offset = -1
    else:
        start, end, step = len(boundary)-1, -1, -1
        offset = 1
    
    def dp_shortest_path(start, end, step, offset=-1):
        dp_path = []
        dp_cost = [0, 0]
        visited = False
        for i in range(start, end, step):
            if boundary[i] is None:
                if visited:
                    break
                continue
            w = boundary[i][1] - boundary[i][0] + 1
            if not visited:
                visited = True
                dp_cost[0], dp_cost[1] = w, w
                dp_path.append([i, -1, -1])
            else:
                dp_path.append([i, 0, 0])
                for j in range(2):
                    l = abs(boundary[i+offset][0] - boundary[i][j])
                    r = abs(boundary[i+offset][1] - boundary[i][j])
                    if l < r:
                        dp_cost[1-j] += w + l
                        dp_path[-1][2-j] = 0
                    else:
                        dp_cost[1-j] += w + r
                        dp_path[-1][2-j] = 1

        # reverse path
        if dp_cost[0] < dp_cost[1]:
            idx = 0
        else:
            idx = 1
        path = []
        for item in reversed(dp_path):
            x = item[0]
            if idx == 0:
                path += map(lambda y: (x, y), range(boundary[x][0], boundary[x][1]+1))
            else:
                path += map(lambda y: (x, y), range(boundary[x][1], boundary[x][0]-1, -1))
            idx = item[idx+1]
        path.reverse()
        return path
        
    result = dp_shortest_path(start, end, step, offset)
    return result
   