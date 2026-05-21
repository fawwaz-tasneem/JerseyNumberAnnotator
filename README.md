# Jersey Number Annotator

A desktop annotation tool for labelling football jersey numbers, built to create training datasets for OCR and jersey-recognition models. Supports manual labelling, automated augmentation, and session-based resume.

Originally developed as part of a Bachelor's final-year project on automatic football commentary generation, where it was used to prepare jersey-recognition training data feeding the downstream commentary pipeline.

## Features

- **Manual annotation** — type the jersey number on the keyboard, press Enter to save and advance.
- **Augmentation mode** — generates multiple augmented variants per image (saved as `_aug0`, `_aug1`, ...) to expand the training set.
- **Session management** — progress is persisted between runs; you can stop at any time and resume from the last annotated image.
- **CSV export** — labels are written to a structured CSV with image name, label, session ID, and timestamp.
- **Keyboard-driven workflow** — arrow keys to navigate, number keys to enter labels, Enter to commit, Backspace to correct.
- **Dark-themed UI** — built with PyQt5 for low-eye-strain extended annotation sessions.

## Project Structure

```
JerseyNumberAnnotator/
├── annotator.py          # Main GUI application (entry point)
├── image_loader.py       # Loads and navigates the input image set
├── csv_handler.py        # Writes annotations to CSV
├── augmentor.py          # Generates augmented image variants
├── session_manager.py    # Persists and resumes session state
├── rename_dialog.py      # Dialog for renaming images in-tool
├── assets/               # Application icons and UI assets
└── inputImages/          # Preprocessing scripts:
    ├── resize50Script.py            # Batch-resize images to 50%
    └── standardRenamingScript.py    # Batch-rename to a standard scheme
```

## Installation

Requires Python 3.8 or later.

```bash
pip install opencv-python numpy PyQt5
```

Clone the repository:

```bash
git clone https://github.com/fawwaz-tasneem/JerseyNumberAnnotator.git
cd JerseyNumberAnnotator
```

Run the tool:

```bash
python annotator.py
```

## Usage

**Load images.** Click *Load Folder* to select a directory of input images. Click *Select Output Folder* to choose where annotations, augmented images, and session data will be written.

**Annotate.** Type the jersey number using the number keys (0–9). Press Backspace to correct. Press Enter to save the label and advance to the next image.

**Navigate.** Use the left and right arrow keys to move between images.

**Augment (optional).** Enable *Augmentation Mode* before saving. Each image will produce the original (suffixed `_aug0`) plus several augmented variants (`_aug1`, `_aug2`, ...). All variants share the same label.

**Resume.** If a previous session exists in the selected output folder, the tool detects it on startup and resumes from the last annotated image.

## Keyboard Shortcuts

| Key            | Action                                  |
|----------------|-----------------------------------------|
| Left arrow     | Previous image                          |
| Right arrow    | Next image                              |
| 0–9            | Enter digit of the jersey number        |
| Backspace      | Delete the last digit entered           |
| Enter          | Save annotation and advance             |

## Output

### Annotations CSV (`annotations.csv`)

| image_name           | label | session_id      | timestamp           |
|----------------------|-------|-----------------|---------------------|
| IMG_0001.jpg         | 10    | 20250215_020223 | 2025-02-15 02:02:36 |
| IMG_0001_aug1.jpg    | 10    | 20250215_020223 | 2025-02-15 02:02:38 |

The `session_id` field groups all images annotated in the same run, which is useful when auditing inter-annotator consistency or rolling back a session.

### Augmented Images

Saved alongside the original in the output folder:

```
IMG_0001_aug0.jpg   # Original
IMG_0001_aug1.jpg   # Augmented variant 1
IMG_0001_aug2.jpg   # Augmented variant 2
...
```

### Session Data (`session_data.json`)

Tracks the list of annotated images and per-session statistics so the tool can resume cleanly after a restart.

## Troubleshooting

**Images are not being saved.** Confirm that an output folder has been selected, and that the process has write permission to it. Run the tool from a terminal (`python annotator.py`) to inspect any errors printed during save.

**Augmented images are not appearing.** Ensure *Augmentation Mode* is enabled before saving. If `cv2.imwrite` fails silently, the underlying error will be printed to the terminal.

**Session does not resume.** Make sure `session_data.json` and `annotations.csv` are present in the currently selected output folder. The tool checks for both files on startup and shows a confirmation when a session is restored.

## Authors

Developed by Fawwaz Bin Tasneem and Syed Ali Mehdi Rizvi as part of a Bachelor's final-year project on automatic football commentary generation at Zakir Husain College of Engineering and Technology, Aligarh Muslim University.

## License

Released under the MIT License. See [LICENSE](LICENSE) for the full text.
