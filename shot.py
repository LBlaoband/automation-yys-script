import uiautomator2 as u2
import cv2
cv2.imwrite('img/full.png', u2.connect('127.0.0.1:16384').screenshot(format='opencv'))