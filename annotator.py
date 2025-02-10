import sys
import os
import PyQt5

# Attempt to import PyQt5, exit if not installed
try:
    from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QFileDialog, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QProgressBar
    from PyQt5.QtGui import QPixmap
except ModuleNotFoundError:
    print("Error: PyQt5 is not installed. Please install it using 'pip install PyQt5'")
    sys.exit(1)

from image_loader import ImageLoader  # Handles loading and navigating images
from csv_handler import CSVHandler  # Handles saving annotations to a CSV file
from augmentor import Augmentor  # Handles augmentations like rotation, noise, etc.

class ImageAnnotator(QWidget):
    def __init__(self):
        """
        Initializes the Image Annotator GUI.
        """
        super().__init__()
        self.initUI()
        self.image_loader = ImageLoader()
        self.csv_handler = CSVHandler()
        self.augmentor = Augmentor()
        self.output_folder = ""  # Folder where annotated images and CSV will be saved
    
    def initUI(self):
        """
        Sets up the GUI layout and widgets.
        """
        self.setWindowTitle("Football Jersey Number Annotator")
        self.setGeometry(200, 100, 800, 600)
        
        # Image display area
        self.image_label = QLabel("No Image Loaded")
        self.image_label.setFixedSize(400, 400)
        
        # Navigation and action buttons
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.load_folder_btn = QPushButton("Load Folder")
        self.select_output_btn = QPushButton("Select Output Folder")
        self.label_input = QLineEdit()  # User enters label here
        self.label_btn = QPushButton("Label (Enter)")
        self.progress = QProgressBar()  # Progress indicator
        
        # Connect buttons to their respective functions
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.next_btn.clicked.connect(self.show_next_image)
        self.load_folder_btn.clicked.connect(self.load_folder)
        self.select_output_btn.clicked.connect(self.select_output_folder)
        self.label_btn.clicked.connect(self.save_annotation)
        
        # Layout setup
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.load_folder_btn)
        layout.addWidget(self.select_output_btn)
        layout.addWidget(self.label_input)
        layout.addWidget(self.label_btn)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
    def load_folder(self):
        """
        Opens a file dialog for the user to select the folder containing images.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.image_loader.load_images(folder)
            self.show_image()
    
    def select_output_folder(self):
        """
        Opens a file dialog for selecting the output folder.
        """
        self.output_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
    
    def show_image(self):
        """
        Displays the current image in the GUI.
        """
        image_path = self.image_loader.get_current_image()
        if image_path:
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(400, 400))
    
    def show_next_image(self):
        """
        Advances to the next image and updates the display.
        """
        self.image_loader.next_image()
        self.show_image()
    
    def show_prev_image(self):
        """
        Goes back to the previous image and updates the display.
        """
        self.image_loader.prev_image()
        self.show_image()
    
    def save_annotation(self):
        """
        Saves the entered label for the current image and applies augmentations.
        """
        label = self.label_input.text().strip()
        if not label:
            return  # Exit if no label is entered
        
        image_path = self.image_loader.get_current_image()
        if not image_path or not self.output_folder:
            return  # Exit if no image is selected or output folder is missing
        
        # Save annotation to CSV
        self.csv_handler.save_annotation(image_path, label, self.output_folder)
        
        # Apply augmentations and save those as well
        aug_images = self.augmentor.augment_image(image_path, self.output_folder)
        for img in aug_images:
            self.csv_handler.save_annotation(img, label, self.output_folder)
        
        # Clear input field and move to the next image
        self.label_input.clear()
        self.show_next_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageAnnotator()
    window.show()
    sys.exit(app.exec_())
