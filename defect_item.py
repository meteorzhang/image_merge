from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QColor, QTransform, QBrush

class DefectItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable | 
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        
        self.setAcceptHoverEvents(True)
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
        
        # Scale and Rotation state
        self.scale_factor = 1.0
        self.rotation_angle = 0.0
        
        # Center the origin for easier rotation/scaling
        self.setTransformOriginPoint(self.boundingRect().center())

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        
        if self.isSelected():
            # Draw a dashed border when selected
            pen = QPen(QColor(0, 120, 215), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def wheelEvent(self, event):
        # Zoom with scroll
        factor = 1.1 if event.delta() > 0 else 0.9
        self.scale_factor *= factor
        self.update_transform()
        event.accept()

    def keyPressEvent(self, event):
        # Rotate with keys (R/L) or Delete
        if event.key() == Qt.Key_Delete:
            scene = self.scene()
            if scene:
                scene.removeItem(self)
        elif event.key() == Qt.Key_R:
            # Rotate clockwise
            self.rotation_angle += 5
            self.update_transform()
        elif event.key() == Qt.Key_L:
            # Rotate counter-clockwise
            self.rotation_angle -= 5
            self.update_transform()
        else:
            super().keyPressEvent(event)

    def update_transform(self):
        # Reset transform and apply new scale/rotation
        # We need to handle the origin point carefully
        
        # Center of the item
        center = self.boundingRect().center()
        
        # Create transform
        trans = QTransform()
        trans.translate(center.x(), center.y())
        trans.rotate(self.rotation_angle)
        trans.scale(self.scale_factor, self.scale_factor)
        trans.translate(-center.x(), -center.y())
        
        self.setTransform(trans)
