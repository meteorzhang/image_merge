import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QPolygon, QBrush, QColor


class ImageLabel(QLabel):
    def __init__(self, parent=None, is_source=False):
        super().__init__(parent)
        self.is_source = is_source
        self.image = None
        self.qimage = None
        self.pixmap = None
        self.points = []
        self.is_drawing = False
        self.selected_region = None
        self.region_position = QPoint(0, 0)
        self.setMinimumSize(400, 400)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        
    def load_image(self, image_path):
        self.image = cv2.imread(image_path)
        if self.image is not None:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            height, width, channel = self.image.shape
            bytes_per_line = 3 * width
            self.qimage = QImage(self.image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(self.qimage)
            self.setPixmap(self.pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))
            return True
        return False
    
    def mousePressEvent(self, event):
        if self.pixmap is None:
            return
            
        if self.is_source:
            if event.button() == Qt.LeftButton:
                point = self.get_image_coordinates(event.pos())
                if point:
                    self.points.append(point)
                    self.update_display()
            elif event.button() == Qt.RightButton:
                if len(self.points) >= 3:
                    self.extract_region()
        else:
            if self.selected_region is not None:
                self.region_position = event.pos()
                self.update_display()
    
    def mouseMoveEvent(self, event):
        if not self.is_source and self.selected_region is not None and event.buttons() == Qt.LeftButton:
            self.region_position = event.pos()
            self.update_display()
    
    def get_image_coordinates(self, pos):
        if self.pixmap() is None:
            return None
            
        scaled_pixmap = self.pixmap()
        label_size = self.size()
        pixmap_size = scaled_pixmap.size()
        
        x_ratio = pixmap_size.width() / label_size.width()
        y_ratio = pixmap_size.height() / label_size.height()
        
        img_x = int(pos.x() * x_ratio)
        img_y = int(pos.y() * y_ratio)
        
        if 0 <= img_x < self.image.shape[1] and 0 <= img_y < self.image.shape[0]:
            return QPoint(img_x, img_y)
        return None
    
    def update_display(self):
        if self.pixmap is None:
            return
            
        scaled_pixmap = self.pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        painter = QPainter(scaled_pixmap)
        
        if self.is_source and len(self.points) > 0:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            
            scaled_points = []
            label_size = self.size()
            pixmap_size = scaled_pixmap.size()
            x_ratio = label_size.width() / pixmap_size.width()
            y_ratio = label_size.height() / pixmap_size.height()
            
            for point in self.points:
                scaled_x = point.x() * x_ratio
                scaled_y = point.y() * y_ratio
                scaled_points.append(QPoint(int(scaled_x), int(scaled_y)))
            
            if len(scaled_points) > 1:
                for i in range(len(scaled_points) - 1):
                    painter.drawLine(scaled_points[i], scaled_points[i + 1])
            
            for point in scaled_points:
                painter.drawEllipse(point, 3, 3)
        
        elif not self.is_source and self.selected_region is not None:
            painter.drawPixmap(self.region_position, self.selected_region)
        
        painter.end()
        self.setPixmap(scaled_pixmap)
    
    def extract_region(self):
        if len(self.points) < 3:
            return
            
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        points_array = np.array([[p.x(), p.y()] for p in self.points], np.int32)
        cv2.fillPoly(mask, [points_array], 255)
        
        masked_image = cv2.bitwise_and(self.image, self.image, mask=mask)
        
        x, y, w, h = cv2.boundingRect(points_array)
        region = masked_image[y:y+h, x:x+w]
        
        height, width, channel = region.shape
        bytes_per_line = 3 * width
        qimage = QImage(region.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.selected_region = QPixmap.fromImage(qimage)
        
        self.points = []
        self.update_display()
        
        return self.selected_region
    
    def get_composite_image(self):
        if self.image is None or self.selected_region is None:
            return None
            
        result = self.image.copy()
        
        scaled_pixmap = self.pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        label_size = self.size()
        pixmap_size = scaled_pixmap.size()
        x_ratio = pixmap_size.width() / label_size.width()
        y_ratio = pixmap_size.height() / label_size.height()
        
        img_x = int(self.region_position.x() * x_ratio)
        img_y = int(self.region_position.y() * y_ratio)
        
        region_height = self.selected_region.height()
        region_width = self.selected_region.width()
        
        qimg = self.selected_region.toImage()
        qimg = qimg.convertToFormat(QImage.Format_RGB888)
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        region_array = np.array(ptr).reshape(region_height, region_width, 3)
        
        y_end = min(img_y + region_height, result.shape[0])
        x_end = min(img_x + region_width, result.shape[1])
        region_h = y_end - img_y
        region_w = x_end - img_x
        
        if region_h > 0 and region_w > 0:
            mask = np.any(region_array[:region_h, :region_w] > 0, axis=2)
            result[img_y:y_end, img_x:x_end][mask] = region_array[:region_h, :region_w][mask]
        
        return result
    
    def reset(self):
        self.points = []
        self.selected_region = None
        self.region_position = QPoint(0, 0)
        if self.pixmap:
            self.setPixmap(self.pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))


class ImageCutoutTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片抠图和合成工具")
        self.setGeometry(100, 100, 1400, 800)
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        button_layout = QHBoxLayout()
        
        self.load_source_btn = QPushButton("加载第一张图片（抠图）")
        self.load_source_btn.clicked.connect(self.load_source_image)
        button_layout.addWidget(self.load_source_btn)
        
        self.load_target_btn = QPushButton("加载第二张图片（合成）")
        self.load_target_btn.clicked.connect(self.load_target_image)
        button_layout.addWidget(self.load_target_btn)
        
        self.clear_btn = QPushButton("清除选择")
        self.clear_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("保存合成图片")
        self.save_btn.clicked.connect(self.save_image)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        instruction_label = QLabel("操作说明：在左侧图片上左键点击选择多边形顶点，右键完成选择；拖拽选中的区域到右侧图片")
        instruction_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        main_layout.addWidget(instruction_label)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_layout = QVBoxLayout()
        left_label = QLabel("第一张图片（选择区域）")
        left_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(left_label)
        
        self.source_label = ImageLabel(is_source=True)
        left_layout.addWidget(self.source_label)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        right_layout = QVBoxLayout()
        right_label = QLabel("第二张图片（合成位置）")
        right_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(right_label)
        
        self.target_label = ImageLabel(is_source=False)
        right_layout.addWidget(self.target_label)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([700, 700])
        main_layout.addWidget(splitter)
    
    def load_source_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择第一张图片", "", 
                                                   "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            if self.source_label.load_image(file_path):
                QMessageBox.information(self, "成功", "图片加载成功！")
            else:
                QMessageBox.warning(self, "错误", "无法加载图片！")
    
    def load_target_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择第二张图片", "", 
                                                   "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            if self.target_label.load_image(file_path):
                QMessageBox.information(self, "成功", "图片加载成功！")
            else:
                QMessageBox.warning(self, "错误", "无法加载图片！")
    
    def clear_selection(self):
        self.source_label.reset()
        self.target_label.reset()
    
    def save_image(self):
        if self.target_label.image is None:
            QMessageBox.warning(self, "警告", "请先加载第二张图片！")
            return
            
        if self.target_label.selected_region is None:
            QMessageBox.warning(self, "警告", "请先从第一张图片选择区域并拖拽到第二张图片！")
            return
        
        result = self.target_label.get_composite_image()
        if result is not None:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", 
                                                        "PNG文件 (*.png);;JPEG文件 (*.jpg);;BMP文件 (*.bmp)")
            if file_path:
                result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
                if cv2.imwrite(file_path, result_bgr):
                    QMessageBox.information(self, "成功", "图片保存成功！")
                else:
                    QMessageBox.warning(self, "错误", "图片保存失败！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageCutoutTool()
    window.show()
    sys.exit(app.exec_())
