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
from app.domain.enums import AnalysisStatus


class HistoryPage(QWidget):
    """Page displaying analysis history."""

    analysis_selected = Signal(int)  # analysis_id
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.analyses: list[Analysis] = []
        self.setup_ui()
        self._update_empty_state()

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
        self.table.setHorizontalHeaderLabels(["Fecha", "Nombre", "Estado", "Resumen"])
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
        self.show()  # útil para que isVisible() en tests sea consistente

    def _update_empty_state(self):
        is_empty = len(self.analyses) == 0
        self.table.setVisible(not is_empty)
        self.empty_label.setVisible(is_empty)

    def set_analyses(self, analyses: Optional[list[Analysis]]):
        self.analyses = analyses or []
        self.table.setRowCount(0)

        if not self.analyses:
            self._update_empty_state()
            return

        self.table.setRowCount(len(self.analyses))
        for row, analysis in enumerate(self.analyses):
            self._populate_table_row(row, analysis)

        self._update_empty_state()

    def _populate_table_row(self, row: int, analysis: Analysis):
        """Populate a single table row with analysis data."""
        # Date
        date_str = ""
        if hasattr(analysis, "created_at") and analysis.created_at:
            if hasattr(analysis.created_at, "strftime"):
                date_str = analysis.created_at.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = str(analysis.created_at)

        status_str = (
            "Completado"
            if analysis.result.status == AnalysisStatus.SUCCESS
            else "Error"
        )

        total_deps = len(analysis.dependencies) if analysis.dependencies else 0
        vuln_count = sum(
            len(dep.vulnerabilities or [])
            for dep in (analysis.dependencies or [])
        )
        summary = f"{total_deps} deps, {vuln_count} vulns"

        items = [
            QTableWidgetItem(date_str),
            QTableWidgetItem(analysis.analysis_name or "Sin nombre"),
            QTableWidgetItem(status_str),
            QTableWidgetItem(summary),
        ]

        items[3].setForeground(QBrush(QColor("#666666")))

        for col, item in enumerate(items):
            item.setData(Qt.ItemDataRole.UserRole, analysis.analysis_id)
            item.setData(260, analysis.analysis_id)
            self.table.setItem(row, col, item)

    def _on_table_item_clicked(self, item: QTableWidgetItem):
        """Handle table row click."""
        analysis_id = item.data(Qt.ItemDataRole.UserRole)

        if analysis_id is None:
            row = item.row()
            fallback_item = self.table.item(row, 1)
            if fallback_item:
                analysis_id = fallback_item.data(Qt.ItemDataRole.UserRole)

        if analysis_id is not None:
            self.analysis_selected.emit(analysis_id)

    def clear(self):
        """Reset page state."""
        self.analyses = []
        self.table.setRowCount(0)
        self._update_empty_state()
