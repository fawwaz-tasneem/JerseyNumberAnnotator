import os
import csv
import time

class CSVHandler:
    def __init__(self):
        self.file_name = "annotations.csv"

    def save_annotation(self, image_path, label, output_folder, session_id):
        """
        Appends a new annotation to the main CSV file.
        Ensures existing annotations are preserved.
        """
        csv_path = os.path.join(output_folder, self.file_name)
        try:
            exists = os.path.isfile(csv_path)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                if not exists:
                    writer.writerow(["image_name", "label", "session_id", "timestamp"])
                writer.writerow([os.path.basename(image_path), label, session_id, timestamp])
            return True
        except Exception as e:
            print(f"Error saving annotation to CSV: {e}")
            return False

    def load_existing_annotations(self, output_folder):
        """
        Loads existing annotations from the main CSV file.
        Returns a dictionary {image_name: (label, session_id, timestamp)}.
        """
        csv_path = os.path.join(output_folder, self.file_name)
        annotations = {}
        if os.path.isfile(csv_path):
            try:
                with open(csv_path, 'r') as file:
                    reader = csv.reader(file)
                    next(reader, None)  # Skip header
                    for row in reader:
                        if len(row) == 4:
                            annotations[row[0]] = (row[1], row[2], row[3])
            except Exception as e:
                print(f"Error reading annotations CSV: {e}")
        return annotations

    def remove_annotations_for_image(self, output_folder, base_stem):
        """
        Removes all CSV rows for a given image stem (original + any _aug variants).
        Returns True if the file was rewritten successfully.
        """
        csv_path = os.path.join(output_folder, self.file_name)
        if not os.path.isfile(csv_path):
            return False
        try:
            with open(csv_path, 'r', newline='') as f:
                rows = list(csv.reader(f))
            header = rows[0:1]
            kept = [
                row for row in rows[1:]
                if row and not (
                    os.path.splitext(row[0])[0] == base_stem
                    or row[0].startswith(base_stem + "_aug")
                )
            ]
            with open(csv_path, 'w', newline='') as f:
                csv.writer(f).writerows(header + kept)
            return True
        except Exception as e:
            print(f"Error removing annotations for {base_stem}: {e}")
            return False
