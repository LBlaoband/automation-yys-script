import uiautomator2 as u2
import cv2
import time
timestamp = time.strftime("%Y%m%d_%H%M%S")
cv2.imwrite(f'yolo/shot_{timestamp}.png', u2.connect('127.0.0.1:16384').screenshot(format='opencv'))