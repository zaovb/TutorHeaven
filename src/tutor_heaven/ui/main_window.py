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
from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.i18n import set_language, tr
from tutor_heaven.ui.title_bar import TitleBar
from tutor_heaven.ui.widgets.calendar import Calendar
from tutor_heaven.ui.widgets.dashboard import Dashboard
from tutor_heaven.ui.widgets.settings_dialog import SettingsDialog
from tutor_heaven.ui.widgets.student_browser import StudentBrowser


class MainWindow(QMainWindow):
    """Main application window.

    Ventana principal sin marco nativo con una barra de título propia
    (minimizar, maximizar, pantalla completa y cerrar). Organiza la
    app en pestañas: un Dashboard de bienvenida, el Calendario y el
    navegador de estudiantes. El idioma de la interfaz se aplica al
    arrancar desde la configuración y se reconstruye si cambia.
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

        # Calendario semanal siempre visible como pestaña.
        self.calendar = Calendar()

        # Si en el calendario se elige "New student...", se lleva al
        # usuario a la pestaña de matrículas para dar de alta.
        self.calendar.openEnrollment.connect(
            lambda: self.tabs.setCurrentWidget(
                self.student_browser
            )
        )

        self.tabs.addTab(
            self.calendar,
            tr("Calendar"),
        )

        # Navegador de estudiantes (lista + perfiles).
        self.student_browser = StudentBrowser()

        self.tabs.addTab(
            self.student_browser,
            tr("Students"),
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

    def open_settings(self) -> None:
        """Abre el diálogo de configuración y reconstruye la interfaz
        si el idioma o el tema cambiaron."""
        from PySide6.QtWidgets import QApplication

        from tutor_heaven.ui.themes import apply_theme

        before_lang = get_settings().language
        before_theme = get_settings().theme

        dialog = SettingsDialog(
            get_settings()
        )

        dialog.exec()

        after_lang = get_settings().language
        after_theme = get_settings().theme

        if before_lang != after_lang or before_theme != after_theme:
            # Aplica el tema elegido y reconstruye toda la interfaz
            # (las cadenas se traducen al crear los widgets).
            apply_theme(
                QApplication.instance()
            )
            self.build_ui()

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
