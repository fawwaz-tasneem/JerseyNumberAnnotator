import sys
import os
import json
import time

# Attempt to import PyQt5, exit if not installed
try:
    from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QFileDialog,
                                 QVBoxLayout, QHBoxLayout, QWidget, QProgressBar,
                                 QFrame, QCheckBox)
    from PyQt5.QtGui import QPixmap, QFont
    from PyQt5.QtCore import Qt
except ModuleNotFoundError:
    print("Error: PyQt5 is not installed. Please install it using 'pip install PyQt5'")
    sys.exit(1)

from image_loader import ImageLoader
from csv_handler import CSVHandler
from augmentor import Augmentor
from rename_dialog import RenameDialog  # For renaming images
from session_manager import SessionManager  # For session saving/resuming

class ImageAnnotator(QWidget):
    def __init__(self):
        """Initializes the Image Annotator GUI."""
        super().__init__()
        self.input_folder = ""  # Stores the input images folder
        self.session_manager = None  # Will be initialized when output folder is selected
        # Initialize current session data
        self.session_data = {
            "session_id": time.strftime("%Y%m%d_%H%M%S"),
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "images_annotated": 0,
            "suitable_images": 0  # Counter for suitable images in this session
        }
        self.initUI()
        self.image_loader = ImageLoader()
        self.csv_handler = CSVHandler()
        self.augmentor = Augmentor()
        self.output_folder = ""
        self.label_text = ""
        self.augmented_mode = False  # Toggle for augmentation mode

    def initUI(self):
        """Sets up the GUI layout and widgets."""
        self.setWindowTitle("Football Jersey Number Annotator")
        self.setGeometry(200, 100, 1000, 750)
        self.setStyleSheet("background-color: #2C2F33; color: #FFFFFF;")

        # Image display area (fixed 500x500)
        self.image_label = QLabel("No Image Loaded")
        self.image_label.setFixedSize(500, 500)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #7289DA; padding: 5px;")

        # Image name display label
        self.image_name_label = QLabel("No Image Loaded")
        self.image_name_label.setFont(QFont("Arial", 16))
        self.image_name_label.setAlignment(Qt.AlignCenter)
        self.image_name_label.setStyleSheet("padding: 5px;")

        # Number display
        self.number_display = QLabel("Enter Number")
        self.number_display.setFont(QFont("Arial", 40, QFont.Bold))
        self.number_display.setAlignment(Qt.AlignCenter)
        self.number_display.setStyleSheet("border: 2px solid #99AAB5; background-color: #23272A; padding: 10px;")
        self.number_display.setFixedSize(250, 120)

        # Session statistics display
        self.session_stats_label = QLabel("Session: --- | Labeled this session: 0 | Total suitable: 0")
        self.session_stats_label.setFont(QFont("Arial", 14))
        self.session_stats_label.setAlignment(Qt.AlignCenter)
        self.session_stats_label.setStyleSheet("padding: 5px;")

        # Buttons
        button_style = "padding: 10px; font-size: 14px; border-radius: 5px; background-color: #7289DA; color: white;"
        self.prev_btn = QPushButton("← Previous")
        self.next_btn = QPushButton("Next →")
        self.load_folder_btn = QPushButton("📂 Load Folder")
        self.select_output_btn = QPushButton("📁 Select Output Folder")
        self.rename_btn = QPushButton("🔄 Rename Images")
        self.label_btn = QPushButton("✔ Label (Enter)")
        self.save_session_btn = QPushButton("💾 Save Session")
        self.resume_session_btn = QPushButton("⟳ Resume Session")  # Button to resume previous session

        for btn in [self.prev_btn, self.next_btn, self.load_folder_btn, self.select_output_btn,
                    self.rename_btn, self.label_btn, self.save_session_btn, self.resume_session_btn]:
            btn.setStyleSheet(button_style)

        self.augment_mode_toggle = QCheckBox("Enable Augmentation")
        self.augment_mode_toggle.setStyleSheet("font-size: 16px;")
        self.progress = QProgressBar()

        # Button connections
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.next_btn.clicked.connect(self.show_next_image)
        self.load_folder_btn.clicked.connect(self.load_folder)
        self.select_output_btn.clicked.connect(self.select_output_folder)
        self.rename_btn.clicked.connect(self.rename_images)
        self.label_btn.clicked.connect(self.save_annotation)
        self.save_session_btn.clicked.connect(self.save_session)
        self.resume_session_btn.clicked.connect(self.resume_session)
        self.augment_mode_toggle.stateChanged.connect(self.toggle_augmentation)

        # Layout
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)

        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.image_name_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.number_display, alignment=Qt.AlignCenter)
        layout.addWidget(self.session_stats_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.load_folder_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.select_output_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.rename_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.augment_mode_toggle, alignment=Qt.AlignCenter)
        layout.addWidget(self.save_session_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.resume_session_btn, alignment=Qt.AlignCenter)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def toggle_augmentation(self, state):
        self.augmented_mode = state == Qt.Checked

    def update_session_stats(self):
        """Updates the session statistics display."""
        # Format session number as 3-digit
        session_no = self.session_manager.get_session_count() + 1 if self.session_manager else 1
        session_no_str = f"{session_no:03d}"
        current = self.session_data.get("images_annotated", 0)
        suitable = self.session_data.get("suitable_images", 0)
        total_prev = self.session_manager.get_total_suitable() if self.session_manager else 0
        self.session_stats_label.setText(
            f"Session #{session_no_str} | Labeled this session: {current} | Total suitable: {total_prev + suitable}"
        )

    def save_session(self):
        """
        Saves current session data to session_history.json (append-only)
        and closes the application.
        """
        self.session_data["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if self.session_manager:
            self.session_manager.add_session(self.session_data)
            print("Session saved.")
        else:
            print("Session manager not initialized.")
        self.update_session_stats()
        self.close()  # Close the application after saving

    def resume_session(self):
        """
        Resumes labeling from the last unlabeled image based on the CSV file.
        Initializes a new session with total suitable images set from previous sessions.
        """
        if not self.session_manager:
            print("Session manager not initialized.")
            return
        if self.session_manager.sessions:
            prev_total = self.session_manager.get_total_suitable()
            print(f"Resuming session. Total suitable images from previous sessions: {prev_total}")
            # Start a new session with previous suitable total in mind (current session counter starts at 0)
            self.session_data = {
                "session_id": time.strftime("%Y%m%d_%H%M%S"),
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "images_annotated": 0,
                "suitable_images": 0
            }
            if self.input_folder:
                self.image_loader.load_images(self.input_folder, self.output_folder, self)
                self.show_image()
            self.update_session_stats()
        else:
            print("No previous session found. Starting a new session.")
            self.session_data = {
                "session_id": time.strftime("%Y%m%d_%H%M%S"),
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "images_annotated": 0,
                "suitable_images": 0
            }
            self.update_session_stats()

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.input_folder = folder
            self.image_loader.load_images(folder, self.output_folder, self)
            self.show_image()

    def select_output_folder(self):
        """
        Opens a file dialog for selecting the output folder.
        Also initializes the session manager.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            print(f"Output folder set to: {self.output_folder}")
            self.session_manager = SessionManager(os.path.join(self.output_folder, "session_history.json"))
            self.update_session_stats()

    def rename_images(self):
        """Opens a dialog for renaming input images and refreshes the image list."""
        if not self.input_folder:
            print("Error: Input folder not set.")
            return

        from rename_dialog import RenameDialog
        dialog = RenameDialog(self.input_folder, self)
        if dialog.exec_() == dialog.Accepted:
            prefix, start_number = dialog.getValues()
            if not prefix or not start_number.isdigit():
                print("Error: Invalid prefix or starting number.")
                return
            start_number = int(start_number)
            self.perform_rename(self.input_folder, prefix, start_number)
            # Refresh image list after renaming
            self.image_loader.load_images(self.input_folder, self.output_folder, self)
            self.show_image()

    def perform_rename(self, folder, prefix, start_number):
        """
        Renames all images in the specified folder using the given prefix and starting number.
        New names will follow the format: prefix_XXXXXX.ext (6-digit number).
        """
        images = sorted([f for f in os.listdir(folder) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        number = start_number
        for old_name in images:
            ext = os.path.splitext(old_name)[1].lower()
            new_name = f"{prefix}_{str(number).zfill(6)}{ext}"
            old_path = os.path.join(folder, old_name)
            new_path = os.path.join(folder, new_name)
            try:
                os.rename(old_path, new_path)
                print(f"Renamed {old_name} to {new_name}")
            except Exception as e:
                print(f"Error renaming {old_name}: {e}")
            number += 1

    def show_prev_image(self):
        self.image_loader.prev_image()
        self.show_image()

    def show_next_image(self):
        self.image_loader.next_image()
        self.show_image()

    def show_image(self):
        image_path = self.image_loader.get_current_image()
        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Failed to load image")
            self.image_name_label.setText(os.path.basename(image_path))
        else:
            self.image_label.setText("No Image Loaded")
            self.image_name_label.setText("No Image Loaded")

    def save_annotation(self):
        """
        Saves the entered label for the current image.
        If the label is "--", it is interpreted as "unsuitable" (no augmentation).
        Suitable images (label not "unsuitable") increment the counter:
          - If augmentation is off, increment by 1.
          - If augmentation is on, increment by 10.
        Updates session statistics accordingly.
        """
        label = self.label_text.strip()
        if label == "--":
            label = "unsuitable"
        if not label or not self.output_folder:
            print("Error: No label entered or output folder not set.")
            return

        image_path = self.image_loader.get_current_image()
        if not image_path:
            print("Error: No image loaded.")
            return

        print(f"Saving annotation for {image_path} in {self.output_folder}")
        self.csv_handler.save_annotation(image_path, label, self.output_folder, self.session_data["session_id"])
        self.session_data["images_annotated"] += 1

        # Count suitable images if label is not "unsuitable"
        if label.lower() != "unsuitable":
            if self.augmented_mode:
                self.session_data["suitable_images"] += 10
            else:
                self.session_data["suitable_images"] += 1
        else:
            print("Image marked as unsuitable. No augmentation performed.")

        # Process augmented images only for suitable images when augmentation is enabled.
        if label.lower() != "unsuitable" and self.augmented_mode:
            print("Augmented mode is ON: Saving augmented images")
            aug_images = self.augmentor.augment_image(image_path, self.output_folder, True)
            for img in aug_images:
                self.csv_handler.save_annotation(img, label, self.output_folder, self.session_data["session_id"])
        self.label_text = ""
        self.show_next_image()
        self.update_session_stats()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            self.show_prev_image()
        elif key == Qt.Key_Right:
            self.show_next_image()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.save_annotation()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            self.label_text += chr(key)
            self.number_display.setText(self.label_text)
        elif key == Qt.Key_Minus:
            # If a minus is pressed and label already equals "-", then set to "unsuitable"
            if self.label_text == "-":
                self.label_text = "unsuitable"
                self.number_display.setText("unsuitable")
            else:
                self.label_text += "-"
                self.number_display.setText(self.label_text)
        elif key == Qt.Key_Backspace:
            self.label_text = self.label_text[:-1]
            self.number_display.setText(self.label_text if self.label_text else "Enter Number")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageAnnotator()
    window.show()
    sys.exit(app.exec_())
