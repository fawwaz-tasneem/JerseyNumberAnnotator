import os
from csv_handler import CSVHandler
from PyQt5.QtWidgets import QMessageBox

class ImageLoader:
    def __init__(self):
        self.image_list = []
        self.index = 0
        self.annotations = {}

    def load_images(self, folder, output_folder, parent_widget):
        """
        Loads images from a directory and resumes from the first unlabeled image.
        """
        self.image_list = sorted([os.path.join(folder, img)
                                  for img in os.listdir(folder)
                                  if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if output_folder:
            csv_handler = CSVHandler()
            self.annotations = csv_handler.load_existing_annotations(output_folder)
        else:
            self.annotations = {}
        self.index = self.find_resume_index()
        if parent_widget and self.image_list:
            if self.index >= len(self.image_list):
                QMessageBox.information(parent_widget, "All Done",
                                        "All images in this folder have already been annotated.")
            elif self.index > 0:
                QMessageBox.information(parent_widget, "Resuming",
                                        f"Found {self.index} annotated image(s). "
                                        f"Resuming from image {self.index + 1} of {len(self.image_list)}.")

    def find_resume_index(self):
        """Finds the first unannotated image index."""
        for i, image_path in enumerate(self.image_list):
            if os.path.basename(image_path) not in self.annotations:
                return i
        return len(self.image_list)

    def get_current_image(self):
        """Returns the current image path."""
        if self.image_list and self.index < len(self.image_list):
            return self.image_list[self.index]
        return None

    def next_image(self):
        """Advances to the next image."""
        if self.index < len(self.image_list):
            self.index += 1

    def prev_image(self):
        """Goes back to the previous image."""
        if self.index > 0:
            self.index -= 1
