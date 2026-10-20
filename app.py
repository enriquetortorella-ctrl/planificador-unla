import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
import os
import base64
from pathlib import Path
from graph_view import graph_html
from html import escape
from career_logic import (materia_id, mascara_materia, estados_por_materia, estado_materia,
                          requisitos_pendientes, vista_academica, fecha_existente)
from storage import guardar_usuario, normalizar_tabla, SaveError
from datetime import date, datetime, timedelta

ANCHO_COMPLETO = {"width": "stretch"} if hasattr(st, "iframe") else {"use_container_width": True}


def mostrar_html(content: str, height: int, scrolling: bool = False):
    """Use the supported embed API, retaining older Streamlit compatibility."""
    if hasattr(st, "iframe"):
        st.iframe(content, height=height, alt="Panel arcade interactivo")
    else:
        st.components.v1.html(content, height=height, scrolling=scrolling)

# ─────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(page_title="Círculo Rojo - SQUAD", page_icon="🔫", layout="wide")

_font_path = Path(__file__).parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"
if _font_path.exists():
    _font_b64 = base64.b64encode(_font_path.read_bytes()).decode("ascii")
    st.markdown("<style>@font-face{font-family:'Press Start 2P';font-style:normal;font-weight:400;"
                "font-display:swap;src:url(data:font/ttf;base64," + _font_b64 + ") format('truetype');}</style>",
                unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Font embedded from assets/fonts below; no Google Fonts request. */

    .stApp { background-color: #0b0d11; color: #e0e0e0; }

    /* ── EFECTO CRT: scanlines + viñeta de monitor arcade ── */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            repeating-linear-gradient(
                0deg,
                rgba(0,0,0,0.18),
                rgba(0,0,0,0.18) 1px,
                rgba(0,0,0,0.00) 1px,
                rgba(0,0,0,0.00) 3px
            ),
            radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.35) 100%);
        pointer-events: none;
        z-index: 9990;
        opacity: 0.24;
        mix-blend-mode: multiply;
    }

    .retro-font {
        font-family: 'Press Start 2P', cursive;
        color: #f1c40f;
        text-shadow: 2px 2px #000;
    }
    .hp-bar-text {
        font-family: 'Press Start 2P', cursive;
        font-size:13px;
        color: #ff4b4b;
        margin-top: 5px;
    }
    .hp-bar-text-blue {
        font-family: 'Press Start 2P', cursive;
        font-size:13px;
        color: #3498db;
        margin-top: 5px;
    }
    .cuatri-header {
        font-family: 'Press Start 2P', cursive;
        color: #3498db;
        font-size:16px;
        margin-top: 30px;
        padding: 10px;
        border-bottom: 2px solid #3498db;
    }
    .materia-card {
        background-color: #1a1c23;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #f1c40f;
    }
    .warning-card {
        background-color: #1a1200;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #ff4b4b;
    }
    .exam-card {
        background-color: #0d1a2e;
        border-radius: 5px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #3498db;
    }
    .exam-urgent {
        border-left: 4px solid #ff4b4b !important;
        background-color: #1a0d0d !important;
    }
    .logro-card {
        background: #1a1c23;
        border-radius: 8px;
        padding: 12px 10px;
        text-align: center;
        border: 1px solid #333;
        height: 100%;
    }
    .logro-on {
        border: 1px solid #f1c40f;
        box-shadow: 0 0 10px #f1c40f44;
    }
    .logro-off { filter: grayscale(1); opacity: 0.78; }
    [data-testid="stMetricValue"] {
        font-family: 'Press Start 2P', cursive;
        font-size:18px !important;
    }

    /* Arcade headings, readable body text and touch controls. */
    .stApp p, .stApp li { line-height: 1.6; }
    .stButton > button { min-height: 44px; font-size:14px; }
    .stButton > button:focus-visible { outline: 3px solid #f1c40f; outline-offset: 3px; }
    [data-testid="stCaptionContainer"] { color: #b9c1ce; }
    @media (max-width: 640px) {
        .retro-font { font-size:16px !important; line-height: 1.7; }
        .hp-bar-text, .hp-bar-text-blue { font-family: monospace; font-size:13px !important; }
        [data-testid="stMetricValue"] { font-size:16px !important; }
    }
    .arcade-signal { border-left: 4px solid #f1c40f; padding: 10px 14px; background: #1e1b0e;
        font-family: monospace; color: #f8e68b; animation: signal 1s ease-out 1; }
    @keyframes signal { from { box-shadow: 0 0 24px #f1c40f77; } to { box-shadow: none; } }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation: none !important; transition: none !important; }
        .stApp::before { display: none; }
        [data-testid="stImage"] img { display: none; }
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 2. PLAN DE ESTUDIOS CON CRÉDITOS
# ─────────────────────────────────────────────
PLAN_ESTUDIOS = {
    # ── 1er año ──────────────────────────────────────────────────────────
    "Introducción a Economía Empresarial":               {"periodo": "Anual",    "puntos": 4,  "correlativas": []},
    "Historia Económica Contemporánea":                  {"periodo": "1° Cuat.", "puntos": 5,  "correlativas": ["Introducción a Economía Empresarial"]},
    "Contabilidad":                                      {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Introducción a Economía Empresarial"]},
    "Matemática I":                                      {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Introducción a Economía Empresarial"]},
    "Taller de Comunicación y Producción de Textos":     {"periodo": "1° Cuat.", "puntos": 5,  "correlativas": []},
    "Empresa, Economía y Sociedad":                      {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Historia Económica Contemporánea"]},
    "Organización y Gestión":                            {"periodo": "2° Cuat.", "puntos": 7,  "correlativas": ["Matemática I"]},
    "Matemática II":                                     {"periodo": "2° Cuat.", "puntos": 8,  "correlativas": ["Matemática I"]},
    "Derecho Comercial":                                 {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Historia Económica Contemporánea"]},
    "Seminario de Justicia y Derechos Humanos":          {"periodo": "2° Cuat.", "puntos": 3,  "correlativas": []},
    # ── 2do año ──────────────────────────────────────────────────────────
    "Microeconomía I":                                   {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Matemática I"]},
    "Cálculo Financiero":                                {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Matemática II"]},
    "Comercialización":                                  {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Taller de Comunicación y Producción de Textos", "Organización y Gestión"]},
    "Costos Empresariales":                              {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Contabilidad", "Matemática II"]},
    "Seminario de Pensamiento Nacional Latinoamericano": {"periodo": "1° Cuat.", "puntos": 3,  "correlativas": []},
    "Control de Gestión":                                {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Derecho Comercial", "Costos Empresariales"]},
    "Estadística":                                       {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Cálculo Financiero"]},
    "Microeconomía II":                                  {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Microeconomía I"]},
    "Macroeconomía":                                     {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Empresa, Economía y Sociedad", "Microeconomía I"]},
    "Taller de Práctica Preprofesional":                 {"periodo": "2° Cuat.", "puntos": 5,  "correlativas": ["Comercialización", "Costos Empresariales"]},
    # ── 3er año (Licenciatura) ───────────────────────────────────────────
    "Plan de Negocios":                                  {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Costos Empresariales"]},
    "Organización de la Producción y la Tecnología":     {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Control de Gestión"]},
    "Formulación de Proyectos de Inversión":             {"periodo": "1° Cuat.", "puntos": 7,  "correlativas": ["Estadística"]},
    "Economía Bancaria y Financiera":                    {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Microeconomía II", "Macroeconomía"]},
    "Evaluación de Proyectos de Inversión":              {"periodo": "2° Cuat.", "puntos": 7,  "correlativas": ["Formulación de Proyectos de Inversión"]},
    "Relaciones Laborales":                              {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Organización de la Producción y la Tecnología"]},
    "Sistemas de Organización":                          {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Organización de la Producción y la Tecnología"]},
    "Principios de Tributación":                         {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Derecho Comercial", "Control de Gestión"]},
    # ── 4to año (Licenciatura) ───────────────────────────────────────────
    "Financiamiento":                                    {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Economía Bancaria y Financiera"]},
    "Tecnología y Ciencia de Datos":                     {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Sistemas de Organización"]},
    "Taller de Proyecto Empresarial":                    {"periodo": "Anual",    "puntos": 11, "correlativas": ["Plan de Negocios", "Evaluación de Proyectos de Inversión"]},
    "Planeamiento Estratégico":                          {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Sistemas de Organización"]},
    "Política Económica":                                {"periodo": "2° Cuat.", "puntos": 5,  "correlativas": ["Economía Bancaria y Financiera"]},
    "Inteligencia de Negocios":                          {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Tecnología y Ciencia de Datos"]},
    "Comercio Exterior":                                 {"periodo": "2° Cuat.", "puntos": 5,  "correlativas": ["Planeamiento Estratégico"]},
    "Inglés I":                                          {"periodo": "2° Cuat.", "puntos": 5,  "correlativas": []},
    # ── Seminarios optativos (oficialmente: requieren toda la Tecnicatura
    #    aprobada; se modela con la materia de cierre como correlativa) ────
    "Seminario Optativo 1":                              {"periodo": "1° Cuat.", "puntos": 4,  "correlativas": ["Taller de Práctica Preprofesional"]},
    "Seminario Optativo 2":                              {"periodo": "2° Cuat.", "puntos": 4,  "correlativas": ["Taller de Práctica Preprofesional"]},
    "Seminario Optativo 3":                              {"periodo": "1° Cuat.", "puntos": 4,  "correlativas": ["Taller de Práctica Preprofesional"]},
    "Seminario Optativo 4":                              {"periodo": "2° Cuat.", "puntos": 4,  "correlativas": ["Taller de Práctica Preprofesional"]},
}

# Áreas para radar chart
AREAS = {
    "Matemática":     ["Matemática I", "Matemática II", "Cálculo Financiero", "Estadística"],
    "Económica":      ["Introducción a Economía Empresarial", "Historia Económica Contemporánea",
                       "Empresa, Economía y Sociedad", "Microeconomía I", "Microeconomía II", "Macroeconomía",
                       "Economía Bancaria y Financiera", "Política Económica", "Comercio Exterior",
                       "Financiamiento"],
    "Administración": ["Organización y Gestión", "Comercialización", "Costos Empresariales",
                       "Control de Gestión", "Taller de Práctica Preprofesional",
                       "Seminario de Pensamiento Nacional Latinoamericano",
                       "Seminario de Justicia y Derechos Humanos",
                       "Plan de Negocios", "Organización de la Producción y la Tecnología",
                       "Formulación de Proyectos de Inversión", "Evaluación de Proyectos de Inversión",
                       "Relaciones Laborales", "Sistemas de Organización",
                       "Taller de Proyecto Empresarial", "Planeamiento Estratégico",
                       "Tecnología y Ciencia de Datos", "Inteligencia de Negocios",
                       "Seminario Optativo 1", "Seminario Optativo 2",
                       "Seminario Optativo 3", "Seminario Optativo 4"],
    "Jurídica":       ["Derecho Comercial", "Principios de Tributación"],
    "Comunicación":   ["Taller de Comunicación y Producción de Textos", "Contabilidad", "Inglés I"],
}

CREDITOS_TOTAL_TECNICATURA  = 120
CREDITOS_TOTAL_LICENCIATURA = 240
TOTAL_MATERIAS = len(PLAN_ESTUDIOS)

# Estados que la app considera "reales". Cualquier fila con un estado fuera de
# este set es basura/fantasma (queda invisible en la UI pero rompe la lógica).
ESTADOS_VALIDOS = {"Cursando", "Final", "Aprobada"}

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

SQUAD_MAP = {
    "Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa",
    "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma",
}

# Horarios y docentes — comisión M-Z NOCHE (1er año) + 2do año NOCHE + contracursadas
HORARIOS = {
    # 1er año M-Z NOCHE
    "Contabilidad": {
        "dia": "Miércoles", "turno": "Noche", "comision": "M-Z",
        "docente": "Cdor. Manuel Calvo", "instructor": "",
    },
    "Historia Económica Contemporánea": {
        "dia": "Martes", "turno": "Noche", "comision": "M-Z",
        "docente": "Dr. Miguel Mazzeo", "instructor": "",
    },
    "Taller de Comunicación y Producción de Textos": {
        "dia": "Miércoles", "turno": "Noche", "comision": "M-Z",
        "docente": "Dr. Miguel Mazzeo", "instructor": "Mg. Diego Martínez",
    },
    "Matemática I": {
        "dia": "Jueves", "turno": "Noche", "comision": "M-Z",
        "docente": "Lic. Viviana Pan", "instructor": "Lic. Natalia Rosso",
    },
    # 2do año NOCHE
    "Comercialización": {
        "dia": "Lunes", "turno": "Noche", "comision": "2do",
        "docente": "DI Carlos Alonso", "instructor": "",
    },
    "Microeconomía I": {
        "dia": "Martes", "turno": "Noche", "comision": "2do",
        "docente": "Mg. Carlos Prieu", "instructor": "Lic. Jonatan Aguirre",
    },
    "Costos Empresariales": {
        "dia": "Miércoles", "turno": "Noche", "comision": "2do",
        "docente": "Cdor. Gabriel Módica", "instructor": "",
    },
    "Cálculo Financiero": {
        "dia": "Viernes", "turno": "Noche", "comision": "2do",
        "docente": "Lic. P. Lemos - Lic. K. Angulo", "instructor": "",
    },
    # Contracursadas NOCHE
    "Empresa, Economía y Sociedad": {
        "dia": "Lunes", "turno": "Noche", "comision": "Contrac.",
        "docente": "Dr. José Fernández", "instructor": "",
    },
    "Matemática II": {
        "dia": "Martes", "turno": "Noche", "comision": "Contrac.",
        "docente": "Lic. Viviana Pan", "instructor": "Lic. Natalia Rosso",
    },
    "Derecho Comercial": {
        "dia": "Miércoles", "turno": "Noche", "comision": "Contrac.",
        "docente": "Mg. Matías Novoa Haidar", "instructor": "Mg. Nicolás Caputo",
    },
    "Organización y Gestión": {
        "dia": "Jueves", "turno": "Noche", "comision": "Contrac.",
        "docente": "Cdra. Analuz Vidal", "instructor": "",
    },
}

DIAS_ORDEN = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Materias que se aprueban por cursada, sin final obligatorio
MATERIAS_SIN_FINAL = {
    "Introducción a Economía Empresarial",
    "Seminario de Justicia y Derechos Humanos",
    "Seminario de Pensamiento Nacional Latinoamericano",
    "Taller de Comunicación y Producción de Textos",
    "Taller de Práctica Preprofesional",
    "Taller de Proyecto Empresarial",
    "Seminario Optativo 1",
    "Seminario Optativo 2",
    "Seminario Optativo 3",
    "Seminario Optativo 4",
}


# ─────────────────────────────────────────────
# 3. HELPERS
# ─────────────────────────────────────────────
def _inscribir_materia(conn, df, usuario, materia, modalidad="Regular"):
    """
    Anota al usuario en una materia como 'Cursando'.
    🧹 Anti-duplicado: borra cualquier fila previa de ESA materia para ESE
    usuario (fantasmas, estados basura, duplicados) antes de crear la nueva.
    """
    df_limpio = df[~mascara_materia(df, usuario, materia)].copy()
    nueva = pd.DataFrame([{
        "Nombre": usuario, "Materia": materia, "Estado": "Cursando",
        "Cursada": modalidad,
        "Nota": "", "Nota_parcial1": "", "Nota_parcial2": "",
        "Fecha_aprobacion": "", "Fecha_examen": "", "Aplazos": "",
    }])
    guardar_df(conn, pd.concat([df_limpio, nueva], ignore_index=True), usuario)


def _norm_nombre(s: str) -> str:
    return materia_id(s)


def get_avatar_path(usuario: str, n_aprobadas: int) -> str:
    char  = SQUAD_MAP.get(usuario, "Marco")
    nivel = 1 if n_aprobadas <= 10 else 2 if n_aprobadas <= 20 else 3 if n_aprobadas <= 30 else 4
    return str(Path(__file__).parent / "assets" / f"{char}_{nivel}.gif")


def barra_retro_html(pct: float, color: str, glow: str, label: str = "") -> str:
    """Barra de progreso estilo HP/XP arcade: segmentada, con glow neón."""
    pct = max(0.0, min(100.0, float(pct)))
    label_html = (
        f"<span style='position:absolute; right:8px; top:2px; font-family:monospace; "
        f"font-size:12px; color:#fff; text-shadow:1px 1px 2px #000; z-index:2;'>{label}</span>"
        if label else ""
    )
    return (
        f"<div style='background:#11141a; border:2px solid {color}; border-radius:4px; "
        f"height:22px; position:relative; overflow:hidden; margin:2px 0; "
        f"box-shadow:0 0 7px {glow}, inset 0 0 6px rgba(0,0,0,0.6);'>"
        f"<div style='width:{pct:.1f}%; height:100%; "
        f"background:repeating-linear-gradient(90deg, {color} 0px, {color} 9px, "
        f"{glow} 9px, {glow} 11px); box-shadow:0 0 10px {glow}; "
        f"transition:width .5s ease;'></div>{label_html}</div>"
    )


def get_rango_militar(creditos: int) -> tuple:
    """Devuelve (nombre_rango, color) según créditos acumulados (escala sobre 240)."""
    escala = [
        (0,   "🎖️ RECLUTA",  "#888888"),
        (20,  "🎖️ SOLDADO",  "#2ecc71"),
        (50,  "🪖 CABO",      "#3498db"),
        (90,  "🪖 SARGENTO",  "#9b59b6"),
        (140, "⭐ TENIENTE",  "#f1c40f"),
        (190, "⭐ CAPITÁN",   "#e67e22"),
        (240, "🏆 GENERAL",   "#ff4b4b"),
    ]
    nombre, color = escala[0][1], escala[0][2]
    for umbral, n, c in escala:
        if creditos >= umbral:
            nombre, color = n, c
    return nombre, color


def normalizar_estado(df: pd.DataFrame) -> pd.DataFrame:
    def _norm(v):
        v = str(v).strip()
        if v.lower() == "final":
            return "Final"
        return v.capitalize()
    df["Estado"] = df["Estado"].apply(_norm)
    return df


def calcular_promedio_ponderado(aprobadas_df: pd.DataFrame) -> float:
    total_pts = total_pond = 0
    for _, row in aprobadas_df.iterrows():
        nota = pd.to_numeric(row.get("Nota", ""), errors="coerce")
        pts  = PLAN_ESTUDIOS.get(row["Materia"], {}).get("puntos", 0)
        if pd.notna(nota) and pts > 0:
            total_pond += nota * pts
            total_pts  += pts
    return (total_pond / total_pts) if total_pts > 0 else 0.0


def asignar_periodo_real(materia: str, cursada: str) -> str:
    teorico = PLAN_ESTUDIOS.get(materia, {}).get("periodo", "1° Cuat.")
    if cursada == "Contracursada":
        return "2° Cuatrimestre" if teorico == "1° Cuat." else "1° Cuatrimestre"
    return "1° Cuatrimestre" if teorico in ("1° Cuat.", "Anual") else "2° Cuatrimestre"


def guardar_df(conn, df_local: pd.DataFrame, usuario: str | None = None) -> bool:
    """Only return after read-back confirmation; stop the UI on any failure."""
    try:
        result = guardar_usuario(conn, df_local, usuario, st.session_state.get("_base_df"))
    except SaveError as exc:
        st.error(f"🛑 {exc}")
        st.stop()
    st.cache_data.clear()
    st.session_state.pop("_session_df", None)
    st.session_state["_save_notice"] = (
        "✅ Cambios guardados y verificados."
        if result.backup_confirmed else
        "✅ Cambios guardados y verificados. ⚠️ No se pudo crear el respaldo previo."
    )
    return True


def asegurar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "Nota": "", "Cursada": "Regular", "Estado": "Cursando",
        "Nota_parcial1": "", "Nota_parcial2": "",
        "Fecha_aprobacion": "", "Fecha_examen": "",
        "Tiene_final": "", "Aplazos": "",
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
        else:
            # Empty Sheets columns may be inferred as float; editors also store
            # dates and blanks, so keep the mixed legacy schema writable.
            blank = "" if col == "Estado" else val
            df[col] = df[col].astype(object).where(pd.notna(df[col]), blank)
    return df


def get_horario_badge(materia: str) -> str:
    """Retorna un string corto con día + docente para mostrar en tarjeta."""
    h = HORARIOS.get(materia)
    if not h:
        return ""
    inst = f" · {h['instructor']}" if h["instructor"] else ""
    return f"📅 {h['dia']} · {h['docente']}{inst}"


def dia_es_hoy(materia: str) -> bool:
    h = HORARIOS.get(materia)
    if not h:
        return False
    return h["dia"] == DIAS_ORDEN[date.today().weekday()]


def get_conflicto_horario(materia_nueva: str, mis_datos: pd.DataFrame) -> str | None:
    """
    Dado una materia que se quiere cursar, devuelve el nombre de la materia
    que ya está activa (Cursando) en el mismo día, o None si no hay conflicto.
    """
    horario_por_id = {materia_id(m): h for m, h in HORARIOS.items()}
    h_nueva = horario_por_id.get(materia_id(materia_nueva))
    if not h_nueva:
        return None
    dia_nueva = h_nueva["dia"]
    # Solo bloquean el horario las materias que estás CURSANDO realmente.
    # Una materia en "Final" ya terminó la cursada (no vas a clase), no genera conflicto.
    activas = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
    for m_activa in activas:
        h_activa = horario_por_id.get(materia_id(m_activa))
        if h_activa and h_activa["dia"] == dia_nueva:
            return m_activa
    return None


def dias_restantes(fecha_str: str):
    try:
        fecha = datetime.strptime(str(fecha_str).strip(), "%Y-%m-%d").date()
        return (fecha - date.today()).days
    except Exception:
        return None


def estimar_egreso(aprobadas_df: pd.DataFrame):
    """Historical scenario using dated approvals only; no academic guarantees."""
    if "Fecha_aprobacion" not in aprobadas_df.columns:
        return None
    fechas = pd.to_datetime(aprobadas_df["Fecha_aprobacion"], errors="coerce").dropna()
    if len(fechas) < 2 or len(aprobadas_df) >= TOTAL_MATERIAS:
        return None
    delta = (fechas.max() - fechas.min()).days
    if delta <= 0:
        return None
    ritmo = (len(fechas) - 1) / delta
    estimated = date.today() + timedelta(days=(TOTAL_MATERIAS - len(aprobadas_df)) / ritmo)
    return f"{MESES_ES[estimated.month - 1]} {estimated.year}"


def calcular_racha(mis_datos: pd.DataFrame) -> int:
    """
    🔥 Racha actual: materias aprobadas consecutivas (por fecha, de la más
    reciente hacia atrás) sin ningún aplazo registrado en esa materia.
    """
    ap = mis_datos[mis_datos["Estado"] == "Aprobada"].copy()
    if ap.empty:
        return 0
    ap["_f"] = pd.to_datetime(ap["Fecha_aprobacion"], errors="coerce")
    ap = ap.dropna(subset=["_f"]).sort_values("_f")
    racha = 0
    for _, r in ap.iloc[::-1].iterrows():
        apl = pd.to_numeric(r.get("Aplazos", ""), errors="coerce")
        if pd.isna(apl) or apl == 0:
            racha += 1
        else:
            break
    return racha


def calcular_logros(mis_datos: pd.DataFrame, aprobadas_df: pd.DataFrame, puntos: int) -> list:
    """Logros PERSONALES (contra tu propia carrera, no contra el squad)."""
    notas = pd.to_numeric(aprobadas_df["Nota"], errors="coerce") if not aprobadas_df.empty else pd.Series(dtype=float)
    p1 = pd.to_numeric(mis_datos.get("Nota_parcial1", pd.Series(dtype=object)), errors="coerce")
    p2 = pd.to_numeric(mis_datos.get("Nota_parcial2", pd.Series(dtype=object)), errors="coerce")
    tiene_10 = bool((notas == 10).any() or (p1 == 10).any() or (p2 == 10).any())

    aplazos_tot = pd.to_numeric(mis_datos.get("Aplazos", pd.Series(dtype=object)), errors="coerce").fillna(0).sum()

    # RAMBO: 3+ materias aprobadas dentro de un mismo semestre calendario
    rambo = False
    fechas = pd.to_datetime(aprobadas_df["Fecha_aprobacion"], errors="coerce").dropna() if not aprobadas_df.empty else pd.Series(dtype="datetime64[ns]")
    if not fechas.empty:
        sem = fechas.dt.year.astype(str) + "-S" + ((fechas.dt.month > 6).astype(int) + 1).astype(str)
        rambo = bool(sem.value_counts().max() >= 3)

    return [
        ("🩸", "FIRST BLOOD", "Primera materia aprobada",          len(aprobadas_df) >= 1),
        ("🎯", "HEADSHOT",    "Un 10 en parcial o final",           tiene_10),
        ("🔫", "RAMBO",       "3 aprobadas en un mismo semestre",   rambo),
        ("🛡️", "FLAWLESS",    "5+ aprobadas sin ningún aplazo",     len(aprobadas_df) >= 5 and aplazos_tot == 0),
        ("🪖", "VETERANO",    "10 materias aprobadas",              len(aprobadas_df) >= 10),
        ("🏅", "TÉCNICO",     "120 créditos (Tecnicatura)",         puntos >= CREDITOS_TOTAL_TECNICATURA),
    ]


def _base_audio_script() -> str:
    """Script base con Web Audio API para todos los sonidos del juego."""
    script = r"""
    <script>
    // ── Web Audio API context ──────────────────────────────────────────
    var _ctx = null;
    function getCtx() {
        if (!_ctx) _ctx = new (window.AudioContext || window.webkitAudioContext)();
        return _ctx;
    }

    // ── DISPARO: ruido blanco con envolvente rápida ────────────────────
    function playGunshot() {
        var ctx = getCtx();
        var bufSize = ctx.sampleRate * 0.18;
        var buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
        var data = buf.getChannelData(0);
        for (var i = 0; i < bufSize; i++) {
            data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufSize, 3.5);
        }
        // Cuerpo del disparo
        var src = ctx.createBufferSource();
        src.buffer = buf;
        var gain = ctx.createGain();
        gain.gain.setValueAtTime(1.4, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.18);
        var filter = ctx.createBiquadFilter();
        filter.type = "lowpass";
        filter.frequency.setValueAtTime(1800, ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(200, ctx.currentTime + 0.18);
        src.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        src.start();
        // Casquillo metálico
        setTimeout(function() {
            var ctx2 = getCtx();
            var osc = ctx2.createOscillator();
            var g2  = ctx2.createGain();
            osc.type = "triangle";
            osc.frequency.setValueAtTime(900, ctx2.currentTime);
            osc.frequency.exponentialRampToValueAtTime(300, ctx2.currentTime + 0.12);
            g2.gain.setValueAtTime(0.25, ctx2.currentTime);
            g2.gain.exponentialRampToValueAtTime(0.001, ctx2.currentTime + 0.12);
            osc.connect(g2);
            g2.connect(ctx2.destination);
            osc.start();
            osc.stop(ctx2.currentTime + 0.12);
        }, 80);
    }

    // ── VICTORIA: fanfarria épica ──────────────────────────────────────
    function playVictory() {
        var ctx = getCtx();
        var notes = [
            { f: 523, t: 0.00, d: 0.12 },
            { f: 659, t: 0.10, d: 0.12 },
            { f: 784, t: 0.20, d: 0.12 },
            { f: 1047, t: 0.30, d: 0.30 },
            { f: 880, t: 0.32, d: 0.12 },
            { f: 1047, t: 0.50, d: 0.40 },
        ];
        notes.forEach(function(n) {
            var osc  = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.type = "square";
            osc.frequency.value = n.f;
            gain.gain.setValueAtTime(0.0, ctx.currentTime + n.t);
            gain.gain.linearRampToValueAtTime(0.18, ctx.currentTime + n.t + 0.01);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + n.t + n.d);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(ctx.currentTime + n.t);
            osc.stop(ctx.currentTime + n.t + n.d + 0.05);
        });
    }

    // ── CLIC RETRO: bip corto ─────────────────────────────────────────
    function playClick() {
        var ctx  = getCtx();
        var osc  = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = "square";
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 0.06);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.08);
    }

    // ── BORRAR: sonido descendente ────────────────────────────────────
    function playDelete() {
        var ctx  = getCtx();
        var osc  = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(300, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.22);
    }

    // ── HEADSHOT: CS-style (disparo seco + pitch descendente brusco) ──
    function playHeadshot() {
        var ctx = getCtx();

        // 1. Disparo seco (ruido blanco corto y agresivo)
        var bufSize = ctx.sampleRate * 0.12;
        var buf  = ctx.createBuffer(1, bufSize, ctx.sampleRate);
        var data = buf.getChannelData(0);
        for (var i = 0; i < bufSize; i++) {
            data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufSize, 5);
        }
        var src    = ctx.createBufferSource();
        src.buffer = buf;
        var filt   = ctx.createBiquadFilter();
        filt.type  = "bandpass";
        filt.frequency.value = 1200;
        filt.Q.value = 0.8;
        var g1 = ctx.createGain();
        g1.gain.setValueAtTime(2.0, ctx.currentTime);
        g1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);
        src.connect(filt); filt.connect(g1); g1.connect(ctx.destination);
        src.start();

        // 2. "Ping" metálico de headshot (tono descendente brusco)
        setTimeout(function() {
            var ctx2 = getCtx();
            var osc  = ctx2.createOscillator();
            var g2   = ctx2.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(1800, ctx2.currentTime);
            osc.frequency.exponentialRampToValueAtTime(400, ctx2.currentTime + 0.18);
            g2.gain.setValueAtTime(0.5, ctx2.currentTime);
            g2.gain.exponentialRampToValueAtTime(0.001, ctx2.currentTime + 0.18);
            osc.connect(g2); g2.connect(ctx2.destination);
            osc.start(); osc.stop(ctx2.currentTime + 0.2);
        }, 40);

        // 3. "HEADSHOT" sintetizado: 3 beeps descendentes cortos
        var beeps = [
            { f: 880, t: 0.18 },
            { f: 660, t: 0.28 },
            { f: 440, t: 0.38 },
        ];
        beeps.forEach(function(b) {
            setTimeout(function() {
                var ctx3 = getCtx();
                var o = ctx3.createOscillator();
                var g = ctx3.createGain();
                o.type = "square";
                o.frequency.value = b.f;
                g.gain.setValueAtTime(0.2, ctx3.currentTime);
                g.gain.exponentialRampToValueAtTime(0.001, ctx3.currentTime + 0.07);
                o.connect(g); g.connect(ctx3.destination);
                o.start(); o.stop(ctx3.currentTime + 0.08);
            }, b.t * 1000);
        });
    }

    // ── FINISH HIM: Mortal Kombat-style ───────────────────────────────
    function playFinishHim() {
        var ctx = getCtx();

        // Reverb simple con ConvolverNode
        function makeReverb(ctx, seconds) {
            var rate    = ctx.sampleRate;
            var length  = rate * seconds;
            var impulse = ctx.createBuffer(2, length, rate);
            for (var c = 0; c < 2; c++) {
                var ch = impulse.getChannelData(c);
                for (var i = 0; i < length; i++) {
                    ch[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 2);
                }
            }
            var conv = ctx.createConvolver();
            conv.buffer = impulse;
            return conv;
        }

        var reverb = makeReverb(ctx, 1.2);
        var master = ctx.createGain();
        master.gain.value = 0.7;
        reverb.connect(master);
        master.connect(ctx.destination);

        function note(freq, startT, dur, type) {
            type = type || "sawtooth";
            var o = ctx.createOscillator();
            var g = ctx.createGain();
            o.type = type;
            o.frequency.setValueAtTime(freq, ctx.currentTime + startT);
            g.gain.setValueAtTime(0.0,  ctx.currentTime + startT);
            g.gain.linearRampToValueAtTime(0.35, ctx.currentTime + startT + 0.02);
            g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + startT + dur);
            o.connect(g); g.connect(reverb); g.connect(ctx.destination);
            o.start(ctx.currentTime + startT);
            o.stop(ctx.currentTime + startT + dur + 0.05);
        }

        // "FI-NISH HIM" — melodía icónica aproximada
        // Frase 1: FI - NISH
        note(220, 0.00, 0.18, "sawtooth");   // FI
        note(196, 0.00, 0.18, "square");
        note(165, 0.20, 0.18, "sawtooth");   // NISH
        note(147, 0.20, 0.18, "square");
        // Pausa dramática
        // Frase 2: HIM (nota baja, sostenida)
        note(110, 0.50, 0.55, "sawtooth");
        note(98,  0.50, 0.55, "square");
        // Golpe final percusivo
        setTimeout(function() {
            var ctx2 = getCtx();
            var bSize = ctx2.sampleRate * 0.08;
            var bbuf  = ctx2.createBuffer(1, bSize, ctx2.sampleRate);
            var bdata = bbuf.getChannelData(0);
            for (var i = 0; i < bSize; i++) {
                bdata[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bSize, 2);
            }
            var bs = ctx2.createBufferSource();
            bs.buffer = bbuf;
            var bg = ctx2.createGain();
            bg.gain.setValueAtTime(1.5, ctx2.currentTime);
            bg.gain.exponentialRampToValueAtTime(0.001, ctx2.currentTime + 0.08);
            bs.connect(bg); bg.connect(ctx2.destination);
            bs.start();
        }, 1150);
    }

    // ── MISSION COMPLETE: Metal Slug style ───────────────────────────
    function playMissionComplete() {
        var ctx = getCtx();

        function note(freq, startT, dur, type, vol) {
            var o = ctx.createOscillator();
            var g = ctx.createGain();
            o.type = type || "square";
            o.frequency.value = freq;
            g.gain.setValueAtTime(0.0,  ctx.currentTime + startT);
            g.gain.linearRampToValueAtTime(vol || 0.20, ctx.currentTime + startT + 0.01);
            g.gain.setValueAtTime(vol || 0.20,          ctx.currentTime + startT + dur - 0.02);
            g.gain.linearRampToValueAtTime(0.001,       ctx.currentTime + startT + dur);
            o.connect(g); g.connect(ctx.destination);
            o.start(ctx.currentTime + startT);
            o.stop(ctx.currentTime  + startT + dur + 0.02);
        }

        function drum(startT, vol) {
            var ctx2  = getCtx();
            var bSize = Math.floor(ctx2.sampleRate * 0.06);
            var buf   = ctx2.createBuffer(1, bSize, ctx2.sampleRate);
            var data  = buf.getChannelData(0);
            for (var i = 0; i < bSize; i++) {
                data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bSize, 4);
            }
            setTimeout(function() {
                var c   = getCtx();
                var src = c.createBufferSource();
                src.buffer = buf;
                var g = c.createGain();
                g.gain.value = vol || 0.6;
                src.connect(g); g.connect(c.destination);
                src.start();
            }, startT * 1000);
        }

        // Jingle Metal Slug "MISSION COMPLETE" aproximado
        // Fanfarria inicial
        note(392, 0.00, 0.08, "square", 0.22);
        note(523, 0.09, 0.08, "square", 0.22);
        note(659, 0.18, 0.08, "square", 0.22);
        note(784, 0.27, 0.18, "square", 0.25);
        // Acorde de victoria
        note(523, 0.50, 0.08, "square", 0.18);
        note(659, 0.59, 0.08, "square", 0.18);
        note(784, 0.68, 0.30, "square", 0.22);
        note(1047,0.68, 0.30, "square", 0.15);
        // Remate final glorioso
        note(659, 1.05, 0.10, "square", 0.18);
        note(784, 1.16, 0.10, "square", 0.20);
        note(1047,1.27, 0.45, "square", 0.25);
        note(1319,1.27, 0.45, "square", 0.15);
        // Bombos
        drum(0.00, 0.7);
        drum(0.27, 0.5);
        drum(0.50, 0.7);
        drum(0.68, 0.5);
        drum(1.05, 0.7);
        drum(1.27, 0.8);
    }
    </script>
    """

    # Route every synthesized effect through one limiter and volume bus.
    for context in ("ctx", "ctx2", "ctx3"):
        script = script.replace(f"connect({context}.destination)", "connect(getOutput())")
    output = """
    var _output = null;
    function getOutput() {
        if (!_output) {
            var ctx = getCtx();
            var limiter = ctx.createDynamicsCompressor();
            limiter.threshold.value = -12;
            limiter.ratio.value = 12;
            var volume = ctx.createGain();
            volume.gain.value = __VOLUME__;
            limiter.connect(volume);
            volume.connect(ctx.destination);
            _output = limiter;
        }
        return _output;
    }
    """.replace("__VOLUME__", str(st.session_state.get("volumen", 45) / 100))
    return script.replace("</script>", output + "</script>")


def sound_html(sound: str) -> str:
    functions = {"gunshot":"playGunshot", "click":"playClick", "delete":"playDelete",
                 "headshot":"playHeadshot", "finishhim":"playFinishHim", "missioncomplete":"playMissionComplete"}
    call = functions.get(sound, "playClick")
    return _base_audio_script() + """
    <style>body{margin:0;background:#0b0d11;color:#f1c40f;font:14px monospace}
    button{background:#1a1c23;color:#f1c40f;border:1px solid #f1c40f;border-radius:5px;min-height:44px;padding:8px 12px;font:inherit;cursor:pointer}
    button:focus-visible{outline:3px solid white}</style>
    <button id="play">▶ Reproducir efecto</button>
    <script>
    let played = false;
    function startEffect() {
        const ctx = getCtx();
        ctx.resume().then(() => {
            if (played) return;
            played = true;
            __CALL__();
            document.getElementById('play').hidden = true;
            setTimeout(() => { if (_ctx) _ctx.close(); }, 5000);
        }).catch(() => {});
    }
    document.getElementById('play').onclick = startEffect;
    startEffect();
    </script>
    """.replace("__CALL__", call)


def confetti_html() -> str:
    """Short local celebration; no CDN or remote graphics. Sound is independent."""
    return r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
    body{margin:0;background:#0b0d11;color:#f1c40f;font:700 20px monospace;overflow:hidden}
    #banner{position:absolute;inset:40px 0 auto;text-align:center;letter-spacing:3px;text-shadow:0 0 12px #f1c40f88}
    canvas{width:100%;height:150px;pointer-events:none}
    @media(prefers-reduced-motion:reduce){canvas{display:none}#banner{text-shadow:none}}
    </style></head><body><div id="banner" role="status">★ MISSION COMPLETE ★</div><canvas id="fx" aria-hidden="true"></canvas>
    <script>(()=>{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    const canvas=document.getElementById('fx'),ctx=canvas.getContext('2d');canvas.width=900;canvas.height=150;
    const colors=['#f1c40f','#ff7373','#61b9ff','#2ecc71'];
    const particles=Array.from({length:56},()=>({x:450,y:90,vx:(Math.random()-.5)*16,vy:-Math.random()*8-1,c:colors[Math.floor(Math.random()*4)]}));
    let frame=0;function draw(){ctx.clearRect(0,0,900,150);ctx.globalAlpha=1-frame/90;
    for(const p of particles){p.x+=p.vx;p.y+=p.vy;p.vy+=.16;ctx.fillStyle=p.c;ctx.fillRect(p.x,p.y,5,5)}
    if(++frame<90)requestAnimationFrame(draw)}requestAnimationFrame(draw)})();</script></body></html>"""


def _get_examenes_proximos(mis_datos: pd.DataFrame) -> list:
    """Exámenes con fecha cargada. Solo estados activos (Cursando / Final):
    las materias ya aprobadas no vuelven a aparecer con su vieja fecha."""
    resultado = []
    for _, row in mis_datos[mis_datos["Estado"].isin(["Cursando", "Final"])].iterrows():
        fecha_str = str(row.get("Fecha_examen", "")).strip()
        if not fecha_str or fecha_str in ("", "nan", "NaT", "None"):
            continue
        dias = dias_restantes(fecha_str)
        # El tipo se deduce del estado real: en "Final" es examen final;
        # en "Cursando" la fecha cargada corresponde a un parcial.
        tipo = "🏆 Final" if row["Estado"] == "Final" else "🎯 Parcial"
        resultado.append({"materia": row["Materia"], "fecha_str": fecha_str, "dias": dias, "tipo": tipo})
    resultado.sort(key=lambda x: (x["dias"] is None, x["dias"] if x["dias"] is not None else 9999))
    return resultado


# ─────────────────────────────────────────────
# 4. GRÁFICOS
# ─────────────────────────────────────────────
def arbol_correlativas_html(aprobadas: list, cursando: list, en_final: list = None, foco=None) -> str:
    rows = [{"Materia": m, "Estado": state} for state, subjects in
            [("Cursando", cursando), ("Final", en_final or []), ("Aprobada", aprobadas)] for m in subjects]
    data = pd.DataFrame(rows, columns=["Materia", "Estado"])
    return graph_html(PLAN_ESTUDIOS, estados_por_materia(data), foco)


def grafico_radar(aprobadas_df: pd.DataFrame) -> go.Figure:
    """Legacy function name retained; horizontal bars compare progress clearly."""
    approved = {materia_id(m) for m in aprobadas_df["Materia"]}
    areas, percentages, labels = [], [], []
    for area, subjects in AREAS.items():
        count = sum(materia_id(m) in approved for m in subjects)
        areas.append(area)
        percentages.append(count / len(subjects) * 100)
        labels.append(f"{count}/{len(subjects)} · {count / len(subjects):.0%}")
    fig = go.Figure(go.Bar(y=areas, x=percentages, orientation="h", text=labels,
        textposition="auto", marker_color="#3498db", insidetextfont=dict(color="#ffffff"),
        hovertemplate="%{y}: %{text}<extra></extra>"))
    fig.update_layout(paper_bgcolor="#0b0d11", plot_bgcolor="#0b0d11", font=dict(color="#e0e0e0",size=14),
        xaxis=dict(range=[0,110], ticksuffix="%", gridcolor="#333", title="Materias aprobadas del área"),
        yaxis=dict(autorange="reversed",automargin=True), height=340,
        margin=dict(l=10,r=20,t=20,b=40), dragmode=False)
    return fig


def grafico_progreso_tiempo(aprobadas_df: pd.DataFrame):
    if "Fecha_aprobacion" not in aprobadas_df.columns:
        return None
    dates = pd.to_datetime(aprobadas_df["Fecha_aprobacion"], errors="coerce").dropna()
    if dates.empty:
        return None
    counts = dates.value_counts().sort_index().cumsum()
    fig = go.Figure(go.Scatter(
        x=counts.index, y=counts.values, mode="lines+markers",
        line=dict(color="#f1c40f", width=3, shape="hv"), marker=dict(color="#ff7373", size=8),
        hovertemplate="%{x|%d/%m/%Y}<br>Aprobadas con fecha: %{y}<extra></extra>",
    ))
    fig.update_layout(paper_bgcolor="#0b0d11", plot_bgcolor="#0b0d11", font=dict(color="#e0e0e0"),
        xaxis=dict(title="Fecha", gridcolor="#333"), yaxis=dict(title="Aprobadas con fecha", rangemode="tozero", dtick=1),
        height=320, margin=dict(l=20,r=20,t=20,b=20), dragmode=False)
    return fig


# ─────────────────────────────────────────────
# 5. VISTAS
# ─────────────────────────────────────────────

def _boton_borrar_confirmado(col, conn, df, usuario, materia, key_btn: str, conf_key: str) -> bool:
    """
    Botón 🗑️ con confirmación en dos toques (anti-dedazo mobile).
    Devuelve True si se ejecutó el borrado.
    """
    if col.button("🗑️", key=key_btn, **ANCHO_COMPLETO, help="Eliminar (requiere 2 toques)"):
        if st.session_state.get(conf_key, False):
            st.session_state[conf_key] = False
            idx_drop = df[mascara_materia(df, usuario, materia)].index
            guardar_df(conn, df.drop(idx_drop).reset_index(drop=True), usuario)
            st.session_state["play_sound"] = "delete"
            st.rerun()
            return True
        else:
            st.session_state[conf_key] = True
            st.rerun()
    return False


def vista_inicio(conn, df, usuario, mis_datos, aprobadas_df, cursando_df, final_df,
                 puntos_logrados, promedio_simple, promedio_pond):

    col_av, col_cur = st.columns([1, 3])

    with col_av:
        img_path = get_avatar_path(usuario, len(aprobadas_df))
        if os.path.exists(img_path) and st.session_state.get("efectos", True):
            st.image(img_path, width=120)
        else:
            st.markdown("🎮")

        # Métricas en mini-tarjetas compactas
        st.markdown(
            f"""<div style='display:flex; flex-wrap:wrap; gap:8px; margin:8px 0;'>
                <div style='background:#1a1c23; border-radius:6px; padding:8px 12px; flex:1; min-width:70px; text-align:center;'>
                    <div style='color:#aaa; font-size:12px; font-family:monospace;'>PUNTOS</div>
                    <div style='color:#f1c40f; font-size:16px; font-weight:bold;'>{puntos_logrados}</div>
                </div>
                <div style='background:#1a1c23; border-radius:6px; padding:8px 12px; flex:1; min-width:70px; text-align:center;'>
                    <div style='color:#aaa; font-size:12px; font-family:monospace;'>PROM.</div>
                    <div style='color:#3498db; font-size:16px; font-weight:bold;'>{promedio_simple:.2f}</div>
                </div>
                <div style='background:#1a1c23; border-radius:6px; padding:8px 12px; flex:1; min-width:70px; text-align:center;'>
                    <div style='color:#aaa; font-size:12px; font-family:monospace;'>POND.</div>
                    <div style='color:#2ecc71; font-size:16px; font-weight:bold;'>{promedio_pond:.2f}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        rango_nombre, rango_color = get_rango_militar(puntos_logrados)
        st.markdown(
            f"<div style='background:#1a1c23; border:1px solid {rango_color}; border-radius:6px; "
            f"padding:6px 10px; margin:8px 0 4px 0; text-align:center; "
            f"box-shadow:0 0 8px {rango_color}55;'>"
            f"<span style='color:{rango_color}; font-family:monospace; font-size:13px; "
            f"font-weight:bold; text-shadow:1px 1px 2px #000;'>{rango_nombre}</span></div>",
            unsafe_allow_html=True,
        )

        # 🔥 Racha personal (finales al hilo sin aplazo)
        racha = calcular_racha(mis_datos)
        if racha >= 2:
            fuego = "🔥" * min(racha, 5)
            st.markdown(
                f"<div style='background:#1a1200; border:1px solid #e67e22; border-radius:6px; "
                f"padding:5px 10px; margin:4px 0; text-align:center;'>"
                f"<span style='color:#e67e22; font-family:monospace; font-size:12px;'>"
                f"{fuego} RACHA: {racha} al hilo</span></div>",
                unsafe_allow_html=True,
            )

        egreso = estimar_egreso(aprobadas_df)
        if egreso:
            st.markdown(
                f"<p style='font-size:12px; color:#aaa;'>🎓 Fin estimado (Licenciatura): "
                f"<strong style='color:#2ecc71'>{egreso}</strong></p>",
                unsafe_allow_html=True,
            )

        st.link_button("📂 DRIVE SQUAD",  "https://drive.google.com/drive/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs", **ANCHO_COMPLETO)
        st.link_button("🏛️ SIU GUARANÍ", "https://estudiantes.unla.edu.ar/autogestion3w/acceso",                     **ANCHO_COMPLETO)
        st.link_button("💻 CAMPUS UNLA", "https://campus.unla.edu.ar/aulas/login/index.php",                          **ANCHO_COMPLETO)
        st.link_button("🧠 ESTUDIO IA",  "https://estudio-ia.streamlit.app/",                                         **ANCHO_COMPLETO)

    with col_cur:
        st.markdown("#### 🏆 PROGRESO POR CRÉDITOS:")
        prog_tec = min(puntos_logrados / CREDITOS_TOTAL_TECNICATURA, 1.0)
        st.markdown(
            barra_retro_html(prog_tec * 100, "#3498db", "#5dade2", f"{int(prog_tec*100)}%"),
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p class='hp-bar-text-blue'>TECNICATURA: {puntos_logrados}/{CREDITOS_TOTAL_TECNICATURA} pts ({int(prog_tec*100)}%)</p>",
            unsafe_allow_html=True,
        )
        prog_lic = min(puntos_logrados / CREDITOS_TOTAL_LICENCIATURA, 1.0)
        st.markdown(
            barra_retro_html(prog_lic * 100, "#ff4b4b", "#ff7b7b", f"{int(prog_lic*100)}%"),
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p class='hp-bar-text'>LICENCIATURA: {puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA} pts ({int(prog_lic*100)}%)</p>",
            unsafe_allow_html=True,
        )

        # Próximos exámenes en inicio (máx. 3, solo futuros o de hoy)
        examenes = [e for e in _get_examenes_proximos(mis_datos)
                    if e["dias"] is not None and e["dias"] >= 0]
        if examenes:
            st.markdown("---")
            st.markdown("#### 📅 PRÓXIMOS EXÁMENES:")
            for ex in examenes[:3]:
                dias    = ex["dias"]
                urgente = dias is not None and dias <= 7
                badge   = "🚨 HOY" if dias == 0 else (f"⚠️ {dias}d" if urgente else f"📅 {dias}d")
                clase   = "exam-card exam-urgent" if urgente else "exam-card"
                st.markdown(
                    f"<div class='{clase}'><strong>{ex['materia']}</strong> <small style='color:#b4becd'>{ex['tipo']}</small> {badge}<br>"
                    f"<span style='color:#aaa; font-size:12px;'>{ex['fecha_str']}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("#### ⚔️ MATERIAS EN CURSO:")

        # Alerta de clase hoy
        hoy_nombre = DIAS_ORDEN[date.today().weekday()]
        clases_hoy = [
            m for m in mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if HORARIOS.get(m, {}).get("dia") == hoy_nombre
        ]
        if clases_hoy:
            materias_hoy_str = " · ".join(clases_hoy)
            st.markdown(
                f"<div style='background:#1a2200; border-left:4px solid #f1c40f; border-radius:6px; "
                f"padding:10px 14px; margin-bottom:10px;'>"
                f"🔥 <strong>HOY {hoy_nombre.upper()} TENÉS:</strong> {materias_hoy_str}</div>",
                unsafe_allow_html=True,
            )

        if cursando_df.empty and final_df.empty:
            st.info("No tenés materias activas. Elegí tu próxima misión en Planificar.")
        else:
            # ── Materias en Final (inscripto, esperando aprobar) ──────────
            if not final_df.empty:
                st.markdown("##### 📝 Regularizadas · final pendiente:")
                for i, row in final_df.iterrows():
                    materia  = row["Materia"]
                    tipo_c   = row["Cursada"]
                    key_ap   = f"aprobar_final_{i}_{materia}"
                    key_fex  = f"editfecha_final_{i}_{materia}"
                    conf_key = f"confdel_final_{i}_{materia}"

                    fecha_ex = str(row.get("Fecha_examen", "")).strip()
                    dias     = dias_restantes(fecha_ex) if fecha_ex and fecha_ex not in ("", "nan", "NaT", "None") else None
                    if dias is not None:
                        badge = f"⚠️ {dias}d" if dias <= 7 else f"📅 {dias}d"
                    else:
                        badge = ""

                    aplazos = pd.to_numeric(row.get("Aplazos", ""), errors="coerce")
                    aplazos_badge = (
                        f" <span style='color:#ff4b4b; font-size:12px;'>💀 x{int(aplazos)}</span>"
                        if pd.notna(aplazos) and aplazos > 0 else ""
                    )

                    st.markdown(
                        f"<div style='background:#0d1a2e; border-left:4px solid #3498db; "
                        f"border-radius:6px; padding:10px 14px; margin-bottom:4px;'>"
                        f"📝 <strong>{materia}</strong> "
                        f"<span style='color:#aaa; font-size:12px;'>[{tipo_c}] {badge}</span>{aplazos_badge}"
                        + (f"<br><span style='color:#f1c40f; font-size:12px;'>{get_horario_badge(materia)}</span>" if get_horario_badge(materia) else "")
                        + f"</div>",
                        unsafe_allow_html=True,
                    )

                    bc1, bc2, bc3, bc4, _ = st.columns([2, 1, 1, 1, 2])
                    if bc1.button("✅ Aprobé el final", key=f"apfinal_{i}", **ANCHO_COMPLETO):
                        st.session_state[key_ap]  = not st.session_state.get(key_ap, False)
                        st.session_state[key_fex] = False
                    if bc2.button("📅", key=f"fexfinal_{i}", **ANCHO_COMPLETO, help="Editar fecha de mesa de final"):
                        st.session_state[key_fex] = not st.session_state.get(key_fex, False)
                        st.session_state[key_ap]  = False
                    if bc3.button("❌", key=f"aplazo_{i}", **ANCHO_COMPLETO, help="Desaprobé el final (suma un aplazo)"):
                        mask = mascara_materia(df, usuario, materia)
                        apl_act = pd.to_numeric(row.get("Aplazos", ""), errors="coerce")
                        nuevo_apl = int(apl_act) + 1 if pd.notna(apl_act) else 1
                        df.loc[mask, "Aplazos"] = nuevo_apl
                        df.loc[mask, "Fecha_examen"] = ""   # la mesa vieja ya pasó
                        guardar_df(conn, df, usuario)
                        st.session_state["play_sound"] = "delete"
                        st.rerun()
                    _boton_borrar_confirmado(bc4, conn, df, usuario, materia,
                                             key_btn=f"delfinal_{i}", conf_key=conf_key)
                    if st.session_state.get(conf_key, False):
                        st.warning(f"⚠️ Tocá 🗑️ de nuevo para eliminar **{materia}**")

                    # Editar fecha de mesa de final (por si te la corren)
                    if st.session_state.get(key_fex, False):
                        with st.form(key=f"formfex_{i}"):
                            st.markdown(f"**📅 Mesa de final: {materia}**")
                            try:
                                fex_val = datetime.strptime(fecha_ex, "%Y-%m-%d").date()
                            except Exception:
                                fex_val = date.today()
                            nueva_fex = st.date_input("Fecha de la mesa de final:", value=fex_val)
                            if st.form_submit_button("💾 GUARDAR FECHA", **ANCHO_COMPLETO):
                                df.loc[
                                    mascara_materia(df, usuario, materia),
                                    "Fecha_examen"
                                ] = str(nueva_fex)
                                guardar_df(conn, df, usuario)
                                st.session_state[key_fex]      = False
                                st.session_state["play_sound"] = "click"
                                st.rerun()

                    if st.session_state.get(key_ap, False):
                        with st.form(key=f"formfinal_{i}"):
                            nota_input = st.number_input("Nota final (4-10):", min_value=4, max_value=10, value=7)
                            fecha_ap   = st.date_input("Fecha de aprobación:", value=date.today())
                            if st.form_submit_button("🎖️ REGISTRAR VICTORIA", **ANCHO_COMPLETO):
                                df.loc[
                                    mascara_materia(df, usuario, materia),
                                    ["Estado", "Nota", "Fecha_aprobacion", "Fecha_examen"]
                                ] = ["Aprobada", nota_input, str(fecha_ap), ""]
                                guardar_df(conn, df, usuario)
                                st.session_state[key_ap]          = False
                                st.session_state["show_confetti"] = True
                                st.rerun()

            # ── Materias cursando ─────────────────────────────────────────
            if not cursando_df.empty:
                st.markdown("##### 📘 Cursando:")
                for i, row in cursando_df.iterrows():
                    materia  = row["Materia"]
                    tipo_c   = row["Cursada"]
                    key_flag = f"aprobar_{i}_{materia}"
                    key_edit = f"editar_{i}_{materia}"
                    conf_key = f"confdel_curs_{i}_{materia}"

                    p1v = pd.to_numeric(row.get("Nota_parcial1", ""), errors="coerce")
                    p2v = pd.to_numeric(row.get("Nota_parcial2", ""), errors="coerce")
                    # Un 0 guardado significa "sin nota", no un cero real
                    p1v = p1v if pd.notna(p1v) and p1v > 0 else float("nan")
                    p2v = p2v if pd.notna(p2v) and p2v > 0 else float("nan")
                    parciales_str = ""
                    if pd.notna(p1v) or pd.notna(p2v):
                        p1_str = f"P1:{int(p1v)}" if pd.notna(p1v) else "P1:-"
                        p2_str = f"P2:{int(p2v)}" if pd.notna(p2v) else "P2:-"
                        parciales_str = f" · {p1_str} {p2_str}"

                    sin_final = materia in MATERIAS_SIN_FINAL
                    badge_tipo = "🔄" if tipo_c == "Contracursada" else "📘"
                    sin_final_badge = "<span style='color:#2ecc71; font-size:12px;'> · Sin final</span>" if sin_final else ""
                    horario_badge = get_horario_badge(materia)
                    hoy_badge = " 🔥" if dia_es_hoy(materia) else ""
                    horario_html = (
                        f"<br><span style='color:#f1c40f; font-size:12px;'>{horario_badge}{hoy_badge}</span>"
                        if horario_badge else ""
                    )

                    st.markdown(
                        f"<div style='background:#1a1c23; border-left:4px solid #f1c40f; "
                        f"border-radius:6px; padding:10px 14px; margin-bottom:4px;'>"
                        f"{badge_tipo} <strong>{materia}</strong> "
                        f"<span style='color:#aaa; font-size:12px;'>[{tipo_c}]{parciales_str}</span>"
                        f"{sin_final_badge}{horario_html}</div>",
                        unsafe_allow_html=True,
                    )

                    bc1, bc2, bc3, _ = st.columns([2, 1, 1, 2])
                    if bc1.button("📋 Terminé de cursar", key=f"mision_{i}", **ANCHO_COMPLETO):
                        st.session_state[key_flag] = not st.session_state.get(key_flag, False)
                        st.session_state[key_edit] = False
                    if bc2.button("✏️", key=f"edit_{i}", **ANCHO_COMPLETO, help="Editar parciales / fecha"):
                        st.session_state[key_edit] = not st.session_state.get(key_edit, False)
                        st.session_state[key_flag] = False
                    _boton_borrar_confirmado(bc3, conn, df, usuario, materia,
                                             key_btn=f"del_{i}", conf_key=conf_key)
                    if st.session_state.get(conf_key, False):
                        st.warning(f"⚠️ Tocá 🗑️ de nuevo para eliminar **{materia}**")

                    # Formulario: terminé de cursar → ¿tiene final?
                    if st.session_state.get(key_flag, False):
                        if sin_final:
                            # Sin final: pedir nota y aprobar directo
                            with st.form(key=f"form_{i}"):
                                st.info("✅ Esta materia no tiene final. Ingresá la nota de cursada.")
                                nota_input = st.number_input("Nota (4-10):", min_value=4, max_value=10, value=7)
                                fecha_ap   = st.date_input("Fecha de aprobación:", value=date.today())
                                if st.form_submit_button("🎖️ APROBAR", **ANCHO_COMPLETO):
                                    df.loc[
                                        mascara_materia(df, usuario, materia),
                                        ["Estado", "Nota", "Fecha_aprobacion", "Fecha_examen"]
                                    ] = ["Aprobada", nota_input, str(fecha_ap), ""]
                                    guardar_df(conn, df, usuario)
                                    st.session_state[key_flag]        = False
                                    st.session_state["show_confetti"] = True
                                    st.rerun()
                        else:
                            # Con final: preguntar si tiene o no
                            tiene_final_key = f"tiene_final_{i}"
                            st.markdown(
                                "<div style='background:#1a1200; border-left:4px solid #f1c40f; "
                                "border-radius:6px; padding:10px 14px; margin:4px 0;'>"
                                "❓ <strong>¿Esta materia tiene examen final?</strong></div>",
                                unsafe_allow_html=True,
                            )
                            col_si, col_no = st.columns(2)
                            if col_si.button("✅ Sí, tiene final", key=f"si_{i}", **ANCHO_COMPLETO):
                                df.loc[
                                    mascara_materia(df, usuario, materia),
                                    "Estado"
                                ] = "Final"
                                guardar_df(conn, df, usuario)
                                st.session_state[key_flag]     = False
                                st.session_state["play_sound"] = "finishhim"
                                st.rerun()
                            if col_no.button("❌ No, apruebo por cursada", key=f"no_{i}", **ANCHO_COMPLETO):
                                st.session_state[tiene_final_key] = "no"
                                st.session_state[key_flag]        = True
                                st.rerun()

                            if st.session_state.get(tiene_final_key) == "no":
                                with st.form(key=f"form_{i}"):
                                    st.info("✅ Aprobada por cursada. Ingresá la nota.")
                                    nota_input = st.number_input("Nota (4-10):", min_value=4, max_value=10, value=7)
                                    fecha_ap   = st.date_input("Fecha:", value=date.today())
                                    if st.form_submit_button("🎖️ APROBAR", **ANCHO_COMPLETO):
                                        df.loc[
                                            mascara_materia(df, usuario, materia),
                                            ["Estado", "Nota", "Fecha_aprobacion", "Fecha_examen"]
                                        ] = ["Aprobada", nota_input, str(fecha_ap), ""]
                                        guardar_df(conn, df, usuario)
                                        st.session_state[tiene_final_key]  = None
                                        st.session_state["show_confetti"] = True
                                        st.rerun()

                    # Formulario: editar parciales / fecha examen
                    if st.session_state.get(key_edit, False):
                        with st.form(key=f"editform_{i}"):
                            st.markdown(f"**✏️ Editar: {materia}**")
                            p1_act = pd.to_numeric(row.get("Nota_parcial1", ""), errors="coerce")
                            p2_act = pd.to_numeric(row.get("Nota_parcial2", ""), errors="coerce")
                            col_p1, col_p2 = st.columns(2)
                            p1 = col_p1.number_input("Parcial 1 (0=sin nota):", 0, 10,
                                                      int(p1_act) if pd.notna(p1_act) else 0)
                            p2 = col_p2.number_input("Parcial 2 (0=sin nota):", 0, 10,
                                                      int(p2_act) if pd.notna(p2_act) else 0)
                            fecha_ex_act = str(row.get("Fecha_examen", "")).strip()
                            try:
                                fecha_ex_val = datetime.strptime(fecha_ex_act, "%Y-%m-%d").date()
                            except Exception:
                                fecha_ex_val = None
                            fecha_ex   = st.date_input("Fecha del próximo parcial:", value=fecha_ex_val)
                            nuevo_tipo = st.selectbox(
                                "Tipo de cursada:",
                                ["Regular", "Contracursada"],
                                index=["Regular", "Contracursada"].index(tipo_c)
                                      if tipo_c in ["Regular", "Contracursada"] else 0,
                            )
                            if st.form_submit_button("💾 GUARDAR", **ANCHO_COMPLETO):
                                mask = mascara_materia(df, usuario, materia)
                                # 0 = sin nota → guardar vacío, no un cero literal
                                df.loc[mask, "Nota_parcial1"] = p1 if p1 > 0 else ""
                                df.loc[mask, "Nota_parcial2"] = p2 if p2 > 0 else ""
                                df.loc[mask, "Fecha_examen"]  = str(fecha_ex) if fecha_ex else ""
                                df.loc[mask, "Cursada"]       = nuevo_tipo
                                guardar_df(conn, df, usuario)
                                st.session_state[key_edit] = False
                                # 🎯 Headshot SOLO si el 10 es nuevo (antes no lo tenía)
                                nuevo_10 = (
                                    (p1 == 10 and (pd.isna(p1_act) or p1_act != 10)) or
                                    (p2 == 10 and (pd.isna(p2_act) or p2_act != 10))
                                )
                                st.session_state["play_sound"] = "headshot" if nuevo_10 else "click"
                                st.rerun()


def vista_grupo(df):
    st.header("👥 DESPLIEGUE POR CUATRIMESTRE REAL")
    en_curso = df[df["Estado"] == "Cursando"].copy()

    if not en_curso.empty:
        en_curso["PeriodoReal"] = en_curso.apply(
            lambda r: asignar_periodo_real(r["Materia"], r["Cursada"]), axis=1
        )
        for periodo in ["1° Cuatrimestre", "2° Cuatrimestre"]:
            st.markdown(f"<div class='cuatri-header'>{periodo}</div>", unsafe_allow_html=True)
            bloque = en_curso[en_curso["PeriodoReal"] == periodo]
            if bloque.empty:
                st.info("Sin actividad en este periodo.")
                continue
            for mat in bloque["Materia"].unique():
                soldados_data = bloque[bloque["Materia"] == mat]
                lista_nombres = [escape(f"{r['Nombre']} ({r['Cursada']})") for _, r in soldados_data.iterrows()]
                puntos_mat    = PLAN_ESTUDIOS.get(mat, {}).get("puntos", 0)
                st.markdown(
                    f"<div class='materia-card'><strong>{mat}</strong> ({puntos_mat} pts)<br>"
                    f"<span style='color:#aaa;'>🎖️ Soldados: {', '.join(lista_nombres)}</span></div>",
                    unsafe_allow_html=True,
                )
    else:
        st.warning("No hay soldados cursando actualmente.")

    st.markdown("---")
    st.markdown("#### 🏅 MATERIAS APROBADAS POR EL SQUAD")
    aprobadas_grupo = df[df["Estado"] == "Aprobada"][["Nombre", "Materia", "Nota"]].copy()
    if not aprobadas_grupo.empty:
        st.dataframe(aprobadas_grupo.sort_values(["Materia", "Nombre"]), **ANCHO_COMPLETO, hide_index=True)
    else:
        st.info("Nadie ha aprobado materias aún.")


def vista_proximas(conn, df, usuario, mis_datos, aprobadas_df):
    st.header("🧭 PLANIFICAR · PRÓXIMA MISIÓN")
    st.caption("Elegí una materia, revisá sus requisitos y explorá lo que sigue. Registrar acá no realiza una inscripción en SIU.")
    states = estados_por_materia(mis_datos)
    c_search, c_filter = st.columns([2, 1])
    query = c_search.text_input("🔎 Buscar materia", placeholder="Nombre completo o una parte", key=f"buscar_{usuario}")
    filter_name = c_filter.selectbox("Estado", ["Disponibles", "Bloqueadas", "Cursando", "Final pendiente", "Aprobadas", "Todas"], key=f"filtro_{usuario}")
    filters = {"Disponibles": "Disponible", "Bloqueadas": "Bloqueada", "Cursando": "Cursando", "Final pendiente": "Final", "Aprobadas": "Aprobada"}
    visible = [m for m in PLAN_ESTUDIOS if materia_id(query) in materia_id(m) and
               (filter_name == "Todas" or estado_materia(m, PLAN_ESTUDIOS, states) == filters[filter_name])]
    st.caption(f"{len(visible)} de {TOTAL_MATERIAS} materias · habilitación según las correlativas cargadas en el plan.")
    if not visible:
        st.info("No hay materias con esa búsqueda y filtro. Probá con Todas o borrá la búsqueda.")
        return
    selected = st.selectbox("Materia a explorar", visible, key=f"detalle_{usuario}")
    status = estado_materia(selected, PLAN_ESTUDIOS, states)
    state_label = "Regularizada · final pendiente" if status == "Final" else status
    with st.container(border=True):
        st.subheader(selected)
        info = PLAN_ESTUDIOS[selected]
        st.markdown(f"**{state_label}** · {info['puntos']} créditos · Oferta teórica: {info['periodo']}")
        st.markdown("**Requisitos para cursar**")
        missing = requisitos_pendientes(selected, PLAN_ESTUDIOS, states)
        if not info["correlativas"]:
            st.write("🔓 No tiene correlativas cargadas.")
        for requirement in info["correlativas"]:
            state = states.get(materia_id(requirement))
            badge = "✅" if state in {"Final", "Aprobada"} else "🔒"
            label = {"Final":"regularizada, final pendiente", "Aprobada":"aprobada", "Cursando":"cursando"}.get(state,"pendiente")
            st.write(f"{badge} {requirement} — {label}")
        dependents = [m for m, details in PLAN_ESTUDIOS.items() if selected in details["correlativas"]]
        if dependents:
            st.markdown("**Después de esta materia**")
            for dependent in dependents:
                others = [m for m in requisitos_pendientes(dependent, PLAN_ESTUDIOS, states) if m != selected]
                st.write(f"↗ {dependent}" + (f" · También requiere: {', '.join(others)}" if others else " · Correlativas cubiertas al regularizar esta materia"))
        if status in {"Disponible", "Bloqueada"}:
            modality = st.selectbox("Modalidad de cursada", ["Regular", "Contracursada"], key=f"modalidad_{usuario}_{materia_id(selected)}")
            conflict = get_conflicto_horario(selected, mis_datos)
            if conflict:
                st.warning(f"📅 Coincide el día con {conflict}. Verificá comisión, horario y cuatrimestre antes de agregarla.")
            allowed = status == "Disponible"
            if missing:
                st.warning("Falta regularizar: " + ", ".join(missing))
                allowed = st.checkbox("Tengo una excepción autorizada para cursarla", key=f"excepcion_{usuario}_{materia_id(selected)}")
            if st.button("⚔️ Agregar a mi cursada", key=f"cursar_{usuario}_{materia_id(selected)}", disabled=not allowed, **ANCHO_COMPLETO):
                _inscribir_materia(conn, df, usuario, selected, modality)
                st.session_state["play_sound"] = "gunshot"
                st.rerun()
        else:
            st.caption("Ya está registrada. Podés actualizar su resultado desde Mi cursada o su nota desde Mi avance → Historial.")
    st.markdown("### 🌐 MAPA DE CORRELATIVIDADES")
    if st.checkbox("Abrir mapa interactivo", key=f"abrir_mapa_{usuario}"):
        whole = st.checkbox("Mostrar el plan completo", key=f"mapa_completo_{usuario}")
        st.caption("🟢 Aprobada · 🟠 Final pendiente · 🟡 Cursando · 🔵 Disponible · ⚪ Bloqueada. Cada nodo también muestra el estado en texto.")
        html = arbol_correlativas_html(
            [m for m in PLAN_ESTUDIOS if states.get(materia_id(m)) == "Aprobada"],
            [m for m in PLAN_ESTUDIOS if states.get(materia_id(m)) == "Cursando"],
            [m for m in PLAN_ESTUDIOS if states.get(materia_id(m)) == "Final"],
            foco=None if whole else selected,
        )
        mostrar_html(html, height=740, scrolling=True)


def vista_horarios(mis_datos):
    st.header("📅 GRILLA DE HORARIOS")

    hoy_nombre = DIAS_ORDEN[date.today().weekday()]

    # Materias que el usuario cursa activamente (van a clase esta semana).
    # Las que están en "Final" ya no ocupan horario semanal.
    activas = set(mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist())
    only_mine = st.checkbox("Sólo mis materias en curso", value=True, key="horarios_personales")
    oferta = {m: h for m, h in HORARIOS.items() if not only_mine or m in activas}
    if only_mine and not oferta:
        st.info("No hay horarios cargados para tus materias activas. Desmarcá el filtro para ver la oferta disponible.")

    # ── Tarjeta de hoy ────────────────────────────────────────────────
    hoy_materias = [m for m, h in oferta.items() if h["dia"] == hoy_nombre]
    if hoy_materias:
        st.markdown(f"### 🔥 HOY — {hoy_nombre}")
        for m in hoy_materias:
            h = HORARIOS[m]
            inst = f"<br><span style='color:#aaa; font-size:12px;'>Instructor: {h['instructor']}</span>" if h["instructor"] else ""
            activa_style = "border-left:4px solid #f1c40f;" if m in activas else "border-left:4px solid #444;"
            activa_badge = " <span style='color:#f1c40f; font-size:12px;'>★ EN CURSO</span>" if m in activas else ""
            st.markdown(
                f"<div style='background:#1a1c23; {activa_style} border-radius:6px; padding:12px 16px; margin-bottom:6px;'>"
                f"<strong>{m}</strong>{activa_badge}"
                f"<br><span style='color:#3498db; font-size:12px;'>👨‍🏫 {h['docente']}</span>{inst}"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("---")

    # ── Grilla semanal completa ───────────────────────────────────────
    st.markdown("### 📋 Semana — NOCHE")

    dias_con_materias = sorted(
        set(h["dia"] for h in oferta.values()),
        key=lambda d: DIAS_ORDEN.index(d) if d in DIAS_ORDEN else 99
    )

    for dia in dias_con_materias:
        es_hoy = dia == hoy_nombre
        dia_header_color = "#f1c40f" if es_hoy else "#e0e0e0"
        hoy_tag = " 🔥" if es_hoy else ""
        st.markdown(
            f"<div style='color:{dia_header_color}; font-family:monospace; font-weight:bold; "
            f"font-size:15px; margin:18px 0 6px 0;'>{dia.upper()}{hoy_tag}</div>",
            unsafe_allow_html=True,
        )
        materias_dia = [m for m, h in oferta.items() if h["dia"] == dia]
        for m in materias_dia:
            h = HORARIOS[m]
            inst = f" · {h['instructor']}" if h["instructor"] else ""
            activa_style = "border-left:4px solid #f1c40f; background:#1e1b0e;" if m in activas else "border-left:4px solid #2c3e50; background:#1a1c23;"
            activa_badge = " <span style='color:#f1c40f; font-size:12px;'>★ EN CURSO</span>" if m in activas else ""
            comision_badge = f"<span style='color:#b4becd; font-size:12px;'> [{h['comision']}]</span>"
            st.markdown(
                f"<div style='{activa_style} border-radius:6px; padding:10px 14px; margin-bottom:4px;'>"
                f"<strong>{m}</strong>{comision_badge}{activa_badge}"
                f"<br><span style='color:#3498db; font-size:12px;'>👨‍🏫 {h['docente']}{inst}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


def vista_historial(conn, df, usuario, mis_datos):
    st.header("✅ REGISTRO DE COMBATE")
    cols_mostrar = [c for c in ["Materia", "Estado", "Nota", "Nota_parcial1", "Nota_parcial2",
                                 "Cursada", "Aplazos", "Fecha_aprobacion", "Fecha_examen"] if c in mis_datos.columns]
    display = mis_datos[cols_mostrar].sort_values("Estado").copy()
    for col in ["Nota", "Nota_parcial1", "Nota_parcial2", "Aplazos"]:
        if col in display:
            display[col] = pd.to_numeric(display[col], errors="coerce")
    st.dataframe(display, **ANCHO_COMPLETO, hide_index=True)

    # Editar materia aprobada
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    if aprobadas_list:
        st.markdown("---")
        st.markdown("#### ✏️ CORREGIR MATERIA APROBADA")
        mat_sel = st.selectbox("Materia aprobada:", aprobadas_list, key=f"hist_materia_{usuario}")
        actual = mis_datos[(mis_datos["Materia"] == mat_sel) & (mis_datos["Estado"] == "Aprobada")].iloc[0]
        nota_actual = pd.to_numeric(actual.get("Nota", ""), errors="coerce")
        nota_actual = int(nota_actual) if pd.notna(nota_actual) and 4 <= nota_actual <= 10 else 7
        fecha_actual = fecha_existente(actual.get("Fecha_aprobacion", ""))
        if fecha_actual is None:
            st.caption("Esta aprobación no tiene fecha: completala sólo si la conocés.")
        with st.form(f"editar_aprobada_{usuario}_{materia_id(mat_sel)}"):
            nueva_nota = st.number_input("Nueva nota (4-10):", min_value=4, max_value=10, value=nota_actual)
            nueva_fecha = st.date_input("Fecha de aprobación:", value=fecha_actual)
            if st.form_submit_button("💾 ACTUALIZAR"):
                mask = mascara_materia(df, usuario, mat_sel)
                df.loc[mask, "Nota"]             = nueva_nota
                df.loc[mask, "Fecha_aprobacion"] = str(nueva_fecha) if nueva_fecha else ""
                guardar_df(conn, df, usuario)
                st.session_state["play_sound"] = "click"
                st.success(f"✅ {mat_sel} actualizada.")
                st.rerun()

    # ── 🩺 CHEQUEO DE INTEGRIDAD ──────────────────────────────────────────
    # Detecta filas que rompen la lógica: estado inválido (fantasmas), materia
    # que no matchea el plan (typo de nombre) o duplicados de la misma materia.
    planes_norm = {_norm_nombre(m): m for m in PLAN_ESTUDIOS}

    filas_estado_malo = mis_datos[~mis_datos["Estado"].isin(ESTADOS_VALIDOS)]
    filas_huerfanas   = mis_datos[~mis_datos["Materia"].apply(lambda m: _norm_nombre(m) in planes_norm)]
    dup_materias      = mis_datos["Materia"].value_counts()
    dup_materias      = dup_materias[dup_materias > 1].index.tolist()

    hay_problemas = (not filas_estado_malo.empty) or (not filas_huerfanas.empty) or bool(dup_materias)

    if hay_problemas:
        st.markdown("---")
        st.markdown("#### 🩺 CHEQUEO DE INTEGRIDAD")
        st.warning("Encontré filas que pueden estar rompiendo la lógica (materias que no aparecen en PRÓX., correlativas que no cierran, etc.). Revisalas y borrá las que sobren.")

        problematicas = pd.concat([filas_estado_malo, filas_huerfanas]).drop_duplicates()
        for i, row in problematicas.iterrows():
            materia = row["Materia"]
            estado  = row["Estado"]
            motivos = []
            if estado not in ESTADOS_VALIDOS:
                motivos.append(f"estado inválido: '{estado or '(vacío)'}'")
            if _norm_nombre(materia) not in planes_norm:
                motivos.append("nombre no coincide con el plan")
            c1i, c2i = st.columns([4, 1])
            c1i.markdown(
                f"<div class='warning-card'><strong>{materia or '(sin materia)'}</strong> "
                f"<span style='color:#aaa; font-size:12px;'>— {', '.join(motivos)}</span></div>",
                unsafe_allow_html=True,
            )
            if c2i.button("🗑️ Borrar", key=f"fixdel_{i}", **ANCHO_COMPLETO):
                idx_drop = df[(df["Nombre"] == usuario)
                              & (df["Materia"] == materia)
                              & (df["Estado"] == estado)].index
                guardar_df(conn, df.drop(idx_drop).reset_index(drop=True), usuario)
                st.session_state["play_sound"] = "delete"
                st.rerun()

        if dup_materias:
            st.markdown(
                f"<div style='color:#e67e22; font-size:13px; margin-top:8px;'>"
                f"⚠️ Materias duplicadas (más de una fila): {', '.join(dup_materias)}. "
                f"Revisá las filas originales antes de editar: las métricas cuentan cada materia una sola vez.</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("---")
        st.caption("🩺 Integridad OK — todas tus filas tienen estado y nombre válidos.")


def vista_estadisticas(df, usuario, mis_datos, aprobadas_df, cursando_df, final_df,
                        puntos_logrados, promedio_simple, promedio_pond):
    st.header("📊 MI AVANCE · CAMPAÑA")
    c1, c2, c3 = st.columns(3)
    c1.metric("Aprobadas", f"{len(aprobadas_df)}/{TOTAL_MATERIAS}")
    c2.metric("Créditos", f"{puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA}")
    c3.metric("Promedio", f"{promedio_simple:.2f}" if pd.notna(promedio_simple) else "Sin notas")
    st.caption(f"Cursando: {len(cursando_df)} · Final pendiente: {len(final_df)} · Promedio ponderado por créditos: {promedio_pond:.2f}")
    st.markdown("### 🧩 AVANCE POR ÁREA")
    st.caption("Porcentaje de materias aprobadas en cada área. No mide tu desempeño ni pondera créditos.")
    st.plotly_chart(grafico_radar(aprobadas_df), **ANCHO_COMPLETO, config={"displayModeBar": False, "staticPlot": True})
    for area, subjects in AREAS.items():
        count = sum(m in aprobadas_df["Materia"].values for m in subjects)
        st.write(f"**{area}:** {count}/{len(subjects)} · {count/len(subjects):.0%}")
    st.markdown("### 📈 PROGRESO EN EL TIEMPO")
    chart = grafico_progreso_tiempo(aprobadas_df)
    dated = pd.to_datetime(aprobadas_df["Fecha_aprobacion"], errors="coerce").notna().sum()
    st.caption(f"La curva incluye {dated} de {len(aprobadas_df)} aprobadas. Las que no tienen fecha siguen contando en tu avance total.")
    if chart is not None:
        st.plotly_chart(chart, **ANCHO_COMPLETO, config={"displayModeBar": False})
    else:
        st.info("Completá las fechas conocidas en Historial para ver la evolución.")
    egreso = estimar_egreso(aprobadas_df)
    if egreso:
        with st.expander("🎓 Escenario de egreso según tu historial"):
            st.write(f"Si mantuvieras el ritmo de tus aprobaciones con fecha: **{egreso}**.")
            st.caption("Es una orientación: no contempla oferta, carga de cursada ni requisitos académicos. Usa sólo aprobaciones fechadas para medir el ritmo.")
    st.markdown("### 🎖️ MEDALLAS DE CAMPAÑA")
    columns = st.columns(3)
    for i, (emoji, name, description, unlocked) in enumerate(calcular_logros(mis_datos, aprobadas_df, puntos_logrados)):
        css = "logro-card logro-on" if unlocked else "logro-card logro-off"
        columns[i % 3].markdown(f"<div class='{css}'><span style='font-size:26px'>{emoji}</span><br><strong>{name}</strong><br>{description}<br>{'DESBLOQUEADA' if unlocked else 'POR DESBLOQUEAR'}</div>", unsafe_allow_html=True)
    st.markdown("### 📅 EXÁMENES REGISTRADOS")
    exams = _get_examenes_proximos(mis_datos)
    if not exams:
        st.info("No hay exámenes cargados. Agregá una fecha desde Mi cursada.")
    for exam in exams:
        days = exam["dias"]
        badge = "Fecha inválida" if days is None else (f"Hace {abs(days)} días" if days < 0 else "HOY" if days == 0 else f"En {days} días")
        st.write(f"{exam['tipo']} · **{exam['materia']}** · {exam['fecha_str']} · {badge}")


# ─────────────────────────────────────────────
# 6. CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(ttl=60)
def cargar_datos(_conn) -> pd.DataFrame | None:
    try:
        df = normalizar_tabla(_conn.read(worksheet=0, ttl=0))
        df = asegurar_columnas(df)
        df = normalizar_estado(df)
        return df
    except Exception:
        st.error("❌ ERROR CRÍTICO DE CONEXIÓN")
        st.warning(
            "Google Sheets no responde. "
            "Revisá la configuración de conexión y los permisos de la planilla. "
            "No se guardó ningún cambio."
        )
        return None


# ─────────────────────────────────────────────
# 7. MAIN
# ─────────────────────────────────────────────
def main():
    st.session_state.setdefault("show_confetti", False)
    st.session_state.setdefault("play_sound", None)
    try:
        conn = get_connection()
    except Exception:
        st.error("No pude abrir la conexión. Revisá su configuración o usá demo.py para probar sin datos reales.")
        st.stop()
    # Freeze the edit baseline until an explicit refresh or confirmed save.
    # A shared-cache expiry must not silently replace it while a form is open.
    df = st.session_state.get("_session_df")
    if df is None:
        df = cargar_datos(conn)
        if df is not None:
            st.session_state["_session_df"] = df.copy(deep=True)
    else:
        df = df.copy(deep=True)
    if df is None:
        if st.button("🔄 Volver a cargar datos"):
            cargar_datos.clear()
            st.rerun()
        st.stop()
    st.session_state["_base_df"] = df.copy(deep=True)
    st.markdown("<h1 class='retro-font' style='text-align:center;font-size:24px'>SQUAD COMMAND 2026</h1>", unsafe_allow_html=True)
    st.markdown("<div class='arcade-signal'>🎮 CÍRCULO ROJO · Tu carrera, misión por misión.</div>", unsafe_allow_html=True)
    with st.expander("⚙️ CABINA ARCADE · Sonido y efectos"):
        st.checkbox("🔊 Sonidos", value=True, key="sonidos")
        st.slider("Volumen", 0, 100, 45, key="volumen")
        st.checkbox("✨ Efectos y personajes animados", value=True, key="efectos")
        st.caption("Las animaciones respetan la preferencia de movimiento reducido del dispositivo. El navegador puede requerir un toque para habilitar audio.")
        if st.button("▶ Probar sonido"):
            if st.session_state.sonidos:
                mostrar_html(sound_html("click"), height=48)
    if not st.session_state.efectos:
        st.markdown("<style>.stApp::before{display:none}.arcade-signal{animation:none}</style>", unsafe_allow_html=True)
    notice = st.session_state.pop("_save_notice", None)
    if notice:
        st.success(notice)
    if st.session_state.show_confetti:
        if st.session_state.efectos:
            mostrar_html(confetti_html(), height=160)
        if st.session_state.sonidos:
            mostrar_html(sound_html("missioncomplete"), height=48)
        st.session_state.show_confetti = False
    if st.session_state.play_sound:
        if st.session_state.sonidos:
            mostrar_html(sound_html(st.session_state.play_sound), height=48)
        st.session_state.play_sound = None
    usuarios = sorted(df["Nombre"].dropna().unique().tolist())
    usuario = st.selectbox("👤 Elegí tu soldado", ["Seleccionar..."] + usuarios, key="soldado")
    if st.button("🔄 Actualizar datos", help="Traer los últimos cambios guardados"):
        cargar_datos.clear()
        st.session_state.pop("_session_df", None)
        st.rerun()
    # ➕ Alta de nuevo soldado (sin tocar el Sheet a mano)
    with st.expander("➕ NUEVO RECLUTA"):
        with st.form("form_nuevo_recluta"):
            nombre_nuevo = st.text_input("Nombre del soldado:")
            materia_ini  = st.selectbox("Primera materia:", list(PLAN_ESTUDIOS.keys()))
            estado_ini   = st.selectbox("Estado inicial:", ["Cursando", "Aprobada"])
            nota_ini     = st.number_input("Nota (solo si ya la aprobó):", 0, 10, 0)
            if st.form_submit_button("🎖️ ALISTAR", **ANCHO_COMPLETO):
                nombre_limpio = nombre_nuevo.strip()
                if not nombre_limpio:
                    st.error("⚠️ Ingresá un nombre.")
                elif nombre_limpio in usuarios:
                    st.error(f"⚠️ **{nombre_limpio}** ya está alistado.")
                else:
                    nueva = pd.DataFrame([{
                        "Nombre": nombre_limpio, "Materia": materia_ini,
                        "Estado": estado_ini, "Cursada": "Regular",
                        "Nota": nota_ini if (estado_ini == "Aprobada" and nota_ini >= 4) else "",
                        "Nota_parcial1": "", "Nota_parcial2": "",
                        "Fecha_aprobacion": str(date.today()) if estado_ini == "Aprobada" else "",
                        "Fecha_examen": "", "Aplazos": "",
                    }])
                    guardar_df(conn, pd.concat([df, nueva], ignore_index=True), nombre_limpio)
                    st.session_state["play_sound"] = "gunshot"
                    st.success(f"🎖️ ¡Bienvenido al squad, {nombre_limpio}!")
                    st.rerun()

    if usuario == "Seleccionar...":
        st.info("Seleccioná tu soldado para continuar la campaña, o alistá uno nuevo.")
        return
    labels = {"Inicio":"⚔️ Mi cursada", "Proximas":"🧭 Planificar", "Stats":"📊 Mi avance", "Grupo":"👥 Squad"}
    menu = st.radio("Panel de misión", list(labels), format_func=labels.get, key="pantalla", horizontal=True, label_visibility="collapsed")
    st.session_state.menu = menu
    st.divider()
    raw_mine = df[df["Nombre"] == usuario].copy()
    mine = vista_academica(raw_mine, PLAN_ESTUDIOS)
    aprobadas = mine[mine["Estado"] == "Aprobada"]
    cursando = mine[mine["Estado"] == "Cursando"]
    final = mine[mine["Estado"] == "Final"]
    points = sum(PLAN_ESTUDIOS[m]["puntos"] for m in aprobadas["Materia"])
    average = pd.to_numeric(aprobadas["Nota"], errors="coerce").dropna().mean() if not aprobadas.empty else 0.0
    weighted = calcular_promedio_ponderado(aprobadas)
    if menu == "Inicio":
        section = st.radio("Mi cursada", ["Materias", "Horarios"], key="seccion_cursada", horizontal=True, label_visibility="collapsed")
        if section == "Horarios":
            vista_horarios(mine)
        else:
            vista_inicio(conn, df, usuario, mine, aprobadas, cursando, final, points, average, weighted)
    elif menu == "Proximas":
        vista_proximas(conn, df, usuario, raw_mine, aprobadas)
    elif menu == "Stats":
        section = st.radio("Mi avance", ["Resumen", "Historial"], key="seccion_avance", horizontal=True, label_visibility="collapsed")
        if section == "Historial":
            vista_historial(conn, df, usuario, raw_mine)
        else:
            vista_estadisticas(df, usuario, mine, aprobadas, cursando, final, points, average, weighted)
    elif menu == "Grupo":
        vista_grupo(df)


if __name__ == "__main__":
    main()
