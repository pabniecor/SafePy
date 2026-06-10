"""Upload page - File selection and analysis initiation."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


class UploadPage(QWidget):
    """Page for uploading dependency files and initiating analysis."""

    analyze_clicked = Signal(str, str)  # file_path, analysis_name
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.selected_file: str = ""
        self.setup_ui()

    def setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)

        # Back button
        back_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Volver al menú")
        self.btn_back.setMaximumWidth(200)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        back_layout.addWidget(self.btn_back)
        back_layout.addStretch()
        layout.addLayout(back_layout)

        # Title
        title = QLabel("Subir archivo de dependencias")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Selecciona un archivo de dependencias (requirements.txt, pyproject.toml, setup.py, etc.)"
        )
        layout.addWidget(description)

        # Drag-drop area
        self.drop_area = QFrame()
        self.drop_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.drop_area.setStyleSheet(
            "border: 2px dashed #0099CC; border-radius: 8px; background-color: #E8F4F8;"
        )
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setAcceptDrops(True)

        drop_layout = QVBoxLayout()
        drop_label = QLabel("Arrastra un archivo aquí\no")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        drop_label.setFont(font)
        drop_layout.addWidget(drop_label)

        browse_btn = QPushButton("Seleccionar archivo")
        browse_btn.setMaximumWidth(200)
        browse_btn.clicked.connect(self._on_browse_clicked)
        drop_layout.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.drop_area.setLayout(drop_layout)
        layout.addWidget(self.drop_area)

        # File path display
        self.file_label = QLabel("Archivo: (ninguno seleccionado)")
        self.file_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.file_label)

        # Analysis name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Nombre del análisis:")
        name_label.setMinimumWidth(150)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Análisis de seguridad 1")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Error/Status message
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # Start analysis button
        self.btn_start = QPushButton("Iniciar análisis")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.clicked.connect(self._on_analyze_clicked)
        layout.addWidget(self.btn_start)

        layout.addStretch()
        self.setLayout(layout)

        # Install drag-drop event handlers
        self.drop_area.dragEnterEvent = self.dragEnterEvent
        self.drop_area.dropEvent = self.dropEvent

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_area.setStyleSheet(
                "border: 2px solid #0099CC; border-radius: 8px; background-color: #D0E8F0;"
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.drop_area.setStyleSheet(
            "border: 2px dashed #0099CC; border-radius: 8px; background-color: #E8F4F8;"
        )

    def dropEvent(self, event):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.selected_file = file_path
            self.file_label.setText(f"Archivo: {Path(file_path).name}")
            self.set_message("Archivo seleccionado", is_error=False)
        self.drop_area.setStyleSheet(
            "border: 2px dashed #0099CC; border-radius: 8px; background-color: #E8F4F8;"
        )

    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de dependencias",
            "",
            "All Files (*);;Requirements (*.txt);;PyProject (*.toml);;Setup (*.py)",
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(f"Archivo: {Path(file_path).name}")
            self.set_message("Archivo seleccionado", is_error=False)

    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        if not self.validate_inputs():
            return
        self.analyze_clicked.emit(self.selected_file, self.name_input.text())

    def validate_inputs(self) -> bool:
        """Validate user inputs before analysis."""
        if not self.selected_file:
            self.set_message("Por favor selecciona un archivo", is_error=True)
            return False

        if not self.name_input.text().strip():
            self.set_message("Por favor ingresa un nombre para el análisis", is_error=True)
            return False

        if not Path(self.selected_file).exists():
            self.set_message("El archivo seleccionado no existe", is_error=True)
            return False

        return True

    def set_message(self, message: str, is_error: bool = False):
        """Display a message to the user."""
        self.message_label.setText(message)
        if is_error:
            self.message_label.setStyleSheet("color: #CC0000;")
        else:
            self.message_label.setStyleSheet("color: #00AA00;")

    def clear_inputs(self):
        """Reset all inputs for new analysis."""
        self.selected_file = ""
        self.name_input.clear()
        self.file_label.setText("Archivo: (ninguno seleccionado)")
        self.message_label.setText("")
