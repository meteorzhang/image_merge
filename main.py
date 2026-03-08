import sys
import os
import json
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QFileDialog, 
                             QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                             QListWidget, QListWidgetItem, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, QLabel, 
                             QMessageBox, QComboBox, QGraphicsItem)
from PyQt5.QtCore import Qt, QMimeData, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QImage, QDrag, QPainter, QPolygonF, QTransform, QPen, QColor, QIcon

from utils import extract_defects, create_synthesized_json

class DefectListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(self.iconSize() * 2) # Larger icons
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
            
        mime_data = QMimeData()
        # Store file path in mime data
        file_path = item.data(Qt.UserRole)
        mime_data.setText(file_path)
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(item.icon().pixmap(50, 50))
        drag.exec_(Qt.CopyAction)

class DefectGraphicsItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, json_path, label):
        super().__init__(pixmap)
        self.json_path = json_path
        self.label = label
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable | 
                      QGraphicsItem.ItemSendsGeometryChanges)
        
        # Load original points from JSON
        self.original_points = self.load_points()
        
        # Center the item origin
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)

    def load_points(self):
        points = []
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Assuming one shape per defect file as per extraction logic
                if data.get('shapes'):
                    points = data['shapes'][0]['points']
            except Exception as e:
                print(f"Error loading points: {e}")
        return points

    def get_scene_points(self):
        # Convert original points to QPolygonF
        poly = QPolygonF([QPointF(p[0], p[1]) for p in self.original_points])
        # Map to scene
        scene_poly = self.mapToScene(poly)
        
        # Convert back to list of lists
        result = []
        for i in range(scene_poly.count()):
            pt = scene_poly.at(i)
            result.append([pt.x(), pt.y()])
        return result

class SynthesisView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.bg_item = None
        self.current_scale = 1.0

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if not self.bg_item:
            return
            
        file_path = event.mimeData().text()
        if os.path.exists(file_path):
            # Load image
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return
                
            # Find corresponding JSON
            json_path = os.path.splitext(file_path)[0] + ".json"
            
            # Extract label from folder name
            label = os.path.basename(os.path.dirname(file_path))
            
            item = DefectGraphicsItem(pixmap, json_path, label)
            pos = self.mapToScene(event.pos())
            item.setPos(pos - QPointF(pixmap.width()/2, pixmap.height()/2))
            self.scene.addItem(item)
            item.setSelected(True)

    def wheelEvent(self, event):
        # If an item is selected, scale it
        items = self.scene.selectedItems()
        if items:
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            for item in items:
                if isinstance(item, DefectGraphicsItem):
                    item.setScale(item.scale() * factor)
        else:
            # Zoom view if no item selected (optional, but good UX)
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        items = self.scene.selectedItems()
        if items:
            step = 5
            for item in items:
                if isinstance(item, DefectGraphicsItem):
                    if event.key() == Qt.Key_R:
                        item.setRotation(item.rotation() + step)
                    elif event.key() == Qt.Key_L:
                        item.setRotation(item.rotation() - step)
                    elif event.key() == Qt.Key_Delete:
                        self.scene.removeItem(item)
        super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Defect Synthesis Tool")
        self.resize(1200, 800)
        
        self.defect_library_path = "defect_library"
        if not os.path.exists(self.defect_library_path):
            os.makedirs(self.defect_library_path)

        self.init_ui()

    def init_ui(self):
        # Menu Bar
        menubar = self.menuBar()
        
        extract_action = QAction('Defect Extraction', self)
        extract_action.triggered.connect(self.extract_defects_ui)
        menubar.addAction(extract_action)
        
        import_action = QAction('Import Defect Library', self)
        import_action.triggered.connect(self.import_library)
        menubar.addAction(import_action)
        
        load_ok_action = QAction('Load OK Image', self)
        load_ok_action.triggered.connect(self.load_ok_image)
        menubar.addAction(load_ok_action)
        
        save_action = QAction('Save Image', self)
        save_action.triggered.connect(self.save_synthesis)
        menubar.addAction(save_action)

        # Main Layout
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.load_defect_list)
        left_layout.addWidget(QLabel("Defect Category:"))
        left_layout.addWidget(self.category_combo)
        
        self.defect_list = DefectListWidget()
        left_layout.addWidget(self.defect_list)
        
        splitter.addWidget(left_widget)
        
        # Right Panel
        self.view = SynthesisView()
        splitter.addWidget(self.view)
        
        splitter.setStretchFactor(1, 3) # Right side bigger
        
        self.setCentralWidget(splitter)
        
        # Initial Load
        self.refresh_library()

    def extract_defects_ui(self):
        # Select Directory
        dir_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not dir_path:
            return

        count = 0
        total_images = 0
        
        # Iterate through files in the directory
        for filename in os.listdir(dir_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                total_images += 1
                image_path = os.path.join(dir_path, filename)
                
                # Assume JSON has same base name
                base_name = os.path.splitext(filename)[0]
                json_path = os.path.join(dir_path, base_name + ".json")
                
                if os.path.exists(json_path):
                    if extract_defects(image_path, json_path, self.defect_library_path):
                        count += 1
        
        if count > 0:
            QMessageBox.information(self, "Success", f"Processed {count} images successfully out of {total_images} found.")
            self.refresh_library()
        else:
            QMessageBox.warning(self, "Result", f"No defects extracted. Found {total_images} images.")

    def import_library(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Defect Library Folder")
        if dir_path:
            self.defect_library_path = dir_path
            self.refresh_library()

    def refresh_library(self):
        self.category_combo.clear()
        if not os.path.exists(self.defect_library_path):
            return
            
        categories = [d for d in os.listdir(self.defect_library_path) 
                      if os.path.isdir(os.path.join(self.defect_library_path, d))]
        self.category_combo.addItems(categories)
        self.load_defect_list()

    def load_defect_list(self):
        self.defect_list.clear()
        category = self.category_combo.currentText()
        if not category:
            return
            
        cat_path = os.path.join(self.defect_library_path, category)
        if not os.path.exists(cat_path):
            return
            
        for f in os.listdir(cat_path):
            if f.lower().endswith(('.png', '.jpg', '.bmp')):
                file_path = os.path.join(cat_path, f)
                item = QListWidgetItem(os.path.basename(f))
                item.setIcon(QIcon(file_path))
                item.setData(Qt.UserRole, file_path)
                self.defect_list.addItem(item)

    def load_ok_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select OK Image", "", "Images (*.png *.jpg *.bmp)")
        if path:
            pixmap = QPixmap(path)
            self.view.scene.clear()
            self.view.bg_item = self.view.scene.addPixmap(pixmap)
            self.view.setSceneRect(QRectF(pixmap.rect()))

    def save_synthesis(self):
        if not self.view.bg_item:
            return

        # Generate timestamp filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_dir = "synthesized"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        save_path = os.path.join(output_dir, f"{timestamp}.png")
        
        # 1. Save Image (Render Scene)
        # We need to render only the scene rect
        rect = self.view.sceneRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        self.view.scene.render(painter)
        painter.end()
        
        image.save(save_path)
        
        # 2. Save JSON
        items_data = []
        for item in self.view.scene.items():
            if isinstance(item, DefectGraphicsItem):
                points = item.get_scene_points()
                items_data.append({
                    "label": item.label,
                    "points": points,
                    "shape_type": "polygon"
                })
        
        # Use helper from utils
        create_synthesized_json(None, save_path, items_data)
        
        QMessageBox.information(self, "Success", f"Saved to {save_path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
