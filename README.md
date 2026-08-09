# TutorHeaven

Aplicación de escritorio (PySide6/Qt) para gestionar un negocio de tutoría académica.

## Funcionalidades

- Registro de estudiantes (individual, grupo o personalizado) con paquete de clases y precios.
- Seguimiento de clases compradas / tomadas, descuentos por volumen y total a pagar.
- Registro de sesiones por estudiante (fecha, horario, tema, estado) con validación de horario.
- Persistencia en `data/students.json`.

## Estructura

- `src/tutor_heaven/models/` — Modelos de datos (`Student`, `Session`).
- `src/tutor_heaven/data/` — Persistencia en JSON.
- `src/tutor_heaven/ui/` — Ventanas, pestañas y widgets de la interfaz.

## Ejecución

```bash
python -m tutor_heaven
```
