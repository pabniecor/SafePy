"""Central presenter coordinating user interactions and services."""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from app.services.dependency_analysis_service import DependencyAnalysisService
from app.services.history_service import HistoryService
from app.services.file_parser_service import FileParserService
from app.domain.models import Analysis, Dependency


class UIPresenter(QObject):
    """Coordinates all UI interactions and business logic using services."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Initialize services
        self.analysis_service = DependencyAnalysisService()
        self.history_service = HistoryService()
        self.file_parser_service = FileParserService()

        # State management
        self.current_analysis: Optional[Analysis] = None
        self.current_analysis_id: Optional[int] = None
        self.navigation_stack: list[int] = [0]  # Start at home page
        self.selected_dependency: Optional[Dependency] = None

    def setup_connections(self):
        """Connect all page signals to presenter slots."""
        # HomePage connections
        if self.main_window.home_page:
            self.main_window.home_page.new_analysis_clicked.connect(
                self.on_home_new_analysis_clicked
            )
            self.main_window.home_page.view_history_clicked.connect(
                self.on_home_view_history_clicked
            )

        # UploadPage connections
        if self.main_window.upload_page:
            self.main_window.upload_page.analyze_clicked.connect(
                self.on_upload_analyze_clicked
            )
            self.main_window.upload_page.back_to_menu_clicked.connect(self.on_back_to_menu_clicked)

        # ResultsPage connections
        if self.main_window.results_page:
            self.main_window.results_page.dependency_clicked.connect(
                self.on_results_dependency_clicked
            )
            self.main_window.results_page.back_to_menu_clicked.connect(self.on_back_to_menu_clicked)

        # HistoryPage connections
        if self.main_window.history_page:
            self.main_window.history_page.analysis_selected.connect(
                self.on_history_analysis_selected
            )
            self.main_window.history_page.back_to_menu_clicked.connect(self.on_back_to_menu_clicked)

    def navigate_to(self, page_index: int):
        """Navigate to a page and update navigation stack."""
        self.navigation_stack.append(page_index)
        self.main_window.show_page(page_index)

    def on_back_to_menu_clicked(self):
        """Handle back button click - navigate to previous page."""
        if len(self.navigation_stack) > 1:
            self.navigation_stack = [0]
            self.main_window.show_page(0)

    # ==================== HomePage Handlers ====================

    def on_home_new_analysis_clicked(self):
        """User clicked 'Nuevo análisis' on HomePage."""
        # Reset upload page state
        if self.main_window.upload_page:
            self.main_window.upload_page.clear_inputs()
        # Navigate to upload page
        self.navigate_to(self.main_window.PAGE_UPLOAD)
        self.main_window.show_status("Selecciona un archivo de dependencias")

    def on_home_view_history_clicked(self):
        """User clicked 'Ver historial' on HomePage."""
        try:
            # Load analyses from database
            analyses = self.history_service.get_all_analyses()
            if self.main_window.history_page:
                self.main_window.history_page.set_analyses(analyses)
            self.navigate_to(self.main_window.PAGE_HISTORY)
        except Exception as e:
            self.main_window.show_error(f"Error al cargar historial: {str(e)}", critical=True)

    # ==================== UploadPage Handlers ====================

    def on_upload_analyze_clicked(self, file_path: str, analysis_name: str):
        """User clicked 'Iniciar análisis' on UploadPage."""
        try:
            # Validate inputs
            if not file_path or not analysis_name:
                self.main_window.show_error("Por favor selecciona un archivo y nombre", critical=False)
                return

            # Show loading state
            self.main_window.show_status("Analizando dependencias...")

            # Import here to avoid circular imports
            from app.ui.workers.analysis_worker import AnalysisWorker

            # Create worker for background analysis
            worker = AnalysisWorker(
                self.analysis_service, file_path, analysis_name
            )
            worker.signals.started.connect(self._on_analysis_started)
            worker.signals.progress.connect(self._on_analysis_progress)
            worker.signals.finished.connect(self._on_analysis_finished)
            worker.signals.error.connect(self._on_analysis_error)

            # Execute in thread pool
            self.main_window.run_worker(worker)

        except Exception as e:
            self.main_window.show_error(f"Error iniciando análisis: {str(e)}", critical=True)

    def _on_analysis_started(self):
        """Analysis worker started."""
        self.main_window.show_status("Iniciando análisis...")

    def _on_analysis_progress(self, message: str):
        """Analysis worker progress update."""
        self.main_window.show_status(message)

    def _on_analysis_finished(self, analysis: Analysis):
        """Analysis worker completed successfully."""
        self.current_analysis = analysis
        self.current_analysis_id = analysis.analysis_id if hasattr(analysis, 'analysis_id') else None

        # Update results page
        if self.main_window.results_page:
            self.main_window.results_page.set_analysis(analysis)

        # Navigate to results
        self.navigate_to(self.main_window.PAGE_RESULTS)
        self.main_window.show_status("Análisis completado")

    def _on_analysis_error(self, error_message: str):
        """Analysis worker encountered an error."""
        self.main_window.show_error(f"Error en análisis: {error_message}", critical=True)

    # ==================== ResultsPage Handlers ====================

    def on_results_dependency_clicked(self, dependency: Dependency):
        """User clicked on a dependency with vulnerabilities."""
        try:
            self.selected_dependency = dependency

            # Import here to avoid circular imports
            from app.ui.dialogs.vulnerability_detail_dialog import VulnerabilityDetailDialog

            # Create and show vulnerability detail dialog
            dialog = VulnerabilityDetailDialog(self.main_window)
            dialog.set_vulnerability_from_dependency(dependency)
            self.main_window.show_dialog(dialog)

        except Exception as e:
            self.main_window.show_error(f"Error mostrando detalles: {str(e)}", critical=True)

    # ==================== HistoryPage Handlers ====================

    def on_history_analysis_selected(self, analysis_id: int):
        """User selected an analysis from history."""
        try:
            # Load analysis from database
            analysis = self.history_service.get_analysis(analysis_id)
            self.current_analysis = analysis
            self.current_analysis_id = analysis.analysis_id if hasattr(analysis, 'analysis_id') else None

            # Update results page
            if self.main_window.results_page:
                self.main_window.results_page.set_analysis(analysis)

            # Navigate to results
            self.navigate_to(self.main_window.PAGE_RESULTS)
            self.main_window.show_status("Análisis cargado")

        except Exception as e:
            self.main_window.show_error(f"Error cargando análisis: {str(e)}", critical=True)
