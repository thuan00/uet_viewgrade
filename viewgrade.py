from pdf2image import convert_from_path, convert_from_bytes
import requests
import cv2
import numpy as np
import re
import pytesseract


# config
DPI = 200  #-> default img shape 2339x1654, do not change this
BIN_INV_THRESHOLD = 192
#
VERTICAL_FILTER = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
ROW_FILTER = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
KERNEL_3x3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
KERNEL_5x5 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
#
HEADER, FOOTER = 300, 2205
HOUGH_LINES_THRESHOLD = 300
MIN_THETA, MAX_THETA = [-np.pi/18, np.pi/18]  #-10, 10 degree
#
TONGDIEM_EXPECTED_REGION = 1300, 270, 1650, 750,  #x1 y1 x2 y2
PATTERN_TONGDIEM = cv2.imread('./data/pattern_tongdiem.png', 0)
PATTERN_H, PATTERN_W = PATTERN_TONGDIEM.shape
TONGDIEM_COLUMN_WIDTH = 120
#
TESSERACT_NUMBER_CONFIG = "-l eng --oem 1 --psm 8 tessedit_char_whitelist=0123456789."
#GRADE_SCALE = [4.0, 5.0, 5.5, 6.5, 7.0, 8.0, 8.5, 9.0] #F,D,D+,C,C+,B,B+,A,A+


def is_local_file(path):
    return path[:4] != 'http'

def pdf_to_np(path):
    if is_local_file(path):
        pil_images = convert_from_path(path, dpi=DPI, grayscale=True)
    else:
        print('Requesting pdf file from server... ', end='')
        response = requests.get(path)
        print('Done')
        assert response.status_code == 200, 'Oops, got some problems requesting the server'
        pil_images = convert_from_bytes(response.content, dpi=DPI, grayscale=True)

    np_images = [np.array(pil_images[i]) for i in range(len(pil_images))]
    return np_images


def deskew(img):
    (thresh, img_bin) = cv2.threshold(img, BIN_INV_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    img_bin = cv2.morphologyEx(img_bin, cv2.MORPH_CLOSE, KERNEL_3x3)
    img_bin = cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, VERTICAL_FILTER)

    lines = cv2.HoughLines(img_bin[HEADER:FOOTER], 1, np.pi/360, HOUGH_LINES_THRESHOLD, min_theta=MIN_THETA, max_theta=MAX_THETA)
    if lines is None or len(lines) < 5:
        return img, float('inf') # indicates a failed deskew, when the img doesn't contain enough lines for deskewing
    
    # take average of the first 5 lines
    angle = np.mean(lines[:5,:,1])*180/np.pi
    # if skewed angle is considerable, deskew
    if angle > 1.0:
        h, w = img.shape
        center_point = (w//2, h//2)
        deskewed_img = cv2.warpAffine(img, cv2.getRotationMatrix2D(center_point,angle_degree,1.0), (w, h), borderValue=255)
        img = deskewed_img

    return img, angle

    
def detect_grade_column(deskewed_img):
    ''' return: (xmin, ymin, xmax, ymax) - the bounding box for the grade column
    '''
    x1,y1, x2,y2 = TONGDIEM_EXPECTED_REGION
    tongdiem_expected_region = 255-deskewed_img[y1:y2,x1:x2]
    res = cv2.matchTemplate(tongdiem_expected_region, PATTERN_TONGDIEM, cv2.TM_CCORR)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    x, y = max_loc
    x, y = x+x1+PATTERN_W//2, y+y1+PATTERN_H+10  #now under the middle of tongdiem
    x1, y1 = x-TONGDIEM_COLUMN_WIDTH//2, y
    x2, y2 = x1+TONGDIEM_COLUMN_WIDTH, FOOTER
    
    return x1,y1, x2,y2


def get_rows(column):
    ''' column: np ndarray - cropped grades column
        return: list of bounding boxes for the grade in each rows
    '''
    (thresh, column_bin) = cv2.threshold(column, BIN_INV_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    column_bin = cv2.morphologyEx(column_bin, cv2.MORPH_CLOSE, ROW_FILTER, borderValue=0)
    column_bin = cv2.morphologyEx(column_bin, cv2.MORPH_OPEN, KERNEL_5x5)

    contours, hierarchy = cv2.findContours(column_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    grade_bboxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)  #h should typically be 18px
        if h <= 8: #discard
            pass
        elif h <= 12: #add border: 7px
            grade_bboxes.append((x-7, y-7, x+w+7, y+h+7)) 
        else: #add border: 5px
            grade_bboxes.append((x-5, y-5, x+w+5, y+h+5)) 
    
    return grade_bboxes
    

def read_grades(path):
    ''' path: string - path to the single pdf file
        return: list of final grades
    '''
    grades = []
    images = pdf_to_np(path)
    for i,img in enumerate(images):

        img, angle = deskew(img)
        if angle == float('inf'):
            continue
        
        x1,y1, x2,y2 = detect_grade_column(img)
        column = img[y1:y2,x1:x2]

        grade_bboxes = get_rows(column)
        for x1,y1, x2,y2 in grade_bboxes:
            ROI = column[y1:y2,x1:x2]
            grade = ocr(ROI)
            grades.append(grade)
        # try multi thread
    return grades


def ocr(ROI):
    ''' ROI: np ndarray - the grade cropped from each row
        return: float - -1.0 for unrecognized
    '''
    grade = -1.0
    try:
      text = pytesseract.image_to_string(ROI, config=TESSERACT_NUMBER_CONFIG)
      text = re.sub("[^0-9.]", "", text)  #exclude '\n\x0c' and failed ocr
      grade = float(text)
      if grade > 10: grade /= 10
    except:
      pass
    return grade


def count_grades(grades):
    grade_map = {
        'A+': 0,
        'A' : 0,
        'B+': 0,
        'B' : 0,
        'C+': 0,
        'C' : 0,
        'D+': 0,
        'D' : 0,
        'F' : 0,
        'N/A': 0,
    }
    for grade in grades:
        #binary_search(GRADE_SCALE, grade, 0, n)
        if grade >= 9:
            grade_map['A+'] += 1
        elif grade >= 8.5:
            grade_map['A']  += 1
        elif grade >= 8.0:
            grade_map['B+'] += 1
        elif grade >= 7.0:
            grade_map['B']  += 1
        elif grade >= 6.5:
            grade_map['C+'] += 1
        elif grade >= 5.5:
            grade_map['C']  += 1
        elif grade >= 5.0:
            grade_map['D+'] += 1
        elif grade >= 4.0:
            grade_map['D']  += 1
        elif grade >= 0.0:
            grade_map['F']  += 1
        else:
            grade_map['N/A']+= 1
    return grade_map



if __name__ == '__main__':
    
    while True:
        path = input('\nEnter path: ')
        if path == 'q':
            quit()

        grades = read_grades(path)
        grade_map = count_grades(grades)

        n_grades = len(grades)
        print('\nTotal recognized:', n_grades)
        print('Grade: %')
        for grade, count in grade_map.items():
            print(f' {grade.ljust(3)} : {round(count*100/n_grades) if count != 0 else "-"}')

        #breakpoint()