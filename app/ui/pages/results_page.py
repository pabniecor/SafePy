"""Results page - Analysis results display."""

from typing import Optional
from PySide6.QtWidgets import (
    QLayout,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from app.domain.models import Analysis, Dependency


class ResultsPage(QWidget):
    """Page displaying analysis results."""

    dependency_clicked = Signal(Dependency)
    back_clicked = Signal()

    # Severity color mapping
    SEVERITY_COLORS = {
        "CRITICAL": QColor(204, 0, 160),  # Pink/Magenta
        "HIGH": QColor(204, 0, 0),      # Red
        "MEDIUM": QColor(255, 200, 0),  # Yellow
        "LOW": QColor(100, 150, 255),   # Blue
        "UNKNOWN": QColor(150, 150, 150),  # Gray
    }

    def __init__(self):
        super().__init__()
        self.current_analysis: Optional[Analysis] = None
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
        title = QLabel("Resultados del análisis")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Summary section
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(20)

        # Total dependencies card
        self.deps_card = self._create_summary_card("Dependencias", "0")
        summary_layout.addWidget(self.deps_card)

        # Vulnerabilities card
        self.vulns_card = self._create_summary_card("Vulnerabilidades", "0")
        summary_layout.addWidget(self.vulns_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Dependencia", "Versión", "Severidad", "Recomendación"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemClicked.connect(self._on_table_item_clicked)
        layout.addWidget(self.table)

        # Observations/notes
        self.notes_label = QLabel("")
        self.notes_label.setWordWrap(True)
        self.notes_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.notes_label)

        self.setLayout(layout)

    def _create_summary_card(self, label: str, value: str) -> QFrame:
        """Create a summary info card."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            "border: 1px solid #CCCCCC; border-radius: 8px; "
            "background-color: #F5F5F5; padding: 15px;"
        )
        card.setMinimumWidth(150)

        layout = QVBoxLayout()
        layout.setSpacing(5)

        label_widget = QLabel(label)
        font = QFont()
        font.setPointSize(10)
        label_widget.setFont(font)
        label_widget.setStyleSheet("color: #666666;")
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(20)
        value_font.setBold(True)
        value_widget.setFont(value_font)
        value_widget.setStyleSheet("color: #0099CC;")
        layout.addWidget(value_widget)

        card.setLayout(layout)
        return card

    def set_analysis(self, analysis: Analysis):
        """Populate page with analysis data."""
        self.current_analysis = analysis

        # Count dependencies and vulnerabilities
        total_deps = len(analysis.dependencies) if analysis.dependencies else 0
        vuln_count = sum(
            1 for dep in (analysis.dependencies or [])
            if dep.vulnerabilities and len(dep.vulnerabilities) > 0
        )

        # Update summary cards
        self._update_summary_card(self.deps_card, str(total_deps))
        self._update_summary_card(self.vulns_card, str(vuln_count))

        # Populate table
        self.table.setRowCount(total_deps)
        for row, dependency in enumerate(analysis.dependencies or []):
            self._populate_table_row(row, dependency)

        # Set notes if analysis has observations
        if hasattr(analysis.result, 'observations') and analysis.result.observations:
            self.notes_label.setText(f"Observaciones: {analysis.result.observations}")
        else:
            self.notes_label.setText("")

    def _update_summary_card(self, card: QFrame, value: str):
        """Update the value in a summary card."""
        # Get the second label (the value label) from the card's layout
        layout: QLayout | None = card.layout()
        if layout is None:
            return
        
        if layout.count() >= 2:
            value_item = layout.itemAt(1)

            if value_item:
                widget = value_item.widget()
                if not isinstance(widget, QLabel):
                    return
                widget.setText(value)

    def _populate_table_row(self, row: int, dependency: Dependency):
        """Populate a single table row with dependency data."""
        # Dependency name
        name_item = QTableWidgetItem(dependency.name or "")
        name_item.setData(Qt.ItemDataRole.UserRole, dependency)  # Store dependency object
        self.table.setItem(row, 0, name_item)

        # Version
        version_item = QTableWidgetItem(dependency.version or "")
        self.table.setItem(row, 1, version_item)

        # Severity and recommendation
        if dependency.vulnerabilities and len(dependency.vulnerabilities) > 0:
            # Has vulnerabilities - show highest severity
            max_severity = self._get_max_severity([v.severity for v in dependency.vulnerabilities])

            severity_item = QTableWidgetItem(max_severity or "UNKNOWN")
            color = self.SEVERITY_COLORS.get(max_severity, QColor(100, 100, 100))
            severity_item.setForeground(color)
            value_font = QFont()
            value_font.setWeight(QFont.Weight.Bold)
            severity_item.setFont(value_font)
            self.table.setItem(row, 2, severity_item)

            # Recommendation (simple - show fixed version if available)
            recommendation = self._get_recommendation(dependency)
            recommendation_item = QTableWidgetItem(recommendation)
            self.table.setItem(row, 3, recommendation_item)

            # Highlight row to indicate it's clickable
            for col in range(4):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QColor(240, 248, 255))  # Light blue
        else:
            # No vulnerabilities - green/safe
            severity_item = QTableWidgetItem("Seguro")
            severity_item.setForeground(QColor(0, 170, 0))
            value_font = QFont()
            value_font.setWeight(QFont.Weight.Bold)
            severity_item.setFont(value_font)
            self.table.setItem(row, 2, severity_item)

            recommendation_item = QTableWidgetItem("Actualizado")
            self.table.setItem(row, 3, recommendation_item)

    def _get_max_severity(self, severities: list[str | None]) -> str:
        """Get the highest severity from a list."""
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        for sev in severity_order:
            if sev in severities:
                return sev
        return "UNKNOWN"

    def _get_recommendation(self, dependency: Dependency) -> str:
        """Get recommendation text for a dependency."""
        if not dependency.vulnerabilities:
            return "Actualizado"

        # Check for fixed versions across vulnerabilities
        fixed_versions = set()
        for vuln in dependency.vulnerabilities:
            if hasattr(vuln, 'fixed_version') and vuln.fixed_version:
                fixed_versions.add(vuln.fixed_version)

        if fixed_versions:
            return f"Actualizar a: {', '.join(sorted(fixed_versions))}"
        return "Revisar vulnerabilidades"

    def _on_table_item_clicked(self, item: QTableWidgetItem):
        """Handle table item click."""
        dependency = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(dependency, Dependency) and dependency.vulnerabilities:
            self.dependency_clicked.emit(dependency)

    def clear(self):
        """Reset page state."""
        self.current_analysis = None
        self.table.setRowCount(0)
        self._update_summary_card(self.deps_card, "0")
        self._update_summary_card(self.vulns_card, "0")
        self.notes_label.setText("")
