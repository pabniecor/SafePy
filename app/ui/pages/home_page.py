"""Home page - Main menu with analysis options."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class HomePage(QWidget):
    """Home page displaying main menu options."""

    new_analysis_clicked = Signal()
    view_history_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("SafePy")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Detector de Vulnerabilidades en Dependencias Python")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Description
        description = QLabel(
            "Analiza tus archivos de dependencias Python para detectar "
            "vulnerabilidades conocidas utilizando la API de OSV. "
            "Obtén recomendaciones automáticas de actualizaciones seguras."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_font = QFont()
        description_font.setPointSize(11)
        description.setFont(description_font)
        layout.addWidget(description)

        # Spacer
        layout.addSpacing(30)

        # Buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Left spacer
        buttons_layout.addSpacing(50)

        # New Analysis button
        self.btn_new_analysis = QPushButton("Realizar nuevo análisis")
        self.btn_new_analysis.setMinimumHeight(60)
        self.btn_new_analysis.setMinimumWidth(250)
        self.btn_new_analysis.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_analysis.clicked.connect(self.new_analysis_clicked.emit)
        buttons_layout.addWidget(self.btn_new_analysis)

        # View History button
        self.btn_view_history = QPushButton("Consultar historial de análisis")
        self.btn_view_history.setMinimumHeight(60)
        self.btn_view_history.setMinimumWidth(250)
        self.btn_view_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_view_history.clicked.connect(self.view_history_clicked.emit)
        buttons_layout.addWidget(self.btn_view_history)

        # Right spacer
        buttons_layout.addSpacing(50)

        layout.addLayout(buttons_layout)

        # Bottom spacer
        layout.addSpacing(30)

        self.setLayout(layout)
