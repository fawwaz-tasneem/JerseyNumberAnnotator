import sys
import os
import time

try:
    from PyQt5.QtWidgets import (
        QApplication, QLabel, QPushButton, QFileDialog,
        QVBoxLayout, QHBoxLayout, QWidget, QProgressBar,
        QFrame, QCheckBox, QSizePolicy, QMessageBox, QScrollArea
    )
    from PyQt5.QtGui import QPixmap, QFont, QIcon
    from PyQt5.QtCore import Qt, QTimer
except ModuleNotFoundError:
    print("Error: PyQt5 is not installed. Please install it using 'pip install PyQt5'")
    sys.exit(1)

from image_loader import ImageLoader
from csv_handler import CSVHandler
from augmentor import Augmentor
from rename_dialog import RenameDialog
from session_manager import SessionManager

# ── Colour palette ─────────────────────────────────────────────────────────────
BG      = "#0D0F18"
SURFACE = "#13162A"
CARD    = "#181C2E"
BORDER  = "#252A45"
ACCENT  = "#4F8AFF"
GREEN   = "#3DBA79"
ORANGE  = "#FF8C42"
RED     = "#FF5C5C"
TEXT    = "#E2E8F0"
MUTED   = "#7A8299"
DIM     = "#2E3354"


class ImageAnnotator(QWidget):
    def __init__(self):
        super().__init__()
        self.input_folder  = ""
        self.output_folder = ""
        self.session_manager = None
        self.session_start_time = time.time()
        self.label_distribution = {}   # {label_str: count}
        self.last_saved_image = None
        self.label_text = ""
        self.augmented_mode = False
        self.session_data = {
            "session_id":        time.strftime("%Y%m%d_%H%M%S"),
            "start_time":        time.strftime("%Y-%m-%d %H:%M:%S"),
            "images_annotated":  0,
            "suitable_images":   0,
        }
        self.image_loader = ImageLoader()
        self.csv_handler  = CSVHandler()
        self.augmentor    = Augmentor()
        self.initUI()
        self._start_timer()

    # ── Timer ──────────────────────────────────────────────────────────────────

    def _start_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        elapsed = int(time.time() - self.session_start_time)
        h, rem  = divmod(elapsed, 3600)
        m, s    = divmod(rem, 60)
        self._elapsed_val.setText(f"{h:02d}:{m:02d}:{s:02d}")

        annotated = self.session_data.get("images_annotated", 0)
        if elapsed > 0 and annotated > 0:
            rate = annotated / (elapsed / 60.0)
            self._rate_val.setText(f"{rate:.1f} / min")
            remaining = len(self.image_loader.image_list) - self.image_loader.index
            eta = int(remaining / rate) if rate > 0 else 0
            self._eta_val.setText(f"~{eta} min")
        else:
            self._rate_val.setText("—")
            self._eta_val.setText("—")

    # ── UI helpers ─────────────────────────────────────────────────────────────

    def _card(self, title, body_layout, dot_color=ACCENT):
        """Wraps a layout in a styled card QFrame."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(14, 10, 14, 14)
        outer.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{dot_color}; font-size:9px; background:transparent; border:none;")
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            f"color:{MUTED}; font-size:10px; font-weight:700; "
            f"letter-spacing:1px; background:transparent; border:none;"
        )
        title_row.addWidget(dot)
        title_row.addWidget(lbl)
        title_row.addStretch()
        outer.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border:none; border-top:1px solid {BORDER}; background:transparent;")
        sep.setMaximumHeight(1)
        outer.addWidget(sep)

        outer.addLayout(body_layout)
        return frame

    def _stat_row(self, label_text, attr, default="—", val_color=TEXT):
        """Creates a key/value row; stores value QLabel as self.<attr>."""
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color:{MUTED}; font-size:13px; background:transparent; border:none;")
        val = QLabel(default)
        val.setStyleSheet(
            f"color:{val_color}; font-size:13px; font-weight:600; "
            f"background:transparent; border:none;"
        )
        val.setAlignment(Qt.AlignRight)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(val)
        setattr(self, attr, val)
        return row

    def _btn(self, text, object_name=None, fixed_width=None):
        b = QPushButton(text)
        if object_name:
            b.setObjectName(object_name)
        if fixed_width:
            b.setFixedWidth(fixed_width)
        b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return b

    # ── initUI ─────────────────────────────────────────────────────────────────

    def initUI(self):
        self.setWindowTitle("Jersey Number Annotator")
        try:
            self.setWindowIcon(QIcon("assets/icon.png"))
        except Exception:
            pass
        self.resize(1300, 840)
        self.setMinimumSize(960, 640)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
                color: {TEXT};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
            }}
            QPushButton:hover   {{ background-color: {DIM}; border-color: {ACCENT}; }}
            QPushButton:pressed {{ background-color: {BG}; }}
            QPushButton#accent  {{ background-color:{ACCENT}; border-color:{ACCENT}; color:#fff; }}
            QPushButton#accent:hover  {{ background-color:#6A9FFF; }}
            QPushButton#green   {{ background-color:{GREEN}; border-color:{GREEN}; color:#fff; }}
            QPushButton#green:hover   {{ background-color:#50CF90; }}
            QPushButton#orange  {{ background-color:{ORANGE}; border-color:{ORANGE}; color:#fff; }}
            QPushButton#orange:hover  {{ background-color:#FFB070; }}
            QPushButton#red     {{ background-color:{RED}; border-color:{RED}; color:#fff; }}
            QPushButton#red:hover     {{ background-color:#FF7A7A; }}
            QLineEdit {{
                padding:10px 12px; font-size:15px;
                border:2px solid {BORDER}; border-radius:6px;
                background-color:{SURFACE}; color:#fff;
                selection-background-color:{ACCENT};
            }}
            QLineEdit:focus {{ border-color:{ACCENT}; }}
            QProgressBar {{
                border:none; border-radius:4px;
                background-color:{SURFACE}; max-height:7px; color:transparent;
            }}
            QProgressBar::chunk {{ border-radius:4px; background-color:{ACCENT}; }}
            QCheckBox {{ font-size:13px; spacing:8px; color:{TEXT}; }}
            QCheckBox::indicator {{
                width:17px; height:17px; border-radius:4px;
                border:2px solid {BORDER}; background-color:{SURFACE};
            }}
            QCheckBox::indicator:checked {{ background-color:{ACCENT}; border-color:{ACCENT}; }}
            QScrollBar:vertical {{
                background:{SURFACE}; width:6px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{ background:{DIM}; border-radius:3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        # ── LEFT: image viewer ────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(6)

        nav = QHBoxLayout()
        self.prev_btn = self._btn("← Prev", fixed_width=84)
        self.next_btn = self._btn("Next →", fixed_width=84)
        self.image_name_label = QLabel("No image loaded")
        self.image_name_label.setAlignment(Qt.AlignCenter)
        self.image_name_label.setStyleSheet(f"color:{MUTED}; font-size:13px;")
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.image_name_label, 1)
        nav.addWidget(self.next_btn)
        left.addLayout(nav)

        self.image_label = QLabel("Load an image folder to begin")
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            border: 2px dashed {BORDER}; border-radius:10px;
            background-color:{SURFACE}; color:{MUTED}; font-size:16px;
        """)
        left.addWidget(self.image_label)

        prog_row = QHBoxLayout()
        self.img_counter = QLabel("0 / 0")
        self.img_counter.setStyleSheet(f"color:{MUTED}; font-size:12px; min-width:60px;")
        self.viewer_progress = QProgressBar()
        prog_row.addWidget(self.img_counter)
        prog_row.addWidget(self.viewer_progress, 1)
        left.addLayout(prog_row)

        # ── RIGHT: scrollable info + controls ────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMinimumWidth(320)
        scroll.setMaximumWidth(390)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:transparent;")

        right_inner = QWidget()
        right_inner.setStyleSheet("background:transparent;")
        right = QVBoxLayout(right_inner)
        right.setSpacing(10)
        right.setContentsMargins(0, 0, 8, 0)

        # Card 1 — Annotation input
        ann = QVBoxLayout(); ann.setSpacing(8)

        self.number_display = QLabel("—")
        self.number_display.setFont(QFont("Segoe UI", 54, QFont.Bold))
        self.number_display.setAlignment(Qt.AlignCenter)
        self.number_display.setFixedHeight(108)
        self.number_display.setStyleSheet(f"""
            color:{ACCENT}; background-color:{SURFACE};
            border:2px solid {BORDER}; border-radius:8px; padding:4px;
        """)
        ann.addWidget(self.number_display)

        hint = QLabel("Type number  ·  Enter to save  ·  ← → to navigate")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color:{MUTED}; font-size:11px; background:transparent; border:none;")
        ann.addWidget(hint)

        btns1 = QHBoxLayout(); btns1.setSpacing(6)
        self.unsuitable_btn = self._btn("Mark Unsuitable", "orange")
        self.skip_btn       = self._btn("Skip")
        self.undo_btn       = self._btn("Undo Last")
        for b in [self.unsuitable_btn, self.skip_btn, self.undo_btn]:
            btns1.addWidget(b)
        ann.addLayout(btns1)

        self.augment_toggle = QCheckBox("Augmentation  (+10 images per label)")
        ann.addWidget(self.augment_toggle, 0, Qt.AlignCenter)

        right.addWidget(self._card("Annotation", ann, ACCENT))

        # Card 2 — Dataset overview
        ds = QVBoxLayout(); ds.setSpacing(5)
        ds.addLayout(self._stat_row("Total images",   "_total_val"))
        ds.addLayout(self._stat_row("Labeled",        "_labeled_val",    val_color=ACCENT))
        ds.addLayout(self._stat_row("Suitable",       "_suitable_val",   val_color=GREEN))
        ds.addLayout(self._stat_row("Unsuitable",     "_unsuitable_val", val_color=ORANGE))
        ds.addLayout(self._stat_row("Remaining",      "_remaining_val"))
        ds.addLayout(self._stat_row("Augmented imgs", "_augmented_val",  val_color=MUTED))
        self._ds_progress = QProgressBar()
        self._pct_label   = QLabel("0%")
        self._pct_label.setStyleSheet(f"color:{MUTED}; font-size:11px; background:transparent; border:none;")
        self._pct_label.setAlignment(Qt.AlignRight)
        ds.addWidget(self._ds_progress)
        ds.addWidget(self._pct_label)
        right.addWidget(self._card("Dataset", ds, GREEN))

        # Card 3 — Session stats
        ss = QVBoxLayout(); ss.setSpacing(5)
        ss.addLayout(self._stat_row("Session #",       "_session_no_val"))
        ss.addLayout(self._stat_row("This session",    "_sess_count_val", val_color=ACCENT))
        ss.addLayout(self._stat_row("Elapsed",         "_elapsed_val"))
        ss.addLayout(self._stat_row("Rate",            "_rate_val"))
        ss.addLayout(self._stat_row("ETA",             "_eta_val"))
        right.addWidget(self._card("Session", ss, MUTED))

        # Card 4 — Label distribution
        dist = QVBoxLayout(); dist.setSpacing(4)
        self._dist_label = QLabel("No labels yet")
        self._dist_label.setStyleSheet(
            f"color:{MUTED}; font-size:12px; background:transparent; border:none;"
        )
        self._dist_label.setWordWrap(True)
        dist.addWidget(self._dist_label)
        right.addWidget(self._card("Label Distribution", dist, MUTED))

        right.addStretch()
        scroll.setWidget(right_inner)

        # ── BOTTOM TOOLBAR ────────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setFixedHeight(54)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color:{SURFACE};
                border-top:1px solid {BORDER};
            }}
        """)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 6, 12, 6)
        tb.setSpacing(8)

        self.load_folder_btn    = self._btn("Load Folder",    "green")
        self.select_output_btn  = self._btn("Output Folder",  "green")
        self.rename_btn         = self._btn("Rename Images")
        self.save_session_btn   = self._btn("Save & Close",   "accent")
        self.resume_session_btn = self._btn("Resume Session")

        tsep = QFrame()
        tsep.setFrameShape(QFrame.VLine)
        tsep.setStyleSheet(f"color:{BORDER};")

        self.status_label = QLabel("Select an output folder, then load an image folder")
        self.status_label.setStyleSheet(f"color:{MUTED}; font-size:12px; background:transparent;")

        tb.addWidget(self.load_folder_btn)
        tb.addWidget(self.select_output_btn)
        tb.addWidget(self.rename_btn)
        tb.addWidget(tsep)
        tb.addWidget(self.status_label, 1)
        tb.addWidget(self.resume_session_btn)
        tb.addWidget(self.save_session_btn)

        # ── ROOT LAYOUT ───────────────────────────────────────────────────────
        content = QHBoxLayout()
        content.setSpacing(10)
        content.setContentsMargins(12, 12, 12, 8)

        left_w = QWidget()
        left_w.setLayout(left)
        content.addWidget(left_w, 1)
        content.addWidget(scroll)

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(content, 1)
        root.addWidget(toolbar)

        # ── Connections ───────────────────────────────────────────────────────
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.next_btn.clicked.connect(self.show_next_image)
        self.load_folder_btn.clicked.connect(self.load_folder)
        self.select_output_btn.clicked.connect(self.select_output_folder)
        self.rename_btn.clicked.connect(self.rename_images)
        self.unsuitable_btn.clicked.connect(self.mark_unsuitable)
        self.skip_btn.clicked.connect(self.skip_image)
        self.undo_btn.clicked.connect(self.undo_last)
        self.save_session_btn.clicked.connect(self.save_session)
        self.resume_session_btn.clicked.connect(self.resume_session)
        self.augment_toggle.stateChanged.connect(self.toggle_augmentation)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        self.show_image()
        super().resizeEvent(event)

    def toggle_augmentation(self, state):
        self.augmented_mode = (state == Qt.Checked)

    def set_status(self, message, level="info"):
        colors = {"success": GREEN, "warning": ORANGE, "error": RED, "info": MUTED}
        color = colors.get(level, MUTED)
        self.status_label.setStyleSheet(f"color:{color}; font-size:12px; background:transparent;")
        self.status_label.setText(message)

    def _load_label_distribution(self):
        """Rebuilds label-count dict from the current CSV."""
        self.label_distribution = {}
        if not self.output_folder:
            return
        for img_name, entry in self.csv_handler.load_existing_annotations(self.output_folder).items():
            label = entry[0]
            if label.lower() != "unsuitable" and not img_name.endswith(("_aug0.jpg", "_aug1.jpg")):
                self.label_distribution[label] = self.label_distribution.get(label, 0) + 1

    def _refresh_dist_display(self):
        if not self.label_distribution:
            self._dist_label.setText("No labels yet")
            return
        top = sorted(self.label_distribution.items(), key=lambda x: -x[1])
        parts = [f"#{lbl} ×{cnt}" for lbl, cnt in top[:14]]
        self._dist_label.setText("   ".join(parts))

    # ── Stats update ──────────────────────────────────────────────────────────

    def update_stats(self):
        total     = len(self.image_loader.image_list)
        anns      = self.image_loader.annotations
        labeled   = sum(1 for p in self.image_loader.image_list
                        if os.path.basename(p) in anns)
        suitable  = sum(1 for p in self.image_loader.image_list
                        if anns.get(os.path.basename(p), ("unsuitable",))[0].lower() != "unsuitable"
                        and os.path.basename(p) in anns)
        unsuitable = labeled - suitable
        remaining  = total - labeled
        pct        = int(labeled / total * 100) if total else 0

        # Count augmented images in output folder
        aug_count = 0
        if self.output_folder and os.path.isdir(self.output_folder):
            aug_count = sum(1 for f in os.listdir(self.output_folder)
                            if "_aug" in f and f.lower().endswith((".jpg", ".png", ".jpeg")))

        self._total_val.setText(str(total))
        self._labeled_val.setText(f"{labeled}  ({pct}%)")
        self._suitable_val.setText(str(suitable))
        self._unsuitable_val.setText(str(unsuitable))
        self._remaining_val.setText(str(remaining))
        self._augmented_val.setText(str(aug_count))
        self._ds_progress.setMaximum(total or 1)
        self._ds_progress.setValue(labeled)
        self._pct_label.setText(f"{pct}% labeled")

        self.viewer_progress.setMaximum(total or 1)
        self.viewer_progress.setValue(self.image_loader.index)
        self.img_counter.setText(f"{self.image_loader.index} / {total}")

        session_no = self.session_manager.get_session_count() + 1 if self.session_manager else 1
        self._session_no_val.setText(f"#{session_no:03d}")
        self._sess_count_val.setText(str(self.session_data.get("images_annotated", 0)))

        self._refresh_dist_display()

    # ── Folder / file actions ─────────────────────────────────────────────────

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return
        self.input_folder = folder
        self.image_loader.load_images(folder, self.output_folder, self)
        self._load_label_distribution()
        self.show_image()
        self.update_stats()
        n = len(self.image_loader.image_list)
        self.set_status(f"Loaded {n} image{'s' if n != 1 else ''} from {os.path.basename(folder)}", "success")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder:
            return
        self.output_folder = folder
        self.session_manager = SessionManager(os.path.join(folder, "session_history.json"))
        if self.input_folder and self.image_loader.image_list:
            self.image_loader.load_images(self.input_folder, self.output_folder, self)
            self.show_image()
        self._load_label_distribution()
        self.update_stats()
        self.set_status(f"Output: {folder}", "success")

    def rename_images(self):
        if not self.input_folder:
            QMessageBox.warning(self, "Rename Images", "Load an image folder first.")
            return
        dialog = RenameDialog(self.input_folder, self)
        if dialog.exec_() == dialog.Accepted:
            prefix, start_number = dialog.getValues()
            if not prefix or not start_number.isdigit():
                QMessageBox.warning(self, "Rename Images", "Invalid prefix or starting number.")
                return
            self._do_rename(self.input_folder, prefix, int(start_number))
            self.image_loader.load_images(self.input_folder, self.output_folder, self)
            self.show_image()
            self.update_stats()
            self.set_status("Images renamed.", "success")

    def _do_rename(self, folder, prefix, start_number):
        images = sorted(f for f in os.listdir(folder)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')))
        for i, old_name in enumerate(images):
            ext      = os.path.splitext(old_name)[1].lower()
            new_name = f"{prefix}_{str(start_number + i).zfill(6)}{ext}"
            try:
                os.rename(os.path.join(folder, old_name), os.path.join(folder, new_name))
            except Exception as e:
                QMessageBox.warning(self, "Rename Images", f"Error renaming {old_name}: {e}")

    # ── Image display ─────────────────────────────────────────────────────────

    def show_prev_image(self):
        self.image_loader.prev_image()
        self.show_image()
        self.update_stats()

    def show_next_image(self):
        self.image_loader.next_image()
        self.show_image()
        self.update_stats()

    def show_image(self):
        path = self.image_loader.get_current_image()
        if path:
            px = QPixmap(path)
            if not px.isNull():
                self.image_label.setPixmap(
                    px.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.image_label.setText("Failed to load image")
            self.image_name_label.setText(os.path.basename(path))
        else:
            self.image_label.setPixmap(QPixmap())
            if self.image_loader.image_list:
                self.image_label.setText("All images annotated")
                self.image_name_label.setText("Done")
                self.set_status("All images in this folder have been annotated.", "success")
            else:
                self.image_label.setText("Load an image folder to begin")
                self.image_name_label.setText("No image loaded")

    # ── Annotation actions ────────────────────────────────────────────────────

    def save_annotation(self):
        label = self.label_text.strip()
        if label == "--":
            label = "unsuitable"
        if not label:
            self.set_status("Type a jersey number, then press Enter.", "warning")
            return
        if not self.output_folder:
            self.set_status("Select an output folder before saving.", "warning")
            return
        path = self.image_loader.get_current_image()
        if not path:
            self.set_status("No image loaded.", "warning")
            return

        saved = self.csv_handler.save_annotation(path, label, self.output_folder,
                                                  self.session_data["session_id"])
        if not saved:
            self.set_status("Failed to write annotation.", "error")
            return

        self.last_saved_image = path
        self.session_data["images_annotated"] += 1

        img_name = os.path.basename(path)
        self.image_loader.annotations[img_name] = (
            label, self.session_data["session_id"], time.strftime("%Y-%m-%d %H:%M:%S")
        )

        if label.lower() != "unsuitable":
            self.label_distribution[label] = self.label_distribution.get(label, 0) + 1
            if self.augmented_mode:
                aug_imgs = self.augmentor.augment_image(path, self.output_folder, True)
                for aug in aug_imgs:
                    self.csv_handler.save_annotation(aug, label, self.output_folder,
                                                      self.session_data["session_id"])
                self.session_data["suitable_images"] += len(aug_imgs)
                self.set_status(
                    f"Saved #{label} + {len(aug_imgs)} augmented copies.", "success"
                )
            else:
                self.session_data["suitable_images"] += 1
                self.set_status(f"Saved  #{label}  —  {img_name}", "success")
        else:
            self.set_status(f"Marked unsuitable  —  {img_name}", "warning")

        self.label_text = ""
        self.number_display.setText("—")
        self.show_next_image()
        self.update_stats()

    def mark_unsuitable(self):
        self.label_text = "unsuitable"
        self.number_display.setText("unsuitable")
        self.save_annotation()

    def skip_image(self):
        self.image_loader.next_image()
        self.show_image()
        self.update_stats()
        self.set_status("Skipped.", "info")

    def undo_last(self):
        if not self.last_saved_image:
            self.set_status("Nothing to undo.", "warning")
            return
        img_name  = os.path.basename(self.last_saved_image)
        base_stem = os.path.splitext(img_name)[0]
        if self.csv_handler.remove_annotations_for_image(self.output_folder, base_stem):
            if img_name in self.image_loader.annotations:
                label = self.image_loader.annotations[img_name][0]
                if label in self.label_distribution:
                    self.label_distribution[label] = max(0, self.label_distribution[label] - 1)
                del self.image_loader.annotations[img_name]
            self.session_data["images_annotated"] = max(0, self.session_data["images_annotated"] - 1)
            if self.image_loader.index > 0:
                self.image_loader.prev_image()
            self.last_saved_image = None
            self.show_image()
            self.update_stats()
            self.set_status(f"Undid annotation for {img_name}.", "warning")
        else:
            self.set_status("Could not undo — entry not found in CSV.", "error")

    # ── Session ───────────────────────────────────────────────────────────────

    def save_session(self):
        self.session_data["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if self.session_manager:
            if self.session_manager.add_session(self.session_data):
                QMessageBox.information(self, "Session Saved", "Session saved successfully.")
            else:
                QMessageBox.warning(self, "Session", "Failed to save session.")
        else:
            QMessageBox.warning(self, "Session", "Select an output folder first.")
        self.close()

    def resume_session(self):
        if not self.session_manager:
            QMessageBox.warning(self, "Resume", "Select an output folder first.")
            return
        self.session_data = {
            "session_id":       time.strftime("%Y%m%d_%H%M%S"),
            "start_time":       time.strftime("%Y-%m-%d %H:%M:%S"),
            "images_annotated": 0,
            "suitable_images":  0,
        }
        self.session_start_time = time.time()
        if self.input_folder:
            self.image_loader.load_images(self.input_folder, self.output_folder, self)
            self._load_label_distribution()
            self.show_image()
        self.update_stats()
        self.set_status("New session started.", "success")

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            self.show_prev_image()
        elif key == Qt.Key_Right:
            self.show_next_image()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self.save_annotation()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            self.label_text += chr(key)
            self.number_display.setText(self.label_text)
        elif key == Qt.Key_Minus:
            if self.label_text == "-":
                self.label_text = "unsuitable"
                self.number_display.setText("unsuitable")
            else:
                self.label_text += "-"
                self.number_display.setText(self.label_text)
        elif key == Qt.Key_Backspace:
            self.label_text = self.label_text[:-1]
            self.number_display.setText(self.label_text if self.label_text else "—")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageAnnotator()
    window.show()
    sys.exit(app.exec_())
