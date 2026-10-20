"""Rules shared by the list, graph and summaries; no network or UI effects."""
import unicodedata

import pandas as pd


def materia_id(nombre):
    value = unicodedata.normalize("NFKD", str(nombre).strip().lower())
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())


def nombre_canonico(nombre, plan):
    return next((m for m in plan if materia_id(m) == materia_id(nombre)), str(nombre))


def mascara_materia(df, usuario, materia):
    return (df["Nombre"] == usuario) & (df["Materia"].map(materia_id) == materia_id(materia))


def estados_por_materia(datos):
    # In an inconsistent legacy sheet prefer the most advanced valid state.
    priority = {"Cursando": 1, "Final": 2, "Aprobada": 3}
    result = {}
    for _, row in datos.iterrows():
        mid, state = materia_id(row["Materia"]), row["Estado"]
        if priority.get(state, 0) > priority.get(result.get(mid), 0):
            result[mid] = state
    return result


def estado_materia(materia, plan, estados):
    registered = estados.get(materia_id(materia))
    if registered:
        return registered
    missing = requisitos_pendientes(materia, plan, estados)
    return "Bloqueada" if missing else "Disponible"


def requisitos_pendientes(materia, plan, estados):
    # Preserve the existing academic rule: regularity OR approval enables cursar.
    return [m for m in plan[materia]["correlativas"]
            if estados.get(materia_id(m)) not in {"Final", "Aprobada"}]


def entorno_materia(materia, plan):
    """Focused graph: selected subject, immediate requirements and dependents."""
    if not materia:
        return set(plan)
    return ({materia} | set(plan[materia]["correlativas"]) |
            {m for m, info in plan.items() if materia in info["correlativas"]})


def vista_academica(datos, plan):
    """Canonical names/deduplicated metrics, without rewriting legacy storage."""
    view = datos.copy()
    view["Materia"] = view["Materia"].map(lambda m: nombre_canonico(m, plan))
    view = view[view["Materia"].isin(plan) & view["Estado"].isin({"Cursando", "Final", "Aprobada"})].copy()
    view["_priority"] = view["Estado"].map({"Cursando": 1, "Final": 2, "Aprobada": 3}).fillna(0)
    view = view.sort_values("_priority", kind="stable").drop_duplicates("Materia", keep="last")
    return view.drop(columns="_priority")


def fecha_existente(value, fallback=None):
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.date() if pd.notna(parsed) else fallback
