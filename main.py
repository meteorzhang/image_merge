import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSplitter, QLabel, QFileDialog, QToolBar, QAction, QStatusBar, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from image_view import NGImageView, OKImageView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Defect Synthesis Tool")
        self.resize(1200, 800)
        
        self.init_ui()
        
    def init_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter for Views
        splitter = QSplitter(Qt.Horizontal)
        
        # NG Container
        ng_container = QWidget()
        ng_layout = QVBoxLayout(ng_container)
        ng_label = QLabel("NG Image (Left Click to Draw, Right Click to Finish)")
        ng_label.setAlignment(Qt.AlignCenter)
        self.ng_view = NGImageView()
        ng_layout.addWidget(ng_label)
        ng_layout.addWidget(self.ng_view)
        
        # OK Container
        ok_container = QWidget()
        ok_layout = QVBoxLayout(ok_container)
        ok_label = QLabel("OK Image (Drag/Scroll/Rotate Defect)")
        ok_label.setAlignment(Qt.AlignCenter)
        self.ok_view = OKImageView()
        ok_layout.addWidget(ok_label)
        ok_layout.addWidget(self.ok_view)
        
        splitter.addWidget(ng_container)
        splitter.addWidget(ok_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Actions
        load_ng_action = QAction("Load NG Image", self)
        load_ng_action.triggered.connect(self.load_ng_image)
        self.toolbar.addAction(load_ng_action)
        
        load_ok_action = QAction("Load OK Image", self)
        load_ok_action.triggered.connect(self.load_ok_image)
        self.toolbar.addAction(load_ok_action)
        
        self.toolbar.addSeparator()
        
        reset_ng_action = QAction("Reset NG Polygon", self)
        reset_ng_action.triggered.connect(self.ng_view.reset_polygon)
        self.toolbar.addAction(reset_ng_action)
        
        save_action = QAction("Save Result", self)
        save_action.triggered.connect(self.save_result)
        self.toolbar.addAction(save_action)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Load images to start.")
        
        # Signals
        self.ng_view.defect_extracted.connect(self.on_defect_extracted)

    def load_ng_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open NG Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif)")
        if path:
            # Read as color to ensure 3 channels for consistency
            img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                self.ng_view.set_image(img)
                self.status_bar.showMessage(f"Loaded NG Image: {path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

    def load_ok_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open OK Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif)")
        if path:
            img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                self.ok_view.set_image(img)
                self.status_bar.showMessage(f"Loaded OK Image: {path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

    def on_defect_extracted(self, pixmap):
        if self.ok_view.pixmap_item:
            self.ok_view.add_defect(pixmap)
            self.status_bar.showMessage("Defect extracted and added to OK Image. Use mouse to move/scale, 'R'/'L' to rotate, 'Delete' to remove.")
        else:
            QMessageBox.warning(self, "Warning", "Please load an OK image first.")

    def save_result(self):
        if not self.ok_view.scene.items():
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Save Result", "result.jpg", "JPEG Images (*.jpg);;PNG Images (*.png)")
        if path:
            img = self.ok_view.get_result_image()
            if not img.isNull():
                img.save(path)
                self.status_bar.showMessage(f"Saved result to {path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to generate result image.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
