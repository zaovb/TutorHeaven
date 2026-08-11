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
    # Las propiedades classes_purchased / classes_taken suman estos
    # bloques, así que el historial es la única fuente de verdad.
    packages: list[Package] = field(default_factory=list)

    # Registro de pagos (abonos) recibidos. La suma de estos importes
    # es la cantidad efectivamente cobrada (ver amount_paid).
    payments: list[Payment] = field(default_factory=list)

    @property
    def classes_purchased(self) -> int:
        """Clases compradas en total (suma de todos los paquetes)."""
        return sum(
            package.classes_purchased
            for package in self.packages
        )

    @property
    def classes_taken(self) -> int:
        """Clases consumidas en total (suma de todos los paquetes)."""
        return sum(
            package.classes_taken
            for package in self.packages
        )

    @property
    def classes_left(self) -> int:
        """Clases que le quedan al estudiante por consumir.

        Puede ser negativo cuando se dieron más clases de las compradas;
        ese exceso es lo que el estudiante debe ("clases por pagar").
        """
        return self.classes_purchased - self.classes_taken

    @property
    def classes_owed(self) -> int:
        """Clases vistas sin pagar (por encima de las compradas)."""
        return max(
            0,
            self.classes_taken - self.classes_purchased,
        )

    @property
    def paid_classes(self) -> int:
        """Clases cubiertas por paquetes pagados.

        Cada paquete marcado como "Paid" paga por adelantado las clases
        que compra. Las sesiones que consumen esas clases se consideran
        pagadas automáticamente.
        """
        return sum(
            package.classes_purchased
            for package in self.packages
            if package.payment_status == "Paid"
        )

    @property
    def package_price(self) -> float:
        """Precio bruto de todos los paquetes sin aplicar descuentos."""
        return sum(
            package.classes_purchased * package.hourly_price
            for package in self.packages
        )

    @property
    def auto_discount_percent(self) -> int:
        """Descuento automático por volumen según las reglas de la
        configuración (ver Settings.discount_for_classes)."""
        return get_settings().discount_for_classes(
            self.classes_purchased
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
        compra) y añadiendo el valor de las clases vistas sin pagar
        (por encima de las compradas) a su precio por hora, sin
        descuento.
        """
        return (
            sum(
                package.total
                for package in self.packages
            )
            + self.classes_owed * self.hourly_price
        )

    @property
    def is_auto_former(self) -> bool:
        """True si el estudiante ha agotado sus clases por sí mismo.

        Solo depende de los datos: no le quedan clases por consumir y
        no tiene una sesión futura pendiente. La marca manual puede
        forzar este estado (is_former) aunque aquí dé falso.
        """
        return self.classes_left <= 0 and self.next_session is None

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
            paid_sessions = sum(
                1
                for session in self.sessions
                if session.paid
            )

            marked = paid_sessions * self.hourly_price

        return max(
            recorded,
            marked,
        )

    @property
    def amount_owed(self) -> float:
        """Cantidad que se debe por clases vistas no cubiertas.

        La deuda aparece cuando el estudiante ha visto más clases de
        las que quedan cubiertas por paquetes pagados: son las clases
        vistas sin pagar multiplicadas por el precio por hora.
        """
        return max(
            self.classes_taken - self.paid_classes,
            0,
        ) * self.hourly_price

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
        de paquetes pagados: las clases se consumen en orden
        cronológico (FIFO) y las primeras ``paid_classes`` están
        pagadas; las que las superan quedan "por pagar". Esto evita
        que un mismo paquete pague más clases de las compradas al
        añadir paquetes nuevos o marcar sesiones retroactivamente.

        En modo "Pay later" cada clase se paga por separado y decide
        el flag individual de la sesión.
        """
        if session.status == "Cancelled":
            return False

        paid_budget = self.paid_classes

        if paid_budget <= 0:
            return session.paid

        ordered = sorted(
            (
                s
                for s in self.sessions
                if s.status != "Cancelled"
            ),
            key=lambda s: s.start_datetime,
        )

        for index, other in enumerate(ordered):
            if other is session:
                return index < paid_budget

        return False

    def mark_sessions_paid(self, classes: int) -> None:
        """Marca como pagadas las sesiones que cubre un paquete pagado.

        Al añadir (o marcar como pagado) un paquete, las clases que ya
        se habían visto sin pagar pasan a pagarse automáticamente: se
        recorren las sesiones sin pagar de más antigua a más reciente
        hasta cubrir las clases del paquete.
        """
        remaining = classes

        for session in self.sessions:
            if remaining <= 0:
                break

            if session.status != "Cancelled" and not session.paid:
                session.paid = True

                remaining -= 1

    def session_paid_default(self) -> bool:
        """Indica si una clase recién creada se considera pagada.

        La clase se paga según el paquete que va a cubrirla: el más
        antiguo del historial que aún tenga clases sin consumir (FIFO).

        - "Pay in advance" y paquete pagado: la clase nace pagada.
        - "Pay later": cada clase se paga después, nace sin pagar.
        - Sin clases disponibles (ningún paquete que la cubra): nace
          sin pagar.
        """
        if self.paid_classes <= 0:
            return False

        consumed = sum(
            1
            for s in self.sessions
            if s.status != "Cancelled"
        )

        return consumed < self.paid_classes

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

    def consume_class(self) -> None:
        """Consume una clase del paquete más antiguo que aún tenga.

        Cuando se da una clase como vista se resta una clase del primer
        paquete del historial que todavía tenga clases sin consumir. Si
        ningún paquete tiene clases disponibles, la clase se registra
        igualmente sobre el paquete más reciente: queda como una clase
        por pagar (classes_left negativo).
        """
        for package in self.packages:
            if package.classes_left > 0:
                package.classes_taken += 1

                return

        if self.packages:
            self.packages[-1].classes_taken += 1

    def release_class(self) -> None:
        """Libera una clase consumida (deshacer consume_class).

        Se usa al desmarcar una clase como vista:
        devuelve una clase al primer paquete del historial que tenga
        clases tomadas. Los totales (classes_taken) siempre quedan
        coherentes.
        """
        for package in self.packages:
            if package.classes_taken > 0:
                package.classes_taken -= 1

                return

    def add_package(
        self,
        classes: int,
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

        Si venía arrastrando deuda (clases tomadas por encima de lo
        comprado en paquetes anteriores), el nuevo bloque absorbe esa
        deuda primero: las clases en exceso se mueven del paquete que
        las registró al nuevo, de modo que ningún paquete antiguo
        muestre "clases por pagar" si el nuevo ya las cubre.
        """
        new_package = Package(
            classes_purchased=classes,
            classes_taken=0,
            hourly_price=hourly_price,
            discount_percent=discount_percent,
            payment_mode=payment_mode,
            payment_status=payment_status,
            date_of_payment=date_of_payment,
            date_of_start=date_of_start,
        )

        self.packages.append(new_package)

        # Redistribuye la deuda acumulada hacia el paquete nuevo: por
        # cada paquete anterior con más clases tomadas que compradas,
        # el exceso pasa a contabilizarse en el nuevo bloque (hasta
        # llenarlo). Los totales quedan intactos.
        for package in self.packages[:-1]:
            if package.classes_taken <= package.classes_purchased:
                continue

            excess = package.classes_taken - package.classes_purchased
            room = (
                new_package.classes_purchased
                - new_package.classes_taken
            )

            if room <= 0:
                break

            move = min(excess, room)

            package.classes_taken -= move
            new_package.classes_taken += move

        self.hourly_price = hourly_price
        self.payment_mode = payment_mode
        self.payment_status = payment_status
