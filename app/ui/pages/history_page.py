"""History page - Past analyses display."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from app.domain.models import Analysis


class HistoryPage(QWidget):
    """Page displaying analysis history."""

    analysis_selected = Signal(int)  # analysis_id
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.analyses: list[Analysis] = []
        self.setup_ui()

    def setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # Back button
        back_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Volver al menú")
        self.btn_back.setMaximumWidth(100)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        back_layout.addWidget(self.btn_back)
        back_layout.addStretch()
        layout.addLayout(back_layout)

        # Title
        title = QLabel("Historial de análisis")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Table for analyses
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Fecha", "Nombre", "Estado", "Resumen"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemClicked.connect(self._on_table_item_clicked)
        layout.addWidget(self.table)

        # Empty state message
        self.empty_label = QLabel("No hay análisis disponibles")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #999999; font-size: 12pt;")
        layout.addWidget(self.empty_label)
        self.empty_label.hide()

        self.setLayout(layout)

    def set_analyses(self, analyses: list[Analysis]):
        """Populate page with analyses list."""
        self.analyses = analyses or []

        if not self.analyses:
            self.table.setRowCount(0)
            self.empty_label.show()
            return

        self.empty_label.hide()
        self.table.setRowCount(len(self.analyses))

        for row, analysis in enumerate(self.analyses):
            self._populate_table_row(row, analysis)

    def _populate_table_row(self, row: int, analysis: Analysis):
        """Populate a single table row with analysis data."""
        # Date
        date_str = ""
        if hasattr(analysis, 'created_at') and analysis.created_at:
            # Format date
            if hasattr(analysis.created_at, 'strftime'):
                date_str = analysis.created_at.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = str(analysis.created_at)
        date_item = QTableWidgetItem(date_str)
        self.table.setItem(row, 0, date_item)

        # Name
        name_item = QTableWidgetItem(analysis.analysis_name or "Sin nombre")
        name_item.setData(Qt.ItemDataRole.UserRole, analysis.analysis_id)  # Store ID for later
        self.table.setItem(row, 1, name_item)

        # Status
        status_str = "Completado" if analysis.result.status == "success" else "Error"
        status_item = QTableWidgetItem(status_str)
        self.table.setItem(row, 2, status_item)

        # Summary (deps and vulns count)
        total_deps = len(analysis.dependencies) if analysis.dependencies else 0
        vuln_count = sum(
            1 for dep in (analysis.dependencies or [])
            if dep.vulnerabilities and len(dep.vulnerabilities) > 0
        )
        summary = f"{total_deps} deps, {vuln_count} vulns"
        summary_item = QTableWidgetItem(summary)
        summary_item.setForeground(QBrush(QColor("#666666")))
        self.table.setItem(row, 3, summary_item)

    def _on_table_item_clicked(self, item: QTableWidgetItem):
        """Handle table row click."""
        analysis_id = item.data(Qt.ItemDataRole.UserRole)
        if analysis_id:
            self.analysis_selected.emit(analysis_id)

    def clear(self):
        """Reset page state."""
        self.analyses = []
        self.table.setRowCount(0)
        self.empty_label.show()
