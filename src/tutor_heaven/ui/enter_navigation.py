from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QPlainTextEdit,
)


class EnterToNextFilter(QObject):
    """Event filter for dialogs: Enter moves to the next field.

    Sin este filtro, pulsar Enter dentro de un QLineEdit en un QDialog
    activa el botón por defecto (OK) y cierra la ventana. Este filtro
    intercepta la tecla Enter y, en su lugar:

    - Si el widget enfocado tiene un atributo _enter_action, lo ejecuta
      (p.ej. añadir un interés) y mantiene el foco para seguir
      escribiendo.
    - Si es un campo de una sola línea, mueve el foco al siguiente
      campo (comportamiento "Enter = siguiente campo").
    - Los botones, checkboxes y campos de texto multilínea (QPlainTextEdit)
      conservan su comportamiento normal (activar / nueva línea).
    """

    def eventFilter(self, obj, event):
        if (
            event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        ):
            widget = QApplication.focusWidget()

            if widget is not None and not isinstance(
                widget,
                (QAbstractButton, QPlainTextEdit),
            ):
                action = getattr(
                    widget,
                    "_enter_action",
                    None,
                )

                if callable(action):
                    action()
                else:
                    widget.focusNextChild()

                # Consume el evento para que el diálogo no lo acepte.
                return True

        return super().eventFilter(obj, event)


def enable_enter_to_next(dialog) -> EnterToNextFilter:
    """Instala el filtro Enter->siguiente campo en un diálogo."""
    filter_ = EnterToNextFilter(dialog)

    dialog.installEventFilter(filter_)

    return filter_
