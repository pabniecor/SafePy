"""Worker thread for background analysis execution."""

from PySide6.QtCore import QRunnable, QObject, Signal
from app.domain.models import Analysis
from app.services.dependency_analysis_service import DependencyAnalysisService


class WorkerSignals(QObject):
    """Signals emitted by worker."""

    started = Signal()
    progress = Signal(str)  # Progress message
    finished = Signal(Analysis)  # Completed analysis
    error = Signal(str)  # Error message


class AnalysisWorker(QRunnable):
    """Worker thread for executing dependency analysis."""

    def __init__(self, service: DependencyAnalysisService, file_path: str, analysis_name: str):
        super().__init__()
        self.service = service
        self.file_path = file_path
        self.analysis_name = analysis_name
        self.signals = WorkerSignals()

    def run(self):
        """Execute analysis in background thread."""
        try:
            self.signals.started.emit()
            self.signals.progress.emit("Iniciando análisis...")

            # Call service to analyze file
            # The service will handle parsing and OSV queries
            analysis = self.service.analyze_from_file(
                self.file_path,
                self.analysis_name,
            )

            self.signals.progress.emit("Análisis completado")
            self.signals.finished.emit(analysis)

        except Exception as e:
            error_message = str(e)
            self.signals.error.emit(error_message)
