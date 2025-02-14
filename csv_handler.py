import os
import csv
import time

class CSVHandler:
    def __init__(self):
        self.file_name = "annotations.csv"
        self.history_file = "annotation_history.csv"  # New history CSV file

    def save_annotation(self, image_path, label, output_folder, session_id):
        """
        Appends a new annotation to the main CSV file.
        Ensures existing annotations are preserved.
        """
        csv_path = os.path.join(output_folder, self.file_name)
        exists = os.path.isfile(csv_path)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(csv_path, 'a', newline='') as file:
            writer = csv.writer(file)
            if not exists:
                writer.writerow(["image_name", "label", "session_id", "timestamp"])
            writer.writerow([os.path.basename(image_path), label, session_id, timestamp])

    def load_existing_annotations(self, output_folder):
        """
        Loads existing annotations from the main CSV file.
        Returns a dictionary {image_name: (label, session_id, timestamp)}.
        """
        csv_path = os.path.join(output_folder, self.file_name)
        annotations = {}

        if os.path.isfile(csv_path):
            with open(csv_path, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) == 4:
                        annotations[row[0]] = (row[1], row[2], row[3])
        return annotations

    def save_history(self, image_path, label, output_folder, session_id):
        """
        Appends a new annotation record to the history CSV file.
        This file is append-only.
        """
        history_path = os.path.join(output_folder, self.history_file)
        exists = os.path.isfile(history_path)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(history_path, 'a', newline='') as file:
            writer = csv.writer(file)
            if not exists:
                writer.writerow(["image_name", "label", "session_id", "timestamp"])
            writer.writerow([os.path.basename(image_path), label, session_id, timestamp])
