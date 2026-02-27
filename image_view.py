from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPolygonF, QPen, QColor, QBrush, QPainter, QImage, QPixmap
import cv2
import numpy as np
from utils import cv2_to_qpixmap
from defect_item import DefectItem

class NGImageView(QGraphicsView):
    defect_extracted = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        # Use HandDrag for panning if needed, but here left click is drawing
        
        self.cv_image = None
        self.pixmap_item = None
        
        self.points = []
        self.current_polygon = None
        
        self.setMouseTracking(True)

    def set_image(self, cv_image):
        self.cv_image = cv_image
        self.scene.clear()
        
        pixmap = cv2_to_qpixmap(cv_image)
        if not pixmap.isNull():
            self.pixmap_item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        self.points = []
        self.current_polygon = None

    def mousePressEvent(self, event):
        if self.cv_image is None:
            return
        
        # Map mouse pos to scene coords
        pos = self.mapToScene(event.pos())
        
        # Ensure click is within image bounds
        if self.pixmap_item:
            if not self.pixmap_item.boundingRect().contains(pos):
                return

        if event.button() == Qt.LeftButton:
            self.points.append(pos)
            self.update_polygon()
        elif event.button() == Qt.RightButton:
            if len(self.points) > 2:
                self.finalize_polygon()
            else:
                self.reset_polygon()

    def update_polygon(self):
        if self.current_polygon:
            self.scene.removeItem(self.current_polygon)
            
        if len(self.points) > 0:
            poly = QPolygonF(self.points)
            self.current_polygon = self.scene.addPolygon(poly, QPen(Qt.red, 2), QBrush(QColor(255, 0, 0, 50)))

    def reset_polygon(self):
        self.points = []
        if self.current_polygon:
            self.scene.removeItem(self.current_polygon)
            self.current_polygon = None

    def finalize_polygon(self):
        if not self.points:
            return

        # Create mask
        h, w = self.cv_image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        pts = np.array([(int(p.x()), int(p.y())) for p in self.points], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        
        # Bounding rect
        x, y, w_rect, h_rect = cv2.boundingRect(pts)
        
        # Crop
        crop = self.cv_image[y:y+h_rect, x:x+w_rect]
        crop_mask = mask[y:y+h_rect, x:x+w_rect]
        
        # Create RGBA
        # Ensure crop is valid
        if crop.size == 0:
            self.reset_polygon()
            return

        b, g, r = cv2.split(crop)
        rgba = cv2.merge([b, g, r, crop_mask])
        
        # Convert to QPixmap
        height, width, channel = rgba.shape
        bytes_per_line = 4 * width
        # Make a copy to ensure data persists
        q_img = QImage(rgba.data, width, height, bytes_per_line, QImage.Format_RGBA8888).copy()
        pixmap = QPixmap.fromImage(q_img)
        
        self.defect_extracted.emit(pixmap)
        self.reset_polygon()

class OKImageView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag) # Allow selection
        
        self.pixmap_item = None
    
    def set_image(self, cv_image):
        self.scene.clear()
        
        pixmap = cv2_to_qpixmap(cv_image)
        if not pixmap.isNull():
            self.pixmap_item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
        
    def add_defect(self, pixmap):
        if not self.pixmap_item:
            return
            
        item = DefectItem(pixmap)
        self.scene.addItem(item)
        
        # Place in center of view or a default position
        center = self.mapToScene(self.viewport().rect().center())
        item.setPos(center - item.boundingRect().center())
        
        item.setSelected(True)
        item.setFocus()

    def get_result_image(self):
        if not self.pixmap_item:
            return QImage()
            
        rect = self.pixmap_item.boundingRect()
        img = QImage(int(rect.width()), int(rect.height()), QImage.Format_RGB888)
        img.fill(Qt.white)
        
        painter = QPainter(img)
        # Render the scene within the image rect
        self.scene.render(painter, target=QRectF(img.rect()), source=rect)
        painter.end()
        
        return img
