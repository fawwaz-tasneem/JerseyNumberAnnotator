import logging
from pathlib import Path
from csv_handler import CSVHandler
from augmentor import Augmentor
from session_manager import SessionManager

class AnnotationService:
    def __init__(self, output_folder=None):
        self.output_folder = Path(output_folder) if output_folder else None
        self.csv_handler = CSVHandler()
        self.augmentor = Augmentor()
        self.session_manager = SessionManager(self.output_folder / "session_history.json") if self.output_folder else None

    def set_output_folder(self, output_folder):
        self.output_folder = Path(output_folder)
        self.session_manager = SessionManager(self.output_folder / "session_history.json")

    def load_existing_annotations(self):
        if not self.output_folder:
            return {}
        return self.csv_handler.load_existing_annotations(self.output_folder)

    def save_annotation(self, image_path, label, session_id, augment=False):
        if not self.output_folder:
            logging.error("Output folder is not configured for annotation service.")
            return {"success": False, "message": "Output folder is not configured."}

        self.output_folder.mkdir(parents=True, exist_ok=True)

        image_path = Path(image_path)
        saved_paths = []
        saved = self.csv_handler.save_annotation(image_path, label, self.output_folder, session_id)
        if not saved:
            return {"success": False, "message": "Failed to save annotation record."}

        saved_paths.append(image_path)
        if label.lower() != "unsuitable" and augment:
            aug_images = self.augmentor.augment_image(image_path, self.output_folder, True)
            for aug_image in aug_images:
                aug_path = Path(aug_image)
                self.csv_handler.save_annotation(aug_path, label, self.output_folder, session_id)
                saved_paths.append(aug_path)

        return {"success": True, "saved_paths": saved_paths}

    def undo_last_annotation(self, base_image_name):
        if not self.output_folder:
            logging.error("Output folder is not configured for undo operation.")
            return False
        removed = self.csv_handler.remove_annotations_for_image(self.output_folder, base_image_name)
        if removed:
            for path in self.output_folder.iterdir():
                if path.name.startswith(f"{base_image_name}_aug"):
                    try:
                        path.unlink()
                        logging.info("Removed output image %s", path)
                    except Exception as e:
                        logging.warning("Could not remove output image %s: %s", path, e)
        return removed

    def save_session(self, session_data):
        if not self.session_manager:
            logging.error("Session manager not initialized.")
            return False
        return self.session_manager.add_session(session_data)
