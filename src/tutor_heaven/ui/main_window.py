from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSizeGrip,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.app_info import APP_NAME
from tutor_heaven.data.backup import start_backup_sync
from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.data.vault import start_vault_sync, sync_vault
from tutor_heaven.i18n import set_language, tr
from tutor_heaven.ui.title_bar import TitleBar
from tutor_heaven.ui.widgets.about_dialog import AboutDialog
from tutor_heaven.ui.widgets.dashboard import Dashboard
from tutor_heaven.ui.widgets.settings_dialog import SettingsDialog
from tutor_heaven.ui.widgets.student_browser import StudentBrowser
from tutor_heaven.ui.widgets.teacher_tasks_view import TeacherTasksView


class MainWindow(QMainWindow):
    """Main application window.

    Ventana principal sin marco nativo con una barra de título propia
    (minimizar, maximizar, pantalla completa y cerrar). Organiza la
    app en pestañas: un Dashboard de bienvenida y el navegador de
    estudiantes. El idioma de la interfaz se aplica al arrancar desde
    la configuración y se reconstruye si cambia.
    """

    def __init__(self) -> None:
        super().__init__()

        # Aplica el idioma guardado en la configuración.
        set_language(get_settings().language)

        self.setWindowTitle(APP_NAME)

        # Sin marco nativo: los controles de ventana son propios.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )

        # Tamaño por defecto, ajustado al área disponible de la pantalla
        # actual para que la ventana quepa en cualquier monitor.
        screen = QApplication.primaryScreen()

        if screen is not None:
            available = screen.availableGeometry()
            width = min(1280, available.width() - 48)
            height = min(800, available.height() - 48)
        else:
            width, height = 1280, 800

        self.resize(width, height)

        self.build_ui()

        # En pantalla completa la barra de título se oculta; Esc permite
        # salir de nuevo (alternativa al botón de la barra).
        self._exit_fullscreen_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Escape),
            self,
        )

        self._exit_fullscreen_shortcut.activated.connect(
            self._exit_fullscreen
        )

        # Bóveda de Obsidian: si está activa, se generan las notas de
        # cada estudiante y se mantienen al día con los datos.
        start_vault_sync()

        # Backup en un .zip: si está activo, se actualiza solo con cada
        # cambio de datos.
        start_backup_sync()

    def _exit_fullscreen(self) -> None:
        """Sale de pantalla completa y restaura la barra de título."""
        if not self.isFullScreen():
            return

        self.showNormal()

        self.title_bar.setVisible(True)

    def build_ui(self) -> None:
        """Construye (o reconstruye) toda la interfaz de la ventana.

        Al cambiar el idioma se elimina el contenido actual y se crea
        de nuevo, ya que las cadenas se traducen al crear los widgets.
        """
        # Elimina el widget central anterior (si lo hay).
        if self.centralWidget() is not None:
            old = self.centralWidget()
            self.setCentralWidget(QWidget())
            old.deleteLater()

        container = QWidget()

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de título personalizada.
        self.title_bar = TitleBar(
            APP_NAME,
            self,
        )

        layout.addWidget(self.title_bar)

        # Barra superior con el botón de configuración.
        self.toolbar = QToolBar()

        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextOnly
        )

        settings_action = self.toolbar.addAction(
            tr("⚙ Settings")
        )

        settings_action.triggered.connect(
            self.open_settings
        )

        about_action = self.toolbar.addAction(
            tr("ℹ About")
        )

        about_action.triggered.connect(
            self.open_about
        )

        layout.addWidget(self.toolbar)

        # Pestañas de la aplicación.
        self.tabs = QTabWidget()

        self.dashboard = Dashboard()

        self.dashboard.studentSelected.connect(
            self.open_student
        )

        self.tabs.addTab(
            self.dashboard,
            tr("Dashboard"),
        )

        # Navegador de estudiantes (lista + perfiles).
        self.student_browser = StudentBrowser()

        self.tabs.addTab(
            self.student_browser,
            tr("Students"),
        )

        # Tareas del profesor: generales y agrupadas por estudiante.
        self.teacher_tasks = TeacherTasksView()

        self.tabs.addTab(
            self.teacher_tasks,
            tr("Teacher Tasks"),
        )

        layout.addWidget(self.tabs, stretch=1)

        # Esquina para redimensionar la ventana sin marco.
        grip_bar = QWidget()

        grip_layout = QHBoxLayout(grip_bar)
        grip_layout.setContentsMargins(0, 0, 0, 0)

        grip_layout.addStretch()

        grip_layout.addWidget(
            QSizeGrip(self)
        )

        layout.addWidget(grip_bar)

        self.setCentralWidget(container)

    def open_about(self) -> None:
        """Abre el diálogo 'Acerca de'."""
        dialog = AboutDialog()
        dialog.exec()

    def open_settings(self) -> None:
        """Abre el diálogo de configuración y reconstruye la interfaz
        si el idioma o el tema cambiaron."""
        from PySide6.QtWidgets import QApplication

        from tutor_heaven.ui.themes import apply_theme

        before_lang = get_settings().language
        before_mode = get_settings().theme_mode
        before_primary = get_settings().theme_primary
        before_secondary = get_settings().theme_secondary

        dialog = SettingsDialog(
            get_settings()
        )

        dialog.exec()

        # El usuario restauró el estado de fábrica: se reconstruye toda
        # la interfaz con los datos y la configuración limpios.
        if dialog.factory_reset_done:
            set_language(get_settings().language)
            apply_theme(
                QApplication.instance()
            )
            self.build_ui()
            return

        after_lang = get_settings().language
        after_mode = get_settings().theme_mode
        after_primary = get_settings().theme_primary
        after_secondary = get_settings().theme_secondary

        if (
            before_lang != after_lang
            or before_mode != after_mode
            or before_primary != after_primary
            or before_secondary != after_secondary
        ):
            # Aplica el tema elegido y reconstruye toda la interfaz
            # (las cadenas se traducen al crear los widgets).
            apply_theme(
                QApplication.instance()
            )
            self.build_ui()

        # Recalcula la bóveda de Obsidian por si se activó o cambió la
        # carpeta en la configuración.
        sync_vault()

        # Genera el backup por si se activó o cambió la ruta.
        from tutor_heaven.data.backup import update_backup

        update_backup()

    def open_student(
        self,
        student,
    ) -> None:
        """Cambia a la pestaña de estudiantes y abre el perfil."""
        self.tabs.setCurrentWidget(
            self.student_browser
        )

        self.student_browser.open_student_by_name(
            student.name
        )
