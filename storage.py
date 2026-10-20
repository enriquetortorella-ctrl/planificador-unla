"""Conservative Google Sheets writes. Does not create a real connection."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from threading import RLock

import pandas as pd

_WRITE_LOCK = RLock()  # Serializes sessions in this Python process only.
REQUIRED = {"Nombre", "Materia", "Estado"}
NUMERIC = {"Nota", "Nota_parcial1", "Nota_parcial2", "Aplazos"}


class SaveError(RuntimeError):
    """No confirmed success; callers must keep the editor and avoid celebrations."""


@dataclass(frozen=True)
class SaveResult:
    backup_confirmed: bool


def normalizar_tabla(df):
    if not isinstance(df, pd.DataFrame):
        raise SaveError("La planilla no devolvió una tabla válida. No se guardó.")
    result = df.copy()
    result.columns = [str(c).strip().capitalize() for c in result.columns]
    if result.columns.duplicated().any() or not REQUIRED.issubset(result.columns):
        raise SaveError("La planilla no tiene las columnas esperadas. No se guardó.")
    return result


def _cell(value, column):
    text = "" if pd.isna(value) else str(value).strip()
    if column == "Estado":
        return text.capitalize()
    if column == "Cursada":
        return text or "Regular"
    if column in NUMERIC and text:
        try:
            return str(Decimal(text).normalize())
        except InvalidOperation:
            pass
    return text


def mismas_filas(left, right):
    columns = sorted(set(left.columns) | set(right.columns))
    def records(frame):
        aligned = frame.reindex(columns=columns, fill_value="")
        return sorted(tuple(_cell(row[c], c) for c in columns) for _, row in aligned.iterrows())
    return records(left) == records(right)


def guardar_usuario(conn, local, usuario, base):
    """Read, detect stale user data, preserve others, write once and verify.

    Sheets has no atomic compare-and-swap: separate processes/external editors can
    still race between the read and write. Never silently retry an uncertain write.
    """
    if not usuario or base is None:
        raise SaveError("Falta la referencia de la sesión. Recargá antes de guardar.")
    local, base = normalizar_tabla(local), normalizar_tabla(base)
    with _WRITE_LOCK:
        try:
            remote = normalizar_tabla(conn.read(worksheet=0, ttl=0))
        except Exception as exc:
            raise SaveError("No pude leer la planilla actual. No se escribió ningún cambio; intentá recargar.") from exc

        expected = base[base["Nombre"] == usuario]
        current = remote[remote["Nombre"] == usuario]
        if not mismas_filas(expected, current):
            raise SaveError("Tus datos cambiaron en otra sesión. No se guardó: recargá y revisá los cambios.")
        mine = local[local["Nombre"] == usuario]
        target = pd.concat([remote[remote["Nombre"] != usuario], mine], ignore_index=True).fillna("")

        # Refuse a new/destructive schema change before any remote write.
        if not set(remote.columns).issubset(target.columns):
            raise SaveError("Cambió la estructura de la planilla. Recargá antes de guardar.")
        backup_ok = True
        try:
            conn.update(worksheet="backup", data=remote)
        except Exception:
            backup_ok = False

        try:
            conn.update(worksheet=0, data=target)
        except Exception as exc:
            # A timeout can happen AFTER the server accepted the write.
            raise SaveError("No pude confirmar la escritura. Puede haberse aplicado: recargá antes de volver a guardar.") from exc
        try:
            saved = normalizar_tabla(conn.read(worksheet=0, ttl=0))
        except Exception as exc:
            raise SaveError("La escritura fue enviada, pero no pude verificarla. Recargá antes de repetirla.") from exc
        if not mismas_filas(saved, target):
            raise SaveError("La verificación no coincide con lo enviado. Recargá y revisá la planilla antes de reintentar.")
        return SaveResult(backup_confirmed=backup_ok)
