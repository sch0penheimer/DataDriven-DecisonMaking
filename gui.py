from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QButtonGroup, QCheckBox, QFileDialog, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import os
import cv2
import sys

from detection import PlateDetector
from ocr import PlateReader
from utility import enum

os.environ['QT_DEVICE_PIXEL_RATIO'] = '0'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCREEN_SCALE_FACTORS'] = '1'
os.environ['QT_SCALE_FACTOR'] = '1'

OCR_MODES = enum('TRAINED', 'TESSERACT')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Data Driven Decision Making")
        self.resize(800, 600)
        self.setMinimumSize(512, 512)

        self.setStyleSheet("background-color: black;")

        # Central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Layouts
        main_layout = QVBoxLayout(self.central_widget)
        top_layout = QHBoxLayout()
        middle_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # Top section: Image display
        self.car_image = QLabel("Car Image")
        self.car_image.setAlignment(Qt.AlignCenter)
        self.car_image.setStyleSheet("border: 1px solid white; color: white;")
        self.car_image.setScaledContents(True)

        self.car_detection = QLabel("Detection Result")
        self.car_detection.setAlignment(Qt.AlignCenter)
        self.car_detection.setStyleSheet("border: 1px solid white; color: white;")
        self.car_detection.setScaledContents(True)

        top_layout.addWidget(self.car_image)
        top_layout.addWidget(self.car_detection)

        # Middle section: Segmented characters
        self.segmented_characters = QLabel("Segmented Characters")
        self.segmented_characters.setAlignment(Qt.AlignCenter)
        self.segmented_characters.setStyleSheet("border: 1px solid white; color: white;")
        self.segmented_characters.setScaledContents(True)

        middle_layout.addWidget(self.segmented_characters)

        # Bottom section: Controls and OCR results
        self.load_image = QPushButton("Load Image")
        self.load_image.clicked.connect(self.on_click_load)
        self.load_image.setStyleSheet("color: white; background-color: gray;")

        self.start_detection = QPushButton("Start Detection")
        self.start_detection.clicked.connect(self.trained_anpr)
        self.start_detection.setStyleSheet("color: white; background-color: gray;")

        self.exit = QPushButton("Exit")
        self.exit.clicked.connect(self.exit_app)
        self.exit.setStyleSheet("color: white; background-color: gray;")

        self.cropped_plat = QLabel("Cropped Plate")
        self.cropped_plat.setAlignment(Qt.AlignCenter)
        self.cropped_plat.setStyleSheet("border: 1px solid white; color: white;")
        self.cropped_plat.setScaledContents(True)

        self.plate_ocr = QLabel("OCR Result")
        self.plate_ocr.setAlignment(Qt.AlignCenter)
        self.plate_ocr.setStyleSheet("border: 1px solid white; color: white;")
        self.plate_ocr.setTextInteractionFlags(Qt.TextSelectableByMouse)

        bottom_layout.addWidget(self.load_image)
        bottom_layout.addWidget(self.start_detection)
        bottom_layout.addWidget(self.exit)

        # OCR mode selection (only Moroccan Plate)
        self.trained_ocr = QCheckBox("Moroccan Plate (Custom OCR)")
        self.trained_ocr.setChecked(True)
        self.trained_ocr.setStyleSheet("color: white;")

        self.ocrButtonGroup = QButtonGroup()
        self.ocrButtonGroup.addButton(self.trained_ocr, 1)
        self.ocrButtonGroup.buttonClicked.connect(self.ocr_switch)

        ocr_layout = QHBoxLayout()
        ocr_layout.addWidget(self.trained_ocr)

        # Add widgets to main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.cropped_plat)
        main_layout.addLayout(middle_layout)  # Add segmented characters section
        main_layout.addWidget(self.plate_ocr)
        main_layout.addLayout(ocr_layout)
        main_layout.addLayout(bottom_layout)

        # Initialize variables
        self.image_path = ""
        self.ocr_mode = OCR_MODES.TRAINED

        # Load models
        self.detector = PlateDetector()
        self.detector.load_model("./weights/detection/yolov3-detection_final.weights", "./weights/detection/yolov3-detection.cfg")

        self.reader = PlateReader()
        self.reader.load_model("./weights/ocr/yolov3-ocr_final.weights", "./weights/ocr/yolov3-ocr.cfg")

    def on_click_load(self):
        self.clear_ocr()
        self.image_path = ""
        image = QFileDialog.getOpenFileName(self, 'Open File', '', "Image file (*.jpg *.png)")
        self.image_path = image[0]
        if self.image_path:
            pixmap = QPixmap(self.image_path)
            self.car_image.setPixmap(pixmap)

    def trained_anpr(self):
        if not self.image_path:
            return

        image, height, width, channels = self.detector.load_image(self.image_path)
        blob, outputs = self.detector.detect_plates(image)
        boxes, confidences, class_ids = self.detector.get_boxes(outputs, width, height, threshold=0.3)
        plate_img, LpImg = self.detector.draw_labels(boxes, confidences, class_ids, image)
        if LpImg:
            cv2.imwrite('./tmp/car_box.jpg', plate_img)
            cv2.imwrite('./tmp/plate_box.jpg', LpImg[0])
            self.car_detection.setPixmap(QPixmap('./tmp/car_box.jpg'))
            self.cropped_plat.setPixmap(QPixmap('./tmp/plate_box.jpg'))
            self.apply_ocr()

    def apply_ocr(self):
        if self.ocr_mode == OCR_MODES.TRAINED:
            image, height, width, channels = self.reader.load_image('./tmp/plate_box.jpg')
            blob, outputs = self.reader.read_plate(image)
            boxes, confidences, class_ids = self.reader.get_boxes(outputs, width, height, threshold=0.3)
            segmented, plate_text = self.reader.draw_labels(boxes, confidences, class_ids, image)
            cv2.imwrite('./tmp/plate_segmented.jpg', segmented)  # Save segmented characters image
            if plate_text:
                self.plate_ocr.setText(plate_text)
                self.plate_ocr.setStyleSheet("""
                border: 1px solid black;
                color: black;
                background-color: white;
                font-size: 18px;
                padding: 10px;
                text-align: center;
            """)
            self.segmented_characters.setPixmap(QPixmap('./tmp/plate_segmented.jpg'))  # Display segmented characters

    def ocr_switch(self, btn):
        if btn.text() == self.trained_ocr.text():
            self.ocr_mode = OCR_MODES.TRAINED
        self.clear_ocr()

    def clear_ocr(self):
        self.plate_ocr.clear()
        self.segmented_characters.clear()

    def exit_app(self):
        sys.exit(0)
