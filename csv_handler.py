import os
import csv

class CSVHandler:
    def __init__(self):
        self.file_name = "labels.csv"

    def save_annotation(self, image_path, label, output_folder):
        csv_path = os.path.join(output_folder, self.file_name)
        with open(csv_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([os.path.basename(image_path), label])
