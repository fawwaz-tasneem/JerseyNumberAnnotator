from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton

class RenameDialog(QDialog):
    def __init__(self, input_folder, parent=None):
        super().__init__(parent)
        self.input_folder = input_folder
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Rename Input Images")
        layout = QVBoxLayout()

        prefix_label = QLabel("Enter prefix:")
        self.prefix_edit = QLineEdit()
        layout.addWidget(prefix_label)
        layout.addWidget(self.prefix_edit)

        number_label = QLabel("Enter starting number:")
        self.number_edit = QLineEdit()
        layout.addWidget(number_label)
        layout.addWidget(self.number_edit)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def getValues(self):
        """Returns the prefix and starting number entered by the user."""
        return self.prefix_edit.text(), self.number_edit.text()
