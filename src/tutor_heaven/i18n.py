"""Sistema de traducciones de la interfaz (Inglés / Español).

El idioma activo se guarda en la configuración (Settings.language) y
se aplica al arrancar la aplicación. Todas las cadenas visibles de la
interfaz deben pasarse por tr() para que se traduzcan automáticamente:

    label = QLabel(tr("Add Session"))

Los valores que se guardan en datos (por ejemplo payment_mode) NO se
traducen: son claves estables del modelo; solo se traduce su texto
visible en pantalla.
"""

LANGUAGE_ENGLISH = "en"
LANGUAGE_SPANISH = "es"

# Traducciones al español. Las claves son las cadenas originales en
# inglés; tr() devuelve la misma cadena si no hay traducción.
_ES: dict[str, str] = {}

# Código de idioma activo.
_current: str = LANGUAGE_ENGLISH


def set_language(code: str) -> None:
    """Fija el idioma activo de la interfaz (en/es)."""
    global _current

    if code in (LANGUAGE_ENGLISH, LANGUAGE_SPANISH):
        _current = code


def tr(text: str) -> str:
    """Traduce una cadena de la interfaz al idioma activo.

    Si el idioma activo es inglés (o la cadena no está traducida),
    devuelve el texto original.
    """
    if _current != LANGUAGE_SPANISH:
        return text

    return _ES.get(text, text)


_ES = {
    # ---------- Ventana principal ----------
    "Dashboard": "Inicio",
    "Students": "Estudiantes",
    "⚙ Settings": "⚙ Configuración",
    "ℹ About": "ℹ Acerca de",

    # ---------- Diálogo About ----------
    "About": "Acerca de",
    "Private tutor management application": "Aplicación de gestión de tutoría privada",
    "Developer: {0}": "Desarrollador: {0}",
    "Built with: OpenCode": "Hecha con: OpenCode",
    "License: GPL-3.0": "Licencia: GPL-3.0",

    # ---------- Barra de título / botones de ventana ----------
    "Minimize": "Minimizar",
    "Maximize": "Maximizar",
    "Fullscreen": "Pantalla completa",
    "Close": "Cerrar",

    # ---------- Diálogo de sesión ----------
    "Add Session": "Añadir Sesión",
    "Edit Session": "Editar Sesión",
    "Invalid Session": "Sesión no válida",
    "End time must be after start time.": "La hora de fin debe ser posterior a la de inicio.",
    "Date": "Fecha",
    "Start Time": "Hora de inicio",
    "End Time": "Hora de fin",
    "Topic": "Tema",
    "Status": "Estado",
    "Notes": "Notas",
    "Payment": "Pago",
    "Pending": "Pendiente",
    "Completed": "Completada",
    "Cancelled": "Cancelada",
    "✓ Paid": "✓ Pagada",
    "Pay later (not paid)": "Paga después (sin pagar)",
    "Progress": "Progreso",
    "Overlapping Classes": "Clases que se solapan",
    "This class overlaps another class of {0}. Choose a different time.": "Esta clase se solapa con otra clase de {0}. Elige una hora diferente.",
    "Student": "Estudiante",
    "➕ Add Class": "➕ Añadir clase",

    # ---------- Diálogo de progreso de clase ----------
    "New Viewed Class": "Nueva clase vista",
    "Class Information": "Información de la Clase",
    "Hours Available:": "Horas disponibles:",
    "Hours Owed:": "Horas por pagar:",
    "Homework Done": "Tarea hecha",
    "Completed the homework": "Completó la tarea",
    "Task:": "Tarea:",
    "Had no task": "No tenía tarea",
    "Conversation Topic": "Tema de conversación",
    "Conversation Topic:": "Tema de conversación:",
    "Grammar Learned": "Gramática aprendida",
    "Grammar Learned:": "Gramática aprendida:",
    "Homework": "Tarea",
    "Next Task:": "Próxima tarea:",
    "To Learn Next": "Por ver en la próxima",
    "To Learn Next:": "Por ver en la próxima:",
    "Student Interests": "Intereses del estudiante",
    "Add an interest (hobby, topic...)": "Añadir un interés (afición, tema...)",
    "➕ Add Interest": "➕ Añadir interés",
    "Remove Selected": "Quitar seleccionado",
    "Teacher Tasks": "Tareas del profesor",
    "General Tasks": "Tareas generales",
    "➕ Add Task": "➕ Añadir tarea",
    "New task for this student...": "Nueva tarea para este estudiante...",
    "New task...": "Nueva tarea...",
    "No teacher tasks yet": "Aún no hay tareas del profesor",
    "Notes...": "Notas...",
    "🗑 Deleted Tasks": "🗑 Tareas eliminadas",
    "↩ Active Tasks": "↩ Tareas activas",
    "↩ Restore Task": "↩ Restaurar tarea",

    # ---------- Perfil del estudiante ----------
    "📋 Resume": "📋 Hoja de Vida",
    "🗑 Delete": "🗑 Eliminar",
    "✏️ Edit": "✏️ Editar",
    "Enrollment": "Matrícula",
    "Sessions": "Sesiones",
    "Packages": "Paquetes",
    "Tasks": "Tareas",
    "Files": "Archivos",
    "Statistics": "Estadísticas",
    "{0} module": "{0} módulo",
    "↩ Unmark as former": "↩ Desmarcar como antiguo",
    "📦 Mark as former": "📦 Marcar como antiguo",
    "Enrollment Information": "Información de la matrícula",
    "No upcoming scheduled class": "No hay clase próxima programada",
    "Next class: {0} {1}": "Próxima clase: {0} {1}",
    "hours available": "horas disponibles",
    "hours owed": "horas por pagar",
    "✅ Mark Class as Viewed": "✅ Añadir clase vista",
    "Mark a class as done: records progress and consumes its duration from the package.": "Marca la clase como vista: registra el progreso y consume su duración del paquete.",
    "Delete student": "Eliminar estudiante",
    "Move {0} to deleted students?\n\nYou can restore them later from the Deleted list.": "¿Mover a {0} a estudiantes eliminados?\n\nPuedes restaurarlo más tarde desde la lista de Eliminados.",
    "Delete student forever": "Eliminar estudiante para siempre",
    "Permanently delete {0}?\n\nAll their packages, sessions, payments and notes will be permanently removed, including their observer base note. This action cannot be undone.": "¿Eliminar definitivamente a {0}?\n\nTodos sus paquetes, sesiones, pagos y notas se eliminarán de forma permanente, incluida su nota de la bóveda de Obsidian. Esta acción no se puede deshacer.",
    "🗑 Deleted": "🗑 Eliminados",
    "↩ Active Students": "↩ Estudiantes activos",
    "↩ Restore Student": "↩ Restaurar estudiante",
    "🗑 Delete Forever": "🗑 Eliminar para siempre",
    "0 ({0} h owed)": "0 ({0} h por pagar)",

    # ---------- Tabla de sesiones ----------
    "Start": "Inicio",
    "End": "Fin",
    "Paid": "Pagado",
    "Not paid": "Sin pagar",
    "Session Detail": "Detalle de sesión",
    "Time": "Hora",
    "Yes": "Sí",
    "No": "No",
    "✏️ Edit Session": "✏️ Editar sesión",
    "🗑 Delete Session": "🗑 Eliminar sesión",
    "🗑 Deleted Sessions": "🗑 Sesiones eliminadas",
    "↩ Active Sessions": "↩ Sesiones activas",
    "↩ Restore Session": "↩ Restaurar sesión",
    "Select a session to edit first.": "Selecciona primero una sesión para editar.",
    "Select a session to delete first.": "Selecciona primero una sesión para eliminar.",
    "Select a session to restore first.": "Selecciona primero una sesión para restaurar.",
    "Restore session": "Restaurar sesión",
    "Delete session": "Eliminar sesión",
    "Delete session forever": "Eliminar sesión para siempre",
    "Delete session {0} {1} forever?\n\nThis session and its progress will be permanently removed. This action cannot be undone.": "¿Eliminar para siempre la sesión {0} {1}?\n\nEsta sesión y su progreso se eliminarán de forma permanente. Esta acción no se puede deshacer.",

    # ---------- Paquetes ----------
    "➕ Add Hours to Package": "➕ Añadir horas al paquete",
    "Package Summary": "Resumen del paquete",
    "Package History": "Historial de paquetes",
    "Current Package": "Paquete actual",
    "Previous Package {0}": "Paquete anterior {0}",
    "Package {0}": "Paquete {0}",
    "Purchased On": "Comprado el",
    "Hours Purchased": "Horas compradas",
    "Hours Taken": "Horas dadas",
    "Hours Left": "Horas restantes",
    "Hours Owed": "Horas por pagar",
    "Finished": "TERMINADO",
    "Date of Payment": "Fecha de pago",
    "Date of Start": "Fecha de inicio",
    "Discount": "Descuento",
    "Hourly Price": "Precio por hora",
    "Total": "Total",
    "Total Paid": "Total histórico pagado",
    "Debt": "Deuda",
    "Active": "Activo",
    "Former": "Antiguo",
    "Eliminated": "Eliminado",
    "Eliminated Students": "Estudiantes eliminados",
    "No eliminated students": "No hay estudiantes eliminados",
    "Pay in advance": "Pago por adelantado",
    "Pay later": "Paga después",
    "Package Total": "Total del paquete",
    "Amount Paid": "Cantidad pagada",
    "Amount Owed": "Cantidad pendiente",

    # ---------- Diálogo de paquete ----------
    "Add Hours to Package": "Añadir Horas al Paquete",
    "Edit Package": "Editar Paquete",
    "Paid Package": "Paquete pagado",
    "Unpaid Package": "Paquete por pagar",
    "📦 Package Purchased": "📦 Paquete comprado",
    "New Block": "Bloque nuevo",
    "Hours to Add": "Horas a añadir",
    "Dates": "Fechas",
    "Mode": "Modo",
    "Payment Mode": "Modo de pago",
    "Payment Status": "Estado de pago",
    "Block Price": "Precio del bloque",
    "Summary": "Resumen",
    "✏️ Edit Package": "✏️ Editar Paquete",

    # ---------- Diálogo de estudiante ----------
    "New Student": "Nuevo Estudiante",
    "Basic Information": "Información básica",
    "Name": "Nombre",
    "Type": "Tipo",
    "Individual": "Individual",
    "Group": "Grupo",
    "Custom": "Personalizado",
    "Email": "Email",
    "Phone": "Teléfono",
    "Initial Package": "Paquete inicial",
    "Package Price": "Precio del paquete",
    "Level": "Nivel",
    "Apply Discount": "Aplicar Descuento",
    "No discount": "Sin descuento",
    "Grammar Topics": "Temas gramaticales",
    "Edit Student": "Editar Estudiante",
    "Grammar Topic": "Tema gramatical",
    "That topic is already added.": "Ese tema ya está añadido.",
    "Add a grammar topic (e.g. Present Perfect)": "Añade un tema gramatical (p. ej. Present Perfect)",
    "➕ Add Topic": "➕ Añadir Tema",
    "Confirm Changes": "Confirmar Cambios",
    "Do you want to apply these changes to {0}?": "¿Quieres aplicar estos cambios a {0}?",

    # ---------- Configuración ----------
    "Settings": "Configuración",
    "Teacher Profile": "Perfil del profesor",
    "Teacher Name": "Nombre del profesor",
    "Teacher Email": "Email del profesor",
    "Teacher Phone": "Teléfono del profesor",
    "Prices": "Precios",
    "Individual price": "Precio individual",
    "Group price": "Precio de grupo",
    "Discount threshold 1": "Umbral de descuento 1",
    "Discount 1": "Descuento 1",
    "Discount threshold 2": "Umbral de descuento 2",
    "Discount 2": "Descuento 2",
    " hours": " horas",
    "Ideas, reminders, anything...\n(here Enter inserts a new line)": "Ideas, recordatorios, lo que sea...\n(aquí Enter inserta una línea nueva)",
    "Language": "Idioma",
    "English": "Inglés",
    "Spanish": "Español",
    "Theme": "Tema",
    "Light": "Claro",
    "Dark": "Oscuro",
    "Primary Color": "Color principal",
    "Secondary Color": "Color secundario",
    "Obsidian Vault": "Bóveda de Obsidian",
    "Enable Obsidian vault": "Activar bóveda de Obsidian",
    "Vault Folder": "Carpeta de la bóveda",
    "Folder Obsidian will open as a vault.": "Carpeta que Obsidian abrirá como bóveda.",
    "One note per student, updated automatically as data changes.": "Una nota por estudiante, actualizada automáticamente al cambiar los datos.",

    # ---------- Backup ----------
    "Backup": "Copia de seguridad",
    "Enable automatic backup": "Activar copia de seguridad automática",
    "A portable .zip with all data and readable notes. You can open it with any editor.": "Un .zip portátil con todos los datos y notas legibles. Puedes abrirlo con cualquier editor.",
    "📦 Export Backup Now": "📦 Exportar copia de seguridad ahora",
    "♻ Restore from Backup": "♻ Restaurar desde copia de seguridad",
    "Backup Folder": "Carpeta de copia de seguridad",
    "Export Backup": "Exportar copia de seguridad",
    "Restore from Backup": "Restaurar desde copia de seguridad",
    "Backup file (*.zip)": "Archivo de copia de seguridad (*.zip)",
    "Could not export the backup:\n{0}": "No se pudo exportar la copia de seguridad:\n{0}",
    "Could not restore from the backup:\n{0}": "No se pudo restaurar desde la copia de seguridad:\n{0}",
    "Backup exported successfully to:\n{0}": "Copia de seguridad exportada correctamente a:\n{0}",
    "Restore all data from the backup?\n\nCurrent students, sessions and settings will be overwritten. This cannot be undone.": "¿Restaurar todos los datos desde la copia de seguridad?\n\nLos estudiantes, sesiones y la configuración actuales se sobrescribirán. Esta acción no se puede deshacer.",
    "Data restored successfully:\n{0} students, {1} deleted, {2} teacher tasks.": "Datos restaurados correctamente:\n{0} estudiantes, {1} eliminados, {2} tareas del profesor.",
    "Unsupported backup version: {0}": "Versión de copia de seguridad no soportada: {0}",
    "Choose a folder outside the app...": "Elige una carpeta fuera de la aplicación...",
    "📁 Choose Folder": "📁 Elegir carpeta",
    "Choose Backup Folder": "Elegir carpeta de copia de seguridad",
    "The backup is stored outside the app so it survives an uninstall.": "La copia de seguridad se guarda fuera de la aplicación para que sobreviva a una desinstalación.",
    "The backup folder cannot be inside the app folder.\n\nChoose an external location (for example Documents) so the backup survives an uninstall.": "La carpeta de la copia de seguridad no puede estar dentro de la carpeta de la aplicación.\n\nElige una ubicación externa (por ejemplo Documentos) para que la copia sobreviva a una desinstalación.",
    "Automatic backup needs a folder OUTSIDE the app.\n\nChoose an external location (for example Documents) so the backup survives an uninstall.": "La copia de seguridad automática necesita una carpeta FUERA de la aplicación.\n\nElige una ubicación externa (por ejemplo Documentos) para que la copia sobreviva a una desinstalación.",

    # ---------- Restablecer a estado de fábrica ----------
    "Danger Zone": "Zona de peligro",
    "Restore to Factory State": "Restablecer a estado de fábrica",
    "🗑 Restore to Factory State": "🗑 Restablecer a estado de fábrica",
    "Deletes ALL data: students, sessions, tasks, notes and settings. The app returns to its factory state.": "Elimina TODOS los datos: estudiantes, sesiones, tareas, notas y configuración. La aplicación vuelve a su estado de fábrica.",
    "This will delete ALL data:\n\n• Students, sessions and packages\n• Teacher tasks\n• Notes and settings\n\nThis cannot be undone. Continue?": "Esto eliminará TODOS los datos:\n\n• Estudiantes, sesiones y paquetes\n• Tareas del profesor\n• Notas y configuración\n\nEsta acción no se puede deshacer. ¿Continuar?",
    "The app has been restored to its factory state.\nAll data was deleted.": "La aplicación ha sido restablecida a su estado de fábrica.\nTodos los datos fueron eliminados.",
    "Welcome to Tutor Heaven": "Bienvenido a Tutor Heaven",
    "Do you want to enable automatic backups?\n\nYou will choose a folder OUTSIDE the app so your data survives an uninstall.": "¿Quieres activar las copias de seguridad automáticas?\n\nElegirás una carpeta FUERA de la aplicación para que tus datos sobrevivan a una desinstalación.",

    # ---------- Diálogo de hoja de vida ----------
    "Curriculum (Resume)": "Hoja de Vida",
    "General Information": "Información general",
    "Enrolled On": "Matriculado el",
    "About the Student": "Sobre el estudiante",
    "Write a short bio: background, goals, level, anything useful...": "Escribe una biografía breve: antecedentes, objetivos, nivel, lo que sea útil...",
    "Interests": "Intereses",
    "Interest": "Interés",
    "That interest is already added.": "Ese interés ya está añadido.",

    # ---------- Navegador de estudiantes ----------
    "Select a student\n\nto open the profile.": "Selecciona un estudiante\n\npara abrir su perfil.",

    # ---------- Matrículas ----------
    "➕ New Enrollment": "➕ Nueva Matrícula",
    "Next Class": "Próxima clase",
    "Student Summary": "Resumen del estudiante",

    # ---------- Dashboard ----------
    "Active Students": "Estudiantes activos",
    "Former Students": "Estudiantes antiguos",
    "With debt": "Con deuda",
    "Without debt": "Sin deuda",
    "Double-click a student to open their profile": "Haz doble clic en un estudiante para abrir su perfil",
    "Next: {0} {1}": "Próxima: {0} {1}",
    "No upcoming class": "Sin próxima clase",
    "hours left": "horas restantes",
}
