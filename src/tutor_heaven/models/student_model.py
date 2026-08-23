from dataclasses import dataclass, field
from datetime import datetime

from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.models.package_model import Package
from tutor_heaven.models.payment_model import Payment
from tutor_heaven.models.session_model import Session


@dataclass(slots=True)
class Student:
    """Represents a student.

    Modelo de datos de un estudiante. Es una dataclass con slots
    (menos memoria y acceso más rápido). Contiene la información
    de la matrícula, la lista de sesiones y el historial de paquetes
    comprados (packages), que es la única fuente de verdad para las
    clases compradas y consumidas.
    """

    name: str
    student_type: str

    email: str
    phone: str

    # Precio por hora actual (el del último paquete comprado).
    hourly_price: float

    # Modo y estado de pago actuales (los del último paquete).
    payment_mode: str
    payment_status: str

    notes: str

    sessions: list[Session] = field(default_factory=list)

    # Sesiones eliminadas (papelera). Se mueven aquí al eliminarlas y
    # solo se ven desde el portal de "Sesiones eliminadas" del perfil,
    # donde se pueden restaurar o borrar definitivamente.
    deleted_sessions: list[Session] = field(default_factory=list)

    # Fecha de ingreso/alta del estudiante. Por defecto, el momento
    # en que se crea el objeto.
    enrolled_at: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # Intereses acumulados del estudiante (hobbies, temas de
    # conversación, gustos). Se van añadiendo sesión a sesión.
    interests: list[str] = field(default_factory=list)

    # Nivel del estudiante según el Marco Común Europeo de Referencia
    # (A1, A2, B1, B2, C1, C2). Es información de contexto para el
    # tutor y el alumno: no afecta a precios ni a cálculos de pago.
    level: str = ""

    # Temas gramaticales vistos hasta ahora. Información pedagógica de
    # referencia; no interviene en ningún cálculo económico.
    topics: list[str] = field(default_factory=list)

    # Hoja de vida del estudiante: breve descripción, datos
    # personales relevantes o cualquier información útil para el tutor.
    bio: str = ""

    # Marca manual para tratar al estudiante como "antiguo" aunque aún
    # le queden clases por consumir. Por defecto falso: el estado se
    # deduce automáticamente de los datos (ver is_former).
    marked_former: bool = False

    # Marca manual para tratar al estudiante como "activo" aunque haya
    # agotado sus clases (la deducción automática diría "antiguo").
    # Tiene prioridad sobre marked_former y sobre is_auto_former, así
    # el botón "Unmark as former" del perfil puede devolver a la lista
    # de activos a quien se agotó por datos pero sigue en activo.
    force_active: bool = False

    # Historial de paquetes comprados, del más antiguo al más nuevo.
    # Las propiedades hours_purchased / hours_taken suman estos
    # bloques, así que el historial es la única fuente de verdad.
    packages: list[Package] = field(default_factory=list)

    # Registro de pagos (abonos) recibidos. La suma de estos importes
    # es la cantidad efectivamente cobrada (ver amount_paid).
    payments: list[Payment] = field(default_factory=list)

    @property
    def hours_purchased(self) -> float:
        """Horas compradas en total (suma de todos los paquetes)."""
        return sum(
            package.hours_purchased
            for package in self.packages
        )

    @property
    def minutes_taken(self) -> int:
        """Minutos consumidos en total (suma de todos los paquetes).

        El consumo se lleva en minutos enteros para que clases de
        media hora o de hora y media nunca generen decimales raros.
        """
        return sum(
            package.minutes_taken
            for package in self.packages
        )

    @property
    def hours_taken(self) -> float:
        """Horas consumidas en total (suma de todos los paquetes)."""
        return self.minutes_taken / 60

    @property
    def hours_left(self) -> float:
        """Horas que le quedan al estudiante por consumir.

        Puede ser negativo cuando se dieron más horas de las
        compradas; ese exceso es lo que el estudiante debe ("horas
        por pagar").
        """
        return self.hours_purchased - self.hours_taken

    @property
    def hours_owed(self) -> float:
        """Horas vistas sin pagar (por encima de las compradas)."""
        return max(
            0.0,
            self.minutes_taken - self.capacity_minutes,
        ) / 60

    @property
    def capacity_minutes(self) -> int:
        """Capacidad total en minutos de todos los paquetes."""
        return sum(
            package.capacity_minutes
            for package in self.packages
        )

    @property
    def paid_minutes(self) -> int:
        """Minutos cubiertos por paquetes pagados.

        Cada paquete marcado como "Paid" paga por adelantado las horas
        que compra. Las sesiones que consumen esas horas se consideran
        pagadas automáticamente.
        """
        return sum(
            package.capacity_minutes
            for package in self.packages
            if package.payment_status == "Paid"
        )

    @property
    def paid_hours(self) -> float:
        """Horas cubiertas por paquetes pagados."""
        return self.paid_minutes / 60

    @property
    def package_price(self) -> float:
        """Precio bruto de todos los paquetes sin aplicar descuentos."""
        return sum(
            package.hours_purchased * package.hourly_price
            for package in self.packages
        )

    @property
    def auto_discount_percent(self) -> int:
        """Descuento automático por volumen según las reglas de la
        configuración (ver Settings.discount_for_hours)."""
        return get_settings().discount_for_hours(
            self.hours_purchased
        )

    @property
    def discount_percent(self) -> int:
        """Descuento aplicado: siempre el automático por reglas."""
        return self.auto_discount_percent

    @property
    def total(self) -> float:
        """Precio final a pagar por todos los paquetes tras descuentos.

        Se calcula sumando cada paquete con su propio precio y su
        propio descuento (el histórico refleja lo negociado en cada
        compra) y añadiendo el valor de las horas vistas sin pagar
        (por encima de las compradas) a su precio por hora, sin
        descuento.
        """
        return (
            sum(
                package.total
                for package in self.packages
            )
            + self.hours_owed * self.hourly_price
        )

    @property
    def is_auto_former(self) -> bool:
        """True si el estudiante ha agotado sus clases por sí mismo.

        Solo depende de los datos: no le quedan clases por consumir y
        no tiene una sesión futura pendiente. La marca manual puede
        forzar este estado (is_former) aunque aquí dé falso.
        """
        return self.hours_left <= 0 and self.next_session is None

    @property
    def is_active(self) -> bool:
        """True si es un estudiante actual (no marcado como antiguo).

        Un estudiante es antiguo si se marcó manualmente o si agotó sus
        clases sin tener una sesión futura pendiente. La marca manual
        tiene prioridad: permite tratar como antiguo a alguien con
        clases por ver, o como activo a alguien que ya las agotó.
        """
        return not self.is_former

    @property
    def is_former(self) -> bool:
        """True si es un estudiante antiguo.

        Es antiguo si (a) se marcó manualmente como antiguo en su
        perfil (marked_former) o (b) agotó sus clases y no tiene
        sesiones pendientes a futuro. La marca force_active tiene la
        máxima prioridad: trata como activo a quien la deducción
        automática daría por antiguo (ver force_active).
        """
        if self.force_active:
            return False

        return self.marked_former or self.is_auto_former

    @property
    def amount_paid(self) -> float:
        """Cantidad efectivamente pagada.

        Se toma la mayor de dos vistas:
        - La suma de los pagos registrados (payments), usada sobre
          todo para abonos parciales.
        - La derivada de las marcas: paquetes "Paid" en modo "Pay in
          advance", o clases pagadas individualmente en "Pay later".

        Usar el máximo evita doble conteo cuando el tutor marca pagos
        y además registra abonos, y mantiene coherentes los datos ya
        guardados que no tienen registros.
        """
        recorded = sum(
            payment.amount
            for payment in self.payments
        )

        if self.payment_mode == "Pay in advance":
            marked = sum(
                package.total
                for package in self.packages
                if package.payment_status == "Paid"
            )
        else:
            # En "Pay later" cada clase pagada individualmente aporta
            # su propia duración (las clases pueden durar media hora,
            # una hora o lo que se haya dado).
            marked = (
                sum(
                    session.duration_minutes()
                    for session in self.sessions
                    if session.paid
                )
                / 60
                * self.hourly_price
            )

        return max(
            recorded,
            marked,
        )

    @property
    def amount_owed(self) -> float:
        """Cantidad que se debe por horas vistas no cubiertas.

        La deuda aparece cuando el estudiante ha visto más horas de
        las que quedan cubiertas por paquetes pagados: son las horas
        vistas sin pagar multiplicadas por el precio por hora.
        """
        return max(
            self.minutes_taken - self.paid_minutes,
            0,
        ) / 60 * self.hourly_price

    @property
    def has_debt(self) -> bool:
        """True si el estudiante debe dinero por clases sin pagar."""
        return self.amount_owed > 0

    @property
    def total_paid(self) -> float:
        """Total histórico pagado: suma de todas las transacciones.

        Suma los paquetes pagados (con su descuento) y los abonos
        registrados: todo el dinero efectivamente recibido del alumno.
        """
        return (
            sum(
                package.total
                for package in self.packages
                if package.payment_status == "Paid"
            )
            + sum(
                payment.amount
                for payment in self.payments
            )
        )

    def session_is_paid(self, session: Session) -> bool:
        """True si la clase está cubierta por un paquete pagado.

        En modo "Pay in advance" el estado se deriva del presupuesto
        de paquetes pagados: las sesiones se recorren en orden
        cronológico (FIFO) acumulando su duración y una clase está
        pagada cuando cabe entera dentro del presupuesto; la que lo
        desborda (o llega parcialmente cubierta) queda "por pagar".
        Con clases de 1 hora esta regla coincide con el conteo por
        clases anterior; con duraciones mixtas reparte el presupuesto
        sin pagar de más.

        En modo "Pay later" cada clase se paga por separado y decide
        el flag individual de la sesión.
        """
        if session.status == "Cancelled":
            return False

        paid_budget = self.paid_minutes

        if paid_budget <= 0:
            return session.paid

        consumed = 0

        for other in sorted(
            (
                s
                for s in self.sessions
                if s.status != "Cancelled"
            ),
            key=lambda s: s.start_datetime,
        ):
            consumed += other.duration_minutes()

            if other is session:
                return consumed <= paid_budget

        return False

    def mark_sessions_paid(self, hours: float) -> None:
        """Marca como pagadas las sesiones que cubre un paquete pagado.

        Al añadir (o marcar como pagado) un paquete, las clases que ya
        se habían visto sin pagar pasan a pagarse automáticamente: se
        recorren las sesiones sin pagar de más antigua a más reciente
        hasta agotar las horas del paquete.
        """
        remaining = round(hours * 60)

        for session in self.sessions:
            if remaining <= 0:
                break

            if session.status != "Cancelled" and not session.paid:
                session.paid = True

                remaining -= session.duration_minutes()

    def session_paid_default(
        self,
        additional_minutes: int = 0,
    ) -> bool:
        """Indica si una clase recién creada se considera pagada.

        La clase se paga según el paquete que va a cubrirla: el más
        antiguo del historial que aún tenga horas sin consumir (FIFO).

        - "Pay in advance" y paquete pagado con presupuesto libre: la
          clase nace pagada.
        - "Pay later": cada clase se paga después, nace sin pagar.
        - Sin horas disponibles (ningún paquete que la cubra): nace
          sin pagar.

        ``additional_minutes`` permite pasar la duración de la clase
        nueva antes de añadirla a la lista: entonces solo nace pagada
        si el presupuesto la cubre entera. Sin duración conocida,
        basta con que quede algo de presupuesto sin consumir.
        """
        paid_budget = self.paid_minutes

        if paid_budget <= 0:
            return False

        consumed = sum(
            s.duration_minutes()
            for s in self.sessions
            if s.status != "Cancelled"
        )

        if additional_minutes > 0:
            return (
                consumed + additional_minutes
                <= paid_budget
            )

        return consumed < paid_budget

    def overlaps_other_sessions(self, session) -> bool:
        """True si la sesión dada coincide en el tiempo con otra suya.

        Dos sesiones solapan si el inicio de una es anterior al fin de
        la otra y viceversa. La propia sesión se excluye del chequeo.
        """
        start = session.start_datetime
        end = session.end_datetime

        for other in self.sessions:
            if other is session:
                continue

            other_start = other.start_datetime
            other_end = other.end_datetime

            if start < other_end and other_start < end:
                return True

        return False

    @property
    def next_session(self) -> Session | None:
        """Próxima sesión pendiente en el tiempo, o None si no hay.

        Filtra las sesiones con estado "Pending" cuya fecha aún no
        ha pasado y devuelve la más cercana (la de menor datetime).
        """
        pending = [
            session
            for session in self.sessions
            if session.start_datetime >= datetime.now()
            and session.status == "Pending"
        ]

        if not pending:
            return None

        return min(
            pending,
            key=lambda session: session.start_datetime,
        )

    def consume_time(self, minutes: int) -> None:
        """Consume minutos del paquete más antiguo que aún tenga.

        Cuando se da una clase como vista se restan sus minutos del
        primer paquete del historial que todavía tenga horas sin
        consumir (llenándolo del todo antes de pasar al siguiente).
        Si ningún paquete tiene horas disponibles, el consumo se
        registra igualmente sobre el paquete más reciente: queda como
        horas por pagar (hours_left negativo).
        """
        remaining = max(0, round(minutes))

        for package in self.packages:
            if remaining <= 0:
                break

            room = package.minutes_left

            if room > 0:
                take = min(room, remaining)

                package.minutes_taken += take
                remaining -= take

        if remaining > 0 and self.packages:
            self.packages[-1].minutes_taken += remaining

    def release_time(self, minutes: int) -> None:
        """Libera minutos consumidos (deshacer consume_time).

        Se usa al desmarcar una clase como vista o al editar una
        sesión ya completada: devuelve los minutos en orden inverso
        (del paquete más nuevo al más antiguo), sin bajar nunca de
        cero en cada bloque. Los totales (minutes_taken) siempre
        quedan coherentes.
        """
        remaining = max(0, round(minutes))

        for package in reversed(self.packages):
            if remaining <= 0:
                break

            give_back = min(
                package.minutes_taken,
                remaining,
            )

            package.minutes_taken -= give_back
            remaining -= give_back

    def delete_session(self, session: Session) -> None:
        """Mueve una sesión a la papelera (eliminación no definitiva).

        Si la sesión estaba completada (consumió horas del paquete)
        se libera su duración, de modo que los conteos quedan
        coherentes con las sesiones visibles.
        """
        if session in self.sessions:
            self.sessions.remove(session)

        if session not in self.deleted_sessions:
            self.deleted_sessions.append(session)

        if session.status == "Completed":
            self.release_time(session.duration_minutes())

    def restore_session(self, session: Session) -> None:
        """Devuelve una sesión de la papelera a la lista activa.

        Si la sesión estaba completada se vuelve a consumir la
        duración que liberó al eliminarla.
        """
        if session in self.deleted_sessions:
            self.deleted_sessions.remove(session)

        if session not in self.sessions:
            self.sessions.append(session)

        if session.status == "Completed":
            self.consume_time(session.duration_minutes())

        self.sort_sessions()

    def purge_session(self, session: Session) -> None:
        """Elimina definitivamente una sesión de la papelera.

        La sesión ya no está en la lista activa (delete_session la movió
        a la papelera); esto la borra sin opción de recuperarla.
        """
        if session in self.deleted_sessions:
            self.deleted_sessions.remove(session)

    def sort_sessions(self) -> None:
        """Ordena las sesiones activas por fecha de inicio."""
        self.sessions.sort(
            key=lambda session: session.start_datetime
        )

    def add_package(
        self,
        hours: float,
        hourly_price: float,
        discount_percent: int,
        payment_mode: str,
        payment_status: str,
        date_of_payment: str,
        date_of_start: str,
    ) -> None:
        """Añade un nuevo paquete comprado y actualiza los datos actuales.

        El nuevo paquete pasa a ser el "current" del estudiante, así
        que también actualiza el precio por hora y el modo de pago
        vigentes.

        Si venía arrastrando deuda (minutos tomados por encima de lo
        comprado en paquetes anteriores), el nuevo bloque absorbe esa
        deuda primero: los minutos en exceso se mueven del paquete que
        los registró al nuevo, de modo que ningún paquete antiguo
        muestre "horas por pagar" si el nuevo ya las cubre.
        """
        new_package = Package(
            hours_purchased=hours,
            minutes_taken=0,
            hourly_price=hourly_price,
            discount_percent=discount_percent,
            payment_mode=payment_mode,
            payment_status=payment_status,
            date_of_payment=date_of_payment,
            date_of_start=date_of_start,
        )

        self.packages.append(new_package)

        # Redistribuye la deuda acumulada hacia el paquete nuevo: por
        # cada paquete anterior con más minutos tomados que comprados,
        # el exceso pasa a contabilizarse en el nuevo bloque (hasta
        # llenarlo). Los totales quedan intactos.
        for package in self.packages[:-1]:
            if package.minutes_taken <= package.capacity_minutes:
                continue

            excess = (
                package.minutes_taken
                - package.capacity_minutes
            )

            room = (
                new_package.capacity_minutes
                - new_package.minutes_taken
            )

            if room <= 0:
                break

            move = min(excess, room)

            package.minutes_taken -= move
            new_package.minutes_taken += move

        self.hourly_price = hourly_price
        self.payment_mode = payment_mode
        self.payment_status = payment_status
