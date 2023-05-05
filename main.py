from os import system
import torch
import cv2
import numpy as np
from pathlib import Path
import easyocr
import pytesseract
from uuid import uuid4 as uuid
import requests

from time import time

def is_plate_valid(plate):
   try:
      res = requests.get(f'http://127.0.0.1:5000/is_registered?number_plate={plate}')
      data = res.json()
      return data['registered']
   except Exception as e:
      return False

def remove_non_alphanumeric(string):
   new_str = ""
   for char in string:
      if char.isalnum():
         new_str += char
   return new_str

def preprocess_image(image):
   # resize image
   RESIZE_FACTOR = 4
   width = int(image.shape[1] * RESIZE_FACTOR)
   height = int(image.shape[0] * RESIZE_FACTOR)
   dim = (width, height)
   image = cv2.resize(image, dim)

   # grayscale
   image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

   # gaussian blur
   image = cv2.GaussianBlur(image, (5,5), 0)

   # thresholding
   ret, image = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

   if (not ret):
      intentional_error += 'intentional'

   # dilation
   rect_kern = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
   image = cv2.dilate(image, rect_kern, iterations = 1)

   return image

def process_image_on_coordinates(image, top, bottom):
   x_top, y_top = top
   x_bottom, y_bottom = bottom

   # crop plate
   plate_img = image[y_top : y_bottom, x_top: x_bottom ]

   # preprocess
   # plate_img = preprocess_image(plate_img)

   # recognize text
   result = recognize_plate_with_easyocr(plate_img)
   # result = recognize_plate_with_pytesseract(plate_img)


   if (len(result) != 7):
      return ''

   return result

def format_text(text):
   return remove_non_alphanumeric(text).upper()

def recognize_plate_with_easyocr(img):
   detections = reader.readtext(img)
   res = ''

   for detection in detections:
      res += detection[1]

   res = format_text(res)
   return res

def recognize_plate_with_pytesseract(img):
   text = pytesseract.image_to_string(img, config='-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ --psm 8 --oem 3')
   return format_text(text)

def detect_from_disk_image(image_path):
   img = cv2.imread(image_path)
   return detect(img)

def get_numberplate_coordinates(image):
   result = model(image)
   # get plate coordinates
   if (len(result.xyxyn[0]) == 0):
      return None
   
   coordinates = (result.xyxyn[0][:, :-1])[0]

   x_shape = image.shape[1]
   y_shape = image.shape[0]
   top = (int(coordinates[0] * x_shape), int(coordinates[1] * y_shape))
   bottom = (int(coordinates[2] * x_shape), int(coordinates[3] * y_shape))

   return top, bottom

def detect(image):

   # get plate coordinates
   coordinates = get_numberplate_coordinates(image)

   if coordinates is None:
      return ''
   
   top, bottom = coordinates

   return process_image_on_coordinates(image, top, bottom)

def add_text_with_box(image, text, x, y):
   # Get the size of the text
   padding = 5
   font_size = 1
   text_size_x, text_size_y = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_size, thickness=2)[0]
   # Calculate the bounding box
   box_coords = ((x, y), (x + text_size_x + 2 * padding, y + text_size_y + 2 * padding))
   # Draw the bounding box
   cv2.rectangle(image, box_coords[0], box_coords[1], (0, 0, 255), -1)
   # Draw the text
   cv2.putText(image, text, (x + padding, y + padding + text_size_y), cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 255, 255), 2)

def draw_box(image, origin, width=50, height=50, color=(0,0,255),thickness=1):
   x, y = origin
   bottom = (x + width, y + height)
   cv2.rectangle(image, origin, bottom, color, thickness=thickness)



def crop_image(image, box, angle=0, transform_matrix=None):
    top, bottom, left, right = box

    x_top, y_top = top
    x_bottom, y_bottom = bottom

    # crop plate
    plate_img = image[y_top:y_bottom, x_top:x_bottom]

    if transform_matrix is not None:
        # apply perspective transform matrix
        src = np.float32([top, (x_bottom, y_top), bottom, (x_top, y_bottom)])
        dst = np.float32([(left, top[1]-y_top), (right, top[1]-y_top), (right, bottom[1]-y_top), (left, bottom[1]-y_top)])
        M = cv2.getPerspectiveTransform(src, dst)

        # apply rotation matrix
        center = ((left+right)//2, (top+bottom)//2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        combined_matrix = np.dot(M, np.vstack([rotation_matrix, [0, 0, 1]]))

        # apply combined transform matrix
        plate_img = cv2.warpPerspective(plate_img, combined_matrix, (right - left, bottom - top))

    return plate_img

def preprocess_image_demo(i):
   results_dir = f'images/preprocessed/plates_{i}'
   img_path = f'images/plates_{i}.jpeg'

   # create dir
   system(f'rm -rf {results_dir}')
   system(f'mkdir {results_dir}')

   # get coordinates
   image = cv2.imread(img_path)
   coordinates = get_numberplate_coordinates(image)

   # original image
   image = crop_image(image, coordinates)
   img_path = f'{results_dir}/1_original.png'
   cv2.imwrite(img_path, image)

   # side stuff
   up_tess =  recognize_plate_with_pytesseract(image)
   up_ocr =  recognize_plate_with_easyocr(image)

   # resized image
   RESIZE_FACTOR = 4
   width = int(image.shape[1] * RESIZE_FACTOR)
   height = int(image.shape[0] * RESIZE_FACTOR)
   dim = (width, height)
   image = cv2.resize(image, dim)
   img_path = f'{results_dir}/2_resized.png'
   cv2.imwrite(img_path, image)

   # grayscale
   image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
   img_path = f'{results_dir}/3_grayscaled.png'
   cv2.imwrite(img_path, image)

   # gaussian blur
   image = cv2.GaussianBlur(image, (5,5), 0)
   img_path = f'{results_dir}/4_blurred.png'
   cv2.imwrite(img_path, image)

   # thresholding
   ret, image = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

   if (not ret):
      intentional_error += 'intentional'

   img_path = f'{results_dir}/5_thresholded.png'
   cv2.imwrite(img_path, image)

   # dilation
   rect_kern = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
   image = cv2.dilate(image, rect_kern, iterations = 1)
   img_path = f'{results_dir}/6_dilation.png'
   cv2.imwrite(img_path, image)

   tess = recognize_plate_with_pytesseract(image)
   ocr  = recognize_plate_with_easyocr(image)

   print(f'plates_{i}: {ocr} ___ {tess}: {up_ocr} ___ {up_tess}')



system('clear')


reader = easyocr.Reader(['en'])
model_path = Path("best.pt")
cpu_or_cuda = "cpu"  # choose device; "cpu" or "cuda"(if cuda is available)
device = torch.device(cpu_or_cuda)
# model = torch.hub.load('ultralytics/yolov5', 'custom', path= model_path, force_reload=True)
model = torch.hub.load('./', 'custom', source ='local', path=model_path,force_reload=True)
model = model.to(device)

video_path = 'm3.mp4'
#video_path = 0
vc = cv2.VideoCapture(video_path)

last_valid_plate = None
last_valid_plate_time = 0


while (True):

   success, frame = vc.read()

   if (not success):
      vc = cv2.VideoCapture(video_path)
      continue

   # get plate coordinates
   coordinates = get_numberplate_coordinates(frame)

   if (coordinates is not None):
  
      top, bottom = coordinates

      x_top, y_top = top
      x_bottom, y_bottom = bottom

      plate = process_image_on_coordinates(frame, top, bottom)

      if (len(plate) > 0):
         add_text_with_box(frame, plate, x_top, y_bottom)

         height = y_bottom - y_top
         width  = x_bottom - x_top

         draw_box(frame, top, width=width, height=height)

         plate_is_valid = is_plate_valid(plate)

         if (plate_is_valid):

            if (plate == last_valid_plate) and (last_valid_plate_time > time() - 20):
               pass
            else:
        
               last_valid_plate = plate
               last_valid_plate_time = time()

      
   cv2.imshow('Video Feed', frame)
   cv2.waitKey(1)
