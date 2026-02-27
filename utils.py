import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap

def cv2_to_qpixmap(cv_img):
    """Convert OpenCV image (BGR/BGRA) to QPixmap."""
    if cv_img is None:
        return QPixmap()
    
    height, width = cv_img.shape[:2]
    
    # Handle Grayscale
    if len(cv_img.shape) == 2:
        q_img = QImage(cv_img.data, width, height, width, QImage.Format_Grayscale8)
        return QPixmap.fromImage(q_img)
        
    channels = cv_img.shape[2]
    
    if channels == 3:
        # OpenCV BGR -> Qt RGB
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * width
        q_img = QImage(rgb_img.data, width, height, bytes_per_line, QImage.Format_RGB888).copy()
        return QPixmap.fromImage(q_img)
    elif channels == 4:
        # OpenCV BGRA -> Qt RGBA
        # Note: QImage.Format_RGBA8888 expects RGBA, OpenCV uses BGRA by default or when adding alpha
        # We need to ensure channel order is correct for Qt
        # Standard cv2.imread with -1 returns BGRA
        # QImage Format_RGBA8888 usually interprets data as R,G,B,A
        # So we need to convert BGRA -> RGBA
        rgba_img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        bytes_per_line = 4 * width
        q_img = QImage(rgba_img.data, width, height, bytes_per_line, QImage.Format_RGBA8888).copy()
        return QPixmap.fromImage(q_img)
        
    return QPixmap()

def qimage_to_cv2(q_img):
    """Convert QImage to OpenCV image."""
    # Convert QImage to format that matches OpenCV expectations (e.g., RGBA or RGB)
    q_img = q_img.convertToFormat(QImage.Format_RGBA8888)
    width = q_img.width()
    height = q_img.height()
    
    ptr = q_img.bits()
    ptr.setsize(height * width * 4)
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
    
    # RGBA -> BGRA (OpenCV default for 4 channel) or BGR
    return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR) # Return BGR for saving as JPG usually, or handle Alpha if needed
