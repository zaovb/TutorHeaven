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
    "Calendar": "Calendario",
    "Students": "Estudiantes",
    "⚙ Settings": "⚙ Configuración",

    # ---------- Barra de título / botones de ventana ----------
    "Minimize": "Minimizar",
    "Maximize": "Maximizar",
    "Fullscreen": "Pantalla completa",
    "Close": "Cerrar",

    # ---------- Calendar ----------
    "Today": "Hoy",
    "➕ New student...": "➕ Nuevo estudiante...",
    "Students who studied this week": "Estudiantes que estudiaron esta semana",
    "Add Session": "Añadir Sesión",
    "Edit Session": "Editar Sesión",
    "Delete session": "Eliminar sesión",
    "Invalid Session": "Sesión no válida",
    "End time must be after start time.": "La hora de fin debe ser posterior a la de inicio.",

    # ---------- WeekGrid / menú de bloques ----------
    "➕ +15 minutes": "➕ +15 minutos",
    "➖ -15 minutes": "➖ -15 minutos",
    "✏️ Edit...": "✏️ Editar...",
    "💵 Mark as Paid": "💵 Marcar como pagada",
    "💵 Mark as Not Paid": "💵 Marcar como no pagada",
    "🗑 Delete": "🗑 Eliminar",

    # ---------- Diálogo de sesión ----------
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
    "Next Topics": "Próximos temas",
    "Overlapping Classes": "Clases que se solapan",
    "This class overlaps another class of {0}. Choose a different time.": "Esta clase se solapa con otra clase de {0}. Elige una hora diferente.",
    "Student": "Estudiante",
    "➕ Add Class": "➕ Añadir clase",

    # ---------- Diálogo de progreso de clase ----------
    "Class Progress": "Progreso de la Clase",
    "Class Information": "Información de la Clase",
    "Classes Available": "Clases disponibles",
    "Last Homework": "Tarea anterior",
    "Homework Done": "Tarea hecha",
    "Completed the homework": "Completó la tarea",
    "Today's Progress": "Progreso de hoy",
    "Conversation Topic": "Tema de conversación",
    "Grammar Learned": "Gramática aprendida",
    "Homework": "Tarea",
    "To Learn Next": "Por ver en la próxima",
    "Student Interests": "Intereses del estudiante",
    "Add an interest (hobby, topic...)": "Añadir un interés (afición, tema...)",
    "➕ Add Interest": "➕ Añadir interés",
    "Remove Selected": "Quitar seleccionado",

    # ---------- Perfil del estudiante ----------
    "📋 Resume": "📋 Hoja de Vida",
    "🎨 Color": "🎨 Color",
    "🗑 Delete": "🗑 Eliminar",
    "Enrollment": "Matrícula",
    "Sessions": "Sesiones",
    "Packages": "Paquetes",
    "Files": "Archivos",
    "Statistics": "Estadísticas",
    "Enrollment Information": "Información de la matrícula",
    "No upcoming scheduled class": "No hay clase próxima programada",
    "Next class: {0} {1}": "Próxima clase: {0} {1}",
    "classes available": "clases disponibles",
    "classes owed": "clases por pagar",
    "✅ Clase vista": "✅ Clase vista",
    "Mark a class as done: records progress and consumes one class from the package.": "Marca la clase como vista: registra el progreso y consume una clase del paquete.",
    "Calendar": "Calendario",
    "Click or drag on an empty slot to schedule a class; resize from the bottom edge; right-click a block for actions.": "Haz clic o arrastra sobre un hueco para programar una clase; redimensiona desde el borde inferior; clic derecho sobre un bloque para acciones.",
    "Delete student": "Eliminar estudiante",
    "Are you sure you want to delete {0}?\n\nAll their packages, sessions and payment data will be permanently removed. This action cannot be undone.": "¿Seguro que quieres eliminar a {0}?\n\nTodos sus paquetes, sesiones y datos de pago se eliminarán de forma permanente. Esta acción no se puede deshacer.",
    "0 ({0} owed)": "0 ({0} por pagar)",

    # ---------- Tabla de sesiones ----------
    "Date": "Fecha",
    "Start": "Inicio",
    "End": "Fin",
    "Topic": "Tema",
    "Status": "Estado",
    "Paid": "Pagado",
    "Not paid": "Sin pagar",
    "Notes": "Notas",
    "Session Detail": "Detalle de sesión",
    "Time": "Hora",
    "Yes": "Sí",
    "No": "No",
    "Homework Done": "Tarea hecha",
    "Delete the session {0} {1}?": "¿Eliminar la sesión {0} {1}?",
    "Delete the session of {0} on {1} at {2}?": "¿Eliminar la sesión de {0} el {1} a las {2}?",

    # ---------- Paquetes ----------
    "➕ Add Classes to Package": "➕ Añadir clases al paquete",
    "Package Summary": "Resumen del paquete",
    "Package History": "Historial de paquetes",
    "Current Package": "Paquete actual",
    "Previous Package {0}": "Paquete anterior {0}",
    "Classes Purchased": "Clases compradas",
    "Classes Taken": "Clases dadas",
    "Classes Left": "Clases restantes",
    "Classes Owed": "Clases por pagar",
    "Finished": "TERMINADO",
    "Date of Payment": "Fecha de pago",
    "Date of Start": "Fecha de inicio",
    "Discount": "Descuento",
    "Hourly Price": "Precio por hora",
    "Total": "Total",
    "Total Paid": "Total histórico pagado",
    "Debt": "Deuda",
    "Status": "Estado",
    "Active": "Activo",
    "Former": "Antiguo",
    "Pay in advance": "Pago por adelantado",
    "Pay later": "Paga después",
    "Pending": "Pendiente",
    "Package Total": "Total del paquete",
    "Amount Paid": "Cantidad pagada",
    "Amount Owed": "Cantidad pendiente",

    # ---------- Diálogo de paquete ----------
    "Add Classes to Package": "Añadir Clases al Paquete",
    "Edit Package": "Editar Paquete",
    "New Block": "Bloque nuevo",
    "Classes to Add": "Clases a añadir",
    "Classes Purchased": "Clases compradas",
    "Dates": "Fechas",
    "Payment": "Pago",
    "Mode": "Modo",
    "Payment Mode": "Modo de pago",
    "Payment Status": "Estado de pago",
    "Block Price": "Precio del bloque",
    "Summary": "Resumen",
    "Edit": "Editar",
    "✏️ Edit Package": "✏️ Editar Paquete",

    # ---------- Diálogo de estudiante ----------
    "New Student": "Nuevo Estudiante",
    "Basic Information": "Información básica",
    "Name": "Nombre",
    "Type": "Tipo",
    "Email": "Email",
    "Phone": "Teléfono",
    "Initial Package": "Paquete inicial",
    "Classes Purchased": "Clases compradas",
    "Hourly Price": "Precio por hora",
    "Package Price": "Precio del paquete",
    "Payment Mode": "Modo de pago",
    "Payment Status": "Estado de pago",
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
    "Ideas, reminders, anything...\n(here Enter inserts a new line)": "Ideas, recordatorios, lo que sea...\n(aquí Enter inserta una línea nueva)",
    "Language": "Idioma",
    "English": "Inglés",
    "Spanish": "Español",
    "Theme": "Tema",
    "Notes": "Notas",
    "Calendar Marks": "Marcas del calendario",
    "Marks": "Marcas",
    "Show class marks in calendar": "Mostrar marcas de clase en el calendario",
    "Marks Style": "Estilo de marcas",
    "Dots": "Puntos",
    "Text": "Texto",
    "Viewed": "Vista",
    "Not viewed": "No vista",

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
    "Classes Left": "Clases restantes",
    "Student Summary": "Resumen del estudiante",

    # ---------- Dashboard ----------
    "Active Students": "Estudiantes activos",
    "Former Students": "Estudiantes antiguos",
    "Double-click a student to open their profile": "Haz doble clic en un estudiante para abrir su perfil",
    "Next: {0} {1}": "Próxima: {0} {1}",
    "No upcoming class": "Sin próxima clase",
    "classes left": "clases restantes",

    # ---------- Días de la semana ----------
    "Mon": "Lun",
    "Tue": "Mar",
    "Wed": "Mié",
    "Thu": "Jue",
    "Fri": "Vie",
    "Sat": "Sáb",
    "Sun": "Dom",
}
