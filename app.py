import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
import os
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(page_title="Círculo Rojo - SQUAD", page_icon="🔫", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

    .stApp { background-color: #0b0d11; color: #e0e0e0; }

    .retro-font {
        font-family: 'Press Start 2P', cursive;
        color: #f1c40f;
        text-shadow: 2px 2px #000;
    }
    .hp-bar-text {
        font-family: 'Press Start 2P', cursive;
        font-size: 10px;
        color: #ff4b4b;
        margin-top: 5px;
    }
    .hp-bar-text-blue {
        font-family: 'Press Start 2P', cursive;
        font-size: 10px;
        color: #3498db;
        margin-top: 5px;
    }
    .cuatri-header {
        font-family: 'Press Start 2P', cursive;
        color: #3498db;
        font-size: 16px;
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
    [data-testid="stMetricValue"] {
        font-family: 'Press Start 2P', cursive;
        font-size: 18px !important;
    }

    /* ── RESPONSIVE MOBILE ── */
    @media (max-width: 640px) {
        /* Columnas principales en mobile: apiladas */
        [data-testid="column"] { min-width: 100% !important; }

        /* Navegación: texto más chico */
        .stButton > button { font-size: 11px !important; padding: 6px 4px !important; }

        /* Header más chico */
        .retro-font { font-size: 14px !important; }

        /* Barras de progreso: texto más chico */
        .hp-bar-text, .hp-bar-text-blue { font-size: 8px !important; }
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
}

# Áreas para radar chart
AREAS = {
    "Matemática":     ["Matemática I", "Matemática II", "Cálculo Financiero", "Estadística"],
    "Económica":      ["Introducción a Economía Empresarial", "Historia Económica Contemporánea",
                       "Empresa, Economía y Sociedad", "Microeconomía I", "Microeconomía II", "Macroeconomía"],
    "Administración": ["Organización y Gestión", "Comercialización", "Costos Empresariales",
                       "Control de Gestión", "Taller de Práctica Preprofesional",
                       "Seminario de Pensamiento Nacional Latinoamericano",
                       "Seminario de Justicia y Derechos Humanos"],
    "Jurídica":       ["Derecho Comercial"],
    "Comunicación":   ["Taller de Comunicación y Producción de Textos", "Contabilidad"],
}

CREDITOS_TOTAL_TECNICATURA  = 120
CREDITOS_TOTAL_LICENCIATURA = 240
TOTAL_MATERIAS = len(PLAN_ESTUDIOS)

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
}


# ─────────────────────────────────────────────
# 3. HELPERS
# ─────────────────────────────────────────────
def get_avatar_path(usuario: str, n_aprobadas: int) -> str:
    char  = SQUAD_MAP.get(usuario, "Marco")
    nivel = 1 if n_aprobadas <= 10 else 2 if n_aprobadas <= 20 else 3 if n_aprobadas <= 30 else 4
    return os.path.join("assets", f"{char}_{nivel}.gif")


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


def guardar_df(conn, df: pd.DataFrame):
    # 🛡️ FUSIBLE DE SEGURIDAD: Si el DF está vacío, no toca el Sheet
    if df.empty or len(df.columns) < 2:
        st.error("🚨 ATENCIÓN: Se intentó guardar una base de datos vacía. Operación cancelada para proteger el archivo.")
        return
    try:
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        conn.update(worksheet=0, data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"⚠️ Error al sincronizar con Google Sheets: {e}")


def asegurar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "Nota": "", "Cursada": "Regular", "Estado": "Cursando",
        "Nota_parcial1": "", "Nota_parcial2": "",
        "Fecha_aprobacion": "", "Fecha_examen": "",
        "Tiene_final": "",
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
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
    hoy = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][
        __import__("datetime").date.today().weekday()
    ]
    return h["dia"] == hoy


def get_conflicto_horario(materia_nueva: str, mis_datos: pd.DataFrame) -> str | None:
    """
    Dado una materia que se quiere cursar, devuelve el nombre de la materia
    que ya está activa (Cursando/Final) en el mismo día, o None si no hay conflicto.
    """
    h_nueva = HORARIOS.get(materia_nueva)
    if not h_nueva:
        return None
    dia_nueva = h_nueva["dia"]
    activas = mis_datos[mis_datos["Estado"].isin(["Cursando", "Final"])]["Materia"].tolist()
    for m_activa in activas:
        h_activa = HORARIOS.get(m_activa)
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
    if "Fecha_aprobacion" not in aprobadas_df.columns:
        return None
    fechas = pd.to_datetime(aprobadas_df["Fecha_aprobacion"], errors="coerce").dropna()
    if len(fechas) < 2:
        return None
    fechas_sorted = fechas.sort_values()
    delta_dias    = (fechas_sorted.iloc[-1] - fechas_sorted.iloc[0]).days
    if delta_dias <= 0:
        return None
    ritmo         = len(aprobadas_df) / delta_dias
    materias_rest = TOTAL_MATERIAS - len(aprobadas_df)
    dias_rest     = materias_rest / ritmo
    fecha_est     = date.today() + timedelta(days=dias_rest)
    return fecha_est.strftime("%B %Y")


def _base_audio_script() -> str:
    """Script base con Web Audio API para todos los sonidos del juego."""
    return r"""
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


def sound_html(sound: str) -> str:
    """
    Inyecta el script base + reproduce el sonido indicado.
    sound: "gunshot" | "click" | "delete" | "headshot" | "finishhim" | "missioncomplete"
    """
    fn_map = {
        "gunshot":        "playGunshot()",
        "click":          "playClick()",
        "delete":         "playDelete()",
        "headshot":       "playHeadshot()",
        "finishhim":      "playFinishHim()",
        "missioncomplete":"playMissionComplete()",
    }
    call = fn_map.get(sound, "playClick()")
    return f"""
    {_base_audio_script()}
    <script>(function(){{ {call} }})();</script>
    """


def confetti_html() -> str:
    """Confetti + MISSION COMPLETE al aprobar una materia."""
    return f"""
    {_base_audio_script()}
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
    (function() {{
        playMissionComplete();
        var duration = 3500;
        var animationEnd = Date.now() + duration;
        var defaults = {{ startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 }};
        function randomInRange(min, max) {{ return Math.random() * (max - min) + min; }}
        var interval = setInterval(function() {{
            var timeLeft = animationEnd - Date.now();
            if (timeLeft <= 0) return clearInterval(interval);
            var particleCount = 50 * (timeLeft / duration);
            confetti(Object.assign({{}}, defaults, {{
                particleCount,
                origin: {{ x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }},
                colors: ['#f1c40f','#ff4b4b','#3498db','#2ecc71','#fff']
            }}));
            confetti(Object.assign({{}}, defaults, {{
                particleCount,
                origin: {{ x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }},
                colors: ['#f1c40f','#ff4b4b','#3498db','#2ecc71','#fff']
            }}));
        }}, 250);
    }})();
    </script>
    """


def _get_examenes_proximos(mis_datos: pd.DataFrame) -> list:
    resultado = []
    for _, row in mis_datos[mis_datos["Estado"].isin(["Cursando", "Aprobada"])].iterrows():
        fecha_str = str(row.get("Fecha_examen", "")).strip()
        if not fecha_str or fecha_str in ("", "nan", "NaT", "None"):
            continue
        dias = dias_restantes(fecha_str)
        p1 = pd.to_numeric(row.get("Nota_parcial1", 0), errors="coerce") or 0
        tipo = "🏆 Final" if p1 > 0 else "🎯 Parcial"
        resultado.append({"materia": row["Materia"], "fecha_str": fecha_str, "dias": dias, "tipo": tipo})
    resultado.sort(key=lambda x: (x["dias"] is None, x["dias"] or 9999))
    return resultado


# ─────────────────────────────────────────────
# 4. GRÁFICOS
# ─────────────────────────────────────────────
def arbol_correlativas_html(aprobadas: list, cursando: list) -> str:
    """
    Genera un grafo interactivo con vis.js:
    - Zoom y pan con touch (funciona en mobile)
    - Layout jerárquico de izquierda a derecha
    - Nodos con color según estado
    - Tooltip con nombre completo, créditos y correlativas
    """
    import json as _json

    nodes = []
    edges = []

    for idx, (m, info) in enumerate(PLAN_ESTUDIOS.items()):
        if m in aprobadas:
            color = {"background": "#2ecc71", "border": "#27ae60", "highlight": {"background": "#58d68d", "border": "#27ae60"}}
            font_color = "#0b0d11"
        elif m in cursando:
            color = {"background": "#f1c40f", "border": "#d4ac0d", "highlight": {"background": "#f4d03f", "border": "#d4ac0d"}}
            font_color = "#0b0d11"
        elif all(c in aprobadas for c in info["correlativas"]):
            color = {"background": "#3498db", "border": "#2980b9", "highlight": {"background": "#5dade2", "border": "#2980b9"}}
            font_color = "#ffffff"
        else:
            color = {"background": "#2c2f36", "border": "#555", "highlight": {"background": "#3d4147", "border": "#777"}}
            font_color = "#aaaaaa"

        pts  = info["puntos"]
        cors = ", ".join(info["correlativas"]) or "Ninguna"
        # Etiqueta corta para el nodo
        palabras = m.split()
        label = " ".join(palabras[:3]) + ("\n" + " ".join(palabras[3:6]) if len(palabras) > 3 else "")

        nodes.append({
            "id":    idx,
            "label": label,
            "title": f"<b>{m}</b><br>Créditos: {pts}<br>Requiere: {cors}",
            "color": color,
            "font":  {"color": font_color, "size": 13, "face": "monospace"},
            "shape": "box",
            "margin": 8,
            "shadow": True,
        })

    materia_idx = {m: i for i, m in enumerate(PLAN_ESTUDIOS.keys())}
    for m, info in PLAN_ESTUDIOS.items():
        for cor in info["correlativas"]:
            edges.append({
                "from":   materia_idx[cor],
                "to":     materia_idx[m],
                "arrows": "to",
                "color":  {"color": "#555", "highlight": "#f1c40f"},
                "width":  2,
                "smooth": {"type": "cubicBezier", "forceDirection": "horizontal"},
            })

    nodes_json = _json.dumps(nodes)
    edges_json = _json.dumps(edges)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0b0d11; overflow: hidden; }}
  #graph {{
    width: 100%;
    height: 600px;
    background: #0b0d11;
    border: 1px solid #333;
    border-radius: 8px;
  }}
  .vis-tooltip {{
    background: #1a1c23 !important;
    border: 1px solid #444 !important;
    color: #e0e0e0 !important;
    font-family: monospace !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    max-width: 250px !important;
  }}
  #hint {{
    position: absolute;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    color: #555;
    font-size: 11px;
    font-family: monospace;
    pointer-events: none;
    white-space: nowrap;
  }}
</style>
</head>
<body>
<div style="position:relative;">
  <div id="graph"></div>
  <div id="hint">📱 Pellizco para zoom · Arrastrá para mover</div>
</div>
<script>
  var nodes = new vis.DataSet({nodes_json});
  var edges = new vis.DataSet({edges_json});

  var options = {{
    layout: {{
      hierarchical: {{
        enabled: true,
        direction: "LR",
        sortMethod: "directed",
        levelSeparation: 220,
        nodeSpacing: 90,
        treeSpacing: 150,
        blockShifting: true,
        edgeMinimization: true,
        parentCentralization: true,
      }}
    }},
    physics: {{ enabled: false }},
    interaction: {{
      dragNodes: false,
      dragView: true,
      zoomView: true,
      hover: true,
      tooltipDelay: 100,
      navigationButtons: false,
      keyboard: false,
    }},
    nodes: {{
      borderWidth: 2,
      borderWidthSelected: 3,
    }},
    edges: {{
      selectionWidth: 3,
    }},
  }};

  var container = document.getElementById("graph");
  var network   = new vis.Network(container, {{ nodes: nodes, edges: edges }}, options);

  // Ajuste automático al cargar
  network.once("stabilized", function() {{
    network.fit({{ animation: {{ duration: 600, easingFunction: "easeInOutQuad" }} }});
  }});
  network.fit();
</script>
</body>
</html>
"""


def grafico_radar(aprobadas_df: pd.DataFrame) -> go.Figure:
    categorias = list(AREAS.keys())
    valores = []
    for area, mats in AREAS.items():
        aprobadas_area = sum(1 for m in mats if m in aprobadas_df["Materia"].values)
        valores.append(round(aprobadas_area / len(mats) * 100, 1) if mats else 0)

    fig = go.Figure(go.Scatterpolar(
        r=valores + [valores[0]],
        theta=categorias + [categorias[0]],
        fill="toself",
        fillcolor="rgba(52, 152, 219, 0.25)",
        line=dict(color="#3498db", width=2),
        marker=dict(color="#f1c40f", size=8),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1c23",
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color="#aaa", size=9),
                            gridcolor="#333", linecolor="#333"),
            angularaxis=dict(tickfont=dict(color="#e0e0e0", size=11),
                             gridcolor="#333", linecolor="#333"),
        ),
        paper_bgcolor="#0b0d11",
        font=dict(color="#e0e0e0"),
        height=380,
        margin=dict(l=60, r=60, t=20, b=20),
        showlegend=False,
    )
    return fig


def grafico_progreso_tiempo(aprobadas_df: pd.DataFrame):
    if "Fecha_aprobacion" not in aprobadas_df.columns:
        return None
    df_f = aprobadas_df.copy()
    df_f["Fecha_aprobacion"] = pd.to_datetime(df_f["Fecha_aprobacion"], errors="coerce")
    df_f = df_f.dropna(subset=["Fecha_aprobacion"]).sort_values("Fecha_aprobacion")
    if df_f.empty:
        return None
    df_f["Acumuladas"] = range(1, len(df_f) + 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f["Fecha_aprobacion"], y=df_f["Acumuladas"],
        mode="lines+markers",
        line=dict(color="#f1c40f", width=3),
        marker=dict(color="#ff4b4b", size=8),
        hovertemplate="%{x|%d/%m/%Y}<br>Materias aprobadas: %{y}<extra></extra>",
    ))
    fig.add_hline(y=TOTAL_MATERIAS, line_dash="dot", line_color="#2ecc71",
                  annotation_text="Meta total", annotation_font_color="#2ecc71")
    fig.update_layout(
        paper_bgcolor="#0b0d11", plot_bgcolor="#0b0d11",
        font=dict(color="#e0e0e0"),
        xaxis=dict(title="Fecha", gridcolor="#222", linecolor="#444"),
        yaxis=dict(title="Materias aprobadas", gridcolor="#222", linecolor="#444"),
        height=320,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    return fig


# ─────────────────────────────────────────────
# 5. VISTAS
# ─────────────────────────────────────────────

def vista_inicio(conn, df, usuario, mis_datos, aprobadas_df, cursando_df, final_df,
                 puntos_logrados, promedio_simple, promedio_pond):

    col_av, col_cur = st.columns([1, 3])

    with col_av:
        img_path = get_avatar_path(usuario, len(aprobadas_df))
        if os.path.exists(img_path):
            st.image(img_path, width=120)
        else:
            st.markdown("🎮")

        # Métricas en mini-tarjetas compactas
        st.markdown(
            f"""<div style='display:flex; flex-wrap:wrap; gap:8px; margin:8px 0;'>
                <div style='background:#1a1c23; border-radius:6px; padding:8px 12px; flex:1; min-width:70px; text-align:center;'>
                    <div style='color:#aaa; font-size:9px; font-family:monospace;'>PUNTOS</div>
                    <div style='color:#f1c40f; font-size:16px; font-weight:bold;'>{puntos_logrados}</div>
                </div>
                <div style='background:#1a1c23; border-radius:6px; padding:8px 12px; flex:1; min-width:70px; text-align:center;'>
                    <div style='color:#aaa; font-size:9px; font-family:monospace;'>PROM.</div>
                    <div style='color:#3498db; font-size:16px; font-weight:bold;'>{promedio_simple:.2f}</div>
                </div>
                <div style='background:#1a1c23; border-radius:6px; padding:8px 12px; flex:1; min-width:70px; text-align:center;'>
                    <div style='color:#aaa; font-size:9px; font-family:monospace;'>POND.</div>
                    <div style='color:#2ecc71; font-size:16px; font-weight:bold;'>{promedio_pond:.2f}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        egreso = estimar_egreso(aprobadas_df)
        if egreso:
            st.markdown(
                f"<p style='font-size:11px; color:#aaa;'>🎓 Estimado egreso: "
                f"<strong style='color:#2ecc71'>{egreso}</strong></p>",
                unsafe_allow_html=True,
            )

        st.link_button("📂 DRIVE SQUAD",  "https://drive.google.com/drive/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs", use_container_width=True)
        st.link_button("🏛️ SIU GUARANÍ", "https://estudiantes.unla.edu.ar/autogestion3w/acceso",                     use_container_width=True)
        st.link_button("💻 CAMPUS UNLA", "https://campus.unla.edu.ar/aulas/login/index.php",                          use_container_width=True)
        st.link_button("🧠 ESTUDIO IA",  "https://estudio-ia.streamlit.app/",                                         use_container_width=True)

    with col_cur:
        st.markdown("#### 🏆 PROGRESO POR CRÉDITOS:")
        prog_tec = min(puntos_logrados / CREDITOS_TOTAL_TECNICATURA, 1.0)
        st.progress(prog_tec)
        st.markdown(
            f"<p class='hp-bar-text-blue'>TECNICATURA: {puntos_logrados}/{CREDITOS_TOTAL_TECNICATURA} pts ({int(prog_tec*100)}%)</p>",
            unsafe_allow_html=True,
        )
        prog_lic = min(puntos_logrados / CREDITOS_TOTAL_LICENCIATURA, 1.0)
        st.progress(prog_lic)
        st.markdown(
            f"<p class='hp-bar-text'>LICENCIATURA: {puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA} pts ({int(prog_lic*100)}%)</p>",
            unsafe_allow_html=True,
        )

        # Próximos exámenes en inicio (máx. 3)
        examenes = _get_examenes_proximos(mis_datos)
        if examenes:
            st.markdown("---")
            st.markdown("#### 📅 PRÓXIMOS EXÁMENES:")
            for ex in examenes[:3]:
                dias    = ex["dias"]
                urgente = dias is not None and dias <= 7
                badge   = f"⚠️ {dias}d" if urgente else (f"📅 {dias}d" if dias is not None else "")
                clase   = "exam-card exam-urgent" if urgente else "exam-card"
                st.markdown(
                    f"<div class='{clase}'><strong>{ex['materia']}</strong> <small style='color:#888'>{ex['tipo']}</small> {badge}<br>"
                    f"<span style='color:#aaa; font-size:12px;'>{ex['fecha_str']}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("#### ⚔️ MATERIAS EN CURSO:")

        # Alerta de clase hoy
        import datetime as _dt
        hoy_nombre = DIAS_ORDEN[_dt.date.today().weekday()]
        clases_hoy = [
            m for m in mis_datos[mis_datos["Estado"].isin(["Cursando","Final"])]["Materia"].tolist()
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

        if cursando_df.empty and mis_datos[mis_datos["Estado"] == "Final"].empty:
            st.info("No estás cursando ninguna materia. ¡Inscribite en PRÓX.!")
        else:
            # ── Materias en Final (inscripto, esperando aprobar) ──────────
            final_df = mis_datos[mis_datos["Estado"] == "Final"]
            if not final_df.empty:
                st.markdown("##### 📝 Inscripto a final:")
                for i, row in final_df.iterrows():
                    materia  = row["Materia"]
                    tipo_c   = row["Cursada"]
                    key_ap   = f"aprobar_final_{i}_{materia}"

                    fecha_ex = str(row.get("Fecha_examen", "")).strip()
                    dias     = dias_restantes(fecha_ex) if fecha_ex and fecha_ex not in ("", "nan", "NaT", "None") else None
                    if dias is not None:
                        badge = f"⚠️ {dias}d" if dias <= 7 else f"📅 {dias}d"
                    else:
                        badge = ""

                    st.markdown(
                        f"<div style='background:#0d1a2e; border-left:4px solid #3498db; "
                        f"border-radius:6px; padding:10px 14px; margin-bottom:4px;'>"
                        f"📝 <strong>{materia}</strong> "
                        f"<span style='color:#aaa; font-size:11px;'>[{tipo_c}] {badge}</span>"
                        + (f"<br><span style='color:#f1c40f; font-size:10px;'>{get_horario_badge(materia)}</span>" if get_horario_badge(materia) else "")
                        + f"</div>",
                        unsafe_allow_html=True,
                    )

                    bc1, bc2, _ = st.columns([2, 1, 4])
                    if bc1.button("✅ Aprobé el final", key=f"apfinal_{i}", use_container_width=True):
                        st.session_state[key_ap] = not st.session_state.get(key_ap, False)
                    if bc2.button("🗑️", key=f"delfinal_{i}", use_container_width=True):
                        idx_drop = df[(df["Nombre"] == usuario) & (df["Materia"] == materia)].index
                        guardar_df(conn, df.drop(idx_drop).reset_index(drop=True))
                        st.session_state["play_sound"] = "delete"
                        st.rerun()

                    if st.session_state.get(key_ap, False):
                        with st.form(key=f"formfinal_{i}"):
                            nota_input = st.number_input("Nota final (4-10):", min_value=4, max_value=10, value=7)
                            fecha_ap   = st.date_input("Fecha de aprobación:", value=date.today())
                            if st.form_submit_button("🎖️ REGISTRAR VICTORIA", use_container_width=True):
                                df.loc[
                                    (df["Nombre"] == usuario) & (df["Materia"] == materia),
                                    ["Estado", "Nota", "Fecha_aprobacion"]
                                ] = ["Aprobada", nota_input, str(fecha_ap)]
                                guardar_df(conn, df)
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

                    p1v = pd.to_numeric(row.get("Nota_parcial1", ""), errors="coerce")
                    p2v = pd.to_numeric(row.get("Nota_parcial2", ""), errors="coerce")
                    parciales_str = ""
                    if pd.notna(p1v) or pd.notna(p2v):
                        p1_str = f"P1:{int(p1v)}" if pd.notna(p1v) else "P1:-"
                        p2_str = f"P2:{int(p2v)}" if pd.notna(p2v) else "P2:-"
                        parciales_str = f" · {p1_str} {p2_str}"

                    sin_final = materia in MATERIAS_SIN_FINAL
                    badge_tipo = "🔄" if tipo_c == "Contracursada" else "📘"
                    sin_final_badge = "<span style='color:#2ecc71; font-size:10px;'> · Sin final</span>" if sin_final else ""
                    horario_badge = get_horario_badge(materia)
                    hoy_badge = " 🔥" if dia_es_hoy(materia) else ""
                    horario_html = (
                        f"<br><span style='color:#f1c40f; font-size:10px;'>{horario_badge}{hoy_badge}</span>"
                        if horario_badge else ""
                    )

                    st.markdown(
                        f"<div style='background:#1a1c23; border-left:4px solid #f1c40f; "
                        f"border-radius:6px; padding:10px 14px; margin-bottom:4px;'>"
                        f"{badge_tipo} <strong>{materia}</strong> "
                        f"<span style='color:#aaa; font-size:11px;'>[{tipo_c}]{parciales_str}</span>"
                        f"{sin_final_badge}{horario_html}</div>",
                        unsafe_allow_html=True,
                    )

                    bc1, bc2, bc3, _ = st.columns([2, 1, 1, 2])
                    if bc1.button("📋 Terminé de cursar", key=f"mision_{i}", use_container_width=True):
                        st.session_state[key_flag] = not st.session_state.get(key_flag, False)
                        st.session_state[key_edit] = False
                    if bc2.button("✏️", key=f"edit_{i}", use_container_width=True, help="Editar parciales / fecha"):
                        st.session_state[key_edit] = not st.session_state.get(key_edit, False)
                        st.session_state[key_flag] = False
                    if bc3.button("🗑️", key=f"del_{i}", use_container_width=True, help="Eliminar"):
                        idx_drop = df[(df["Nombre"] == usuario) & (df["Materia"] == materia)].index
                        guardar_df(conn, df.drop(idx_drop).reset_index(drop=True))
                        st.session_state["play_sound"] = "delete"
                        st.rerun()

                    # Formulario: terminé de cursar → ¿tiene final?
                    if st.session_state.get(key_flag, False):
                        if sin_final:
                            # Sin final: pedir nota y aprobar directo
                            with st.form(key=f"form_{i}"):
                                st.info("✅ Esta materia no tiene final. Ingresá la nota de cursada.")
                                nota_input = st.number_input("Nota (4-10):", min_value=4, max_value=10, value=7)
                                fecha_ap   = st.date_input("Fecha de aprobación:", value=date.today())
                                if st.form_submit_button("🎖️ APROBAR", use_container_width=True):
                                    df.loc[
                                        (df["Nombre"] == usuario) & (df["Materia"] == materia),
                                        ["Estado", "Nota", "Fecha_aprobacion"]
                                    ] = ["Aprobada", nota_input, str(fecha_ap)]
                                    guardar_df(conn, df)
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
                            if col_si.button("✅ Sí, tiene final", key=f"si_{i}", use_container_width=True):
                                df.loc[
                                    (df["Nombre"] == usuario) & (df["Materia"] == materia),
                                    "Estado"
                                ] = "Final"
                                guardar_df(conn, df)
                                st.session_state[key_flag]     = False
                                st.session_state["play_sound"] = "finishhim"
                                st.rerun()
                            if col_no.button("❌ No, apruebo por cursada", key=f"no_{i}", use_container_width=True):
                                st.session_state[tiene_final_key] = "no"
                                st.session_state[key_flag]        = False
                                st.rerun()

                            if st.session_state.get(tiene_final_key) == "no":
                                with st.form(key=f"form_{i}"):
                                    st.info("✅ Aprobada por cursada. Ingresá la nota.")
                                    nota_input = st.number_input("Nota (4-10):", min_value=4, max_value=10, value=7)
                                    fecha_ap   = st.date_input("Fecha:", value=date.today())
                                    if st.form_submit_button("🎖️ APROBAR", use_container_width=True):
                                        df.loc[
                                            (df["Nombre"] == usuario) & (df["Materia"] == materia),
                                            ["Estado", "Nota", "Fecha_aprobacion"]
                                        ] = ["Aprobada", nota_input, str(fecha_ap)]
                                        guardar_df(conn, df)
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
                                fecha_ex_val = date.today()
                            fecha_ex   = st.date_input("Fecha de examen final:", value=fecha_ex_val)
                            nuevo_tipo = st.selectbox(
                                "Tipo de cursada:",
                                ["Regular", "Contracursada"],
                                index=["Regular", "Contracursada"].index(tipo_c)
                                      if tipo_c in ["Regular", "Contracursada"] else 0,
                            )
                            if st.form_submit_button("💾 GUARDAR", use_container_width=True):
                                mask = (df["Nombre"] == usuario) & (df["Materia"] == materia)
                                df.loc[mask, "Nota_parcial1"] = p1 if p1 > 0 else 0
                                df.loc[mask, "Nota_parcial2"] = p2 if p2 > 0 else 0
                                df.loc[mask, "Fecha_examen"]  = str(fecha_ex)
                                df.loc[mask, "Cursada"]       = nuevo_tipo
                                guardar_df(conn, df)
                                st.session_state[key_edit] = False
                                # Headshot si algún parcial es 10
                                if p1 == 10 or p2 == 10:
                                    st.session_state["play_sound"] = "headshot"
                                else:
                                    st.session_state["play_sound"] = "click"
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
                lista_nombres = [f"{r['Nombre']} ({r['Cursada']})" for _, r in soldados_data.iterrows()]
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
        st.dataframe(aprobadas_grupo.sort_values(["Materia", "Nombre"]), use_container_width=True, hide_index=True)
    else:
        st.info("Nadie ha aprobado materias aún.")


def vista_proximas(conn, df, usuario, mis_datos, aprobadas_df):
    st.header("📝 PRÓXIMOS OBJETIVOS")
    ya_registradas = mis_datos["Materia"].tolist()
    aprobadas      = aprobadas_df["Materia"].tolist()

    disponibles = [m for m, info in PLAN_ESTUDIOS.items()
                   if m not in ya_registradas and all(c in aprobadas for c in info["correlativas"])]
    bloqueadas  = [m for m, info in PLAN_ESTUDIOS.items()
                   if m not in ya_registradas and not all(c in aprobadas for c in info["correlativas"])]

    if disponibles:
        st.markdown("##### 🔓 Disponibles para cursar:")
        for d in disponibles:
            h = HORARIOS.get(d)
            horario_str = ""
            if h:
                inst = f" · {h['instructor']}" if h["instructor"] else ""
                horario_str = f" · 📅 {h['dia']} NOCHE · {h['docente']}{inst}"

            conflicto = get_conflicto_horario(d, mis_datos)

            c1, c2, c3 = st.columns([3, 1, 1])
            c1.success(f"**{d}** ({PLAN_ESTUDIOS[d]['puntos']} pts){horario_str}")

            tipo_key = f"tipo_{d}"
            if tipo_key not in st.session_state:
                st.session_state[tipo_key] = "Regular"
            st.session_state[tipo_key] = c2.selectbox(
                "Modalidad:", ["Regular", "Contracursada"], key=f"sel_{d}",
                index=["Regular", "Contracursada"].index(st.session_state[tipo_key]),
            )

            if conflicto:
                c3.button("⚔️ CURSAR", key=f"in_{d}", disabled=True, use_container_width=True)
                st.markdown(
                    f"<div style='background:#1a0d0d; border-left:4px solid #ff4b4b; "
                    f"border-radius:6px; padding:8px 12px; margin:-6px 0 8px 0; font-size:12px;'>"
                    f"⚠️ <strong>Conflicto de horario</strong> — "
                    f"Ya estás cursando <strong>{conflicto}</strong> el mismo día "
                    f"({HORARIOS[conflicto]['dia']})</div>",
                    unsafe_allow_html=True,
                )
            else:
                if c3.button("⚔️ CURSAR", key=f"in_{d}", use_container_width=True):
                    nueva = pd.DataFrame([{
                        "Nombre": usuario, "Materia": d, "Estado": "Cursando",
                        "Cursada": st.session_state[tipo_key],
                        "Nota": "", "Nota_parcial1": "", "Nota_parcial2": "",
                        "Fecha_aprobacion": "", "Fecha_examen": "",
                    }])
                    guardar_df(conn, pd.concat([df, nueva], ignore_index=True))
                    st.session_state["play_sound"] = "gunshot"
                    st.rerun()

    if bloqueadas:
        st.markdown("---")
        st.markdown("##### 🔒 Bloqueadas (faltan correlativas):")
        for b in bloqueadas:
            faltan = [c for c in PLAN_ESTUDIOS[b]["correlativas"] if c not in aprobadas]
            st.markdown(
                f"<div class='warning-card'><strong>{b}</strong> — falta: {', '.join(faltan)}</div>",
                unsafe_allow_html=True,
            )


def vista_horarios(mis_datos):
    st.header("📅 GRILLA DE HORARIOS")

    import datetime as _dt
    hoy_idx  = _dt.date.today().weekday()
    hoy_nombre = DIAS_ORDEN[hoy_idx] if hoy_idx < 7 else ""

    # Materias que el usuario tiene activas (cursando o en final)
    activas = set(mis_datos[mis_datos["Estado"].isin(["Cursando", "Final"])]["Materia"].tolist())

    # ── Tarjeta de hoy ────────────────────────────────────────────────
    hoy_materias = [m for m, h in HORARIOS.items() if h["dia"] == hoy_nombre]
    if hoy_materias:
        st.markdown(f"### 🔥 HOY — {hoy_nombre}")
        for m in hoy_materias:
            h = HORARIOS[m]
            inst = f"<br><span style='color:#aaa; font-size:11px;'>Instructor: {h['instructor']}</span>" if h["instructor"] else ""
            activa_style = "border-left:4px solid #f1c40f;" if m in activas else "border-left:4px solid #444;"
            activa_badge = " <span style='color:#f1c40f; font-size:10px;'>★ EN CURSO</span>" if m in activas else ""
            st.markdown(
                f"<div style='background:#1a1c23; {activa_style} border-radius:6px; padding:12px 16px; margin-bottom:6px;'>"
                f"<strong>{m}</strong>{activa_badge}"
                f"<br><span style='color:#3498db; font-size:12px;'>👨‍🏫 {h['docente']}</span>{inst}"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("---")

    # ── Grilla semanal completa ───────────────────────────────────────
    st.markdown("### 📋 Semana completa — NOCHE")

    dias_con_materias = sorted(
        set(h["dia"] for h in HORARIOS.values()),
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
        materias_dia = [m for m, h in HORARIOS.items() if h["dia"] == dia]
        for m in materias_dia:
            h = HORARIOS[m]
            inst = f" · {h['instructor']}" if h["instructor"] else ""
            activa_style = "border-left:4px solid #f1c40f; background:#1e1b0e;" if m in activas else "border-left:4px solid #2c3e50; background:#1a1c23;"
            activa_badge = " <span style='color:#f1c40f; font-size:10px;'>★ EN CURSO</span>" if m in activas else ""
            comision_badge = f"<span style='color:#666; font-size:10px;'> [{h['comision']}]</span>"
            st.markdown(
                f"<div style='{activa_style} border-radius:6px; padding:10px 14px; margin-bottom:4px;'>"
                f"<strong>{m}</strong>{comision_badge}{activa_badge}"
                f"<br><span style='color:#3498db; font-size:11px;'>👨‍🏫 {h['docente']}{inst}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


def vista_historial(conn, df, usuario, mis_datos):
    st.header("✅ REGISTRO DE COMBATE")
    cols_mostrar = [c for c in ["Materia", "Estado", "Nota", "Nota_parcial1", "Nota_parcial2",
                                 "Cursada", "Fecha_aprobacion", "Fecha_examen"] if c in mis_datos.columns]
    st.dataframe(mis_datos[cols_mostrar].sort_values("Estado"), use_container_width=True, hide_index=True)

    # Editar materia aprobada
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    if aprobadas_list:
        st.markdown("---")
        st.markdown("#### ✏️ CORREGIR MATERIA APROBADA")
        with st.form("editar_aprobada"):
            mat_sel     = st.selectbox("Materia:", aprobadas_list)
            nueva_nota  = st.number_input("Nueva nota (4-10):", min_value=4, max_value=10, value=7)
            nueva_fecha = st.date_input("Fecha de aprobación:", value=date.today())
            if st.form_submit_button("💾 ACTUALIZAR"):
                mask = (df["Nombre"] == usuario) & (df["Materia"] == mat_sel)
                df.loc[mask, "Nota"]             = nueva_nota
                df.loc[mask, "Fecha_aprobacion"] = str(nueva_fecha)
                guardar_df(conn, df)
                st.session_state["play_sound"] = "click"
                st.success(f"✅ {mat_sel} actualizada.")
                st.rerun()


def vista_estadisticas(df, usuario, mis_datos, aprobadas_df, cursando_df, final_df,
                        puntos_logrados, promedio_simple, promedio_pond):
    st.header("📊 ANÁLISIS DE CAMPAÑA")

    # Métricas resumen
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Aprobadas",  len(aprobadas_df))
    c2.metric("Cursando",   len(cursando_df))
    c3.metric("En final",   len(final_df))
    c4.metric("Pendientes", TOTAL_MATERIAS - len(aprobadas_df) - len(cursando_df) - len(final_df))
    c5.metric("Créditos",   f"{puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA}")

    egreso = estimar_egreso(aprobadas_df)
    if egreso:
        st.info(f"🎓 A tu ritmo actual, terminarías la carrera aproximadamente en **{egreso}**.")
    else:
        st.info("💡 Registrá fechas de aprobación en INICIO para estimar cuándo terminás la carrera.")

    st.markdown("---")

    # Progreso en el tiempo
    st.markdown("#### 📈 PROGRESO EN EL TIEMPO")
    fig_tiempo = grafico_progreso_tiempo(aprobadas_df)
    if fig_tiempo:
        st.plotly_chart(fig_tiempo, use_container_width=True)
    else:
        st.info("💡 Registrá fechas de aprobación para ver tu curva de progreso.")

    st.markdown("---")

    # Radar chart
    st.markdown("#### 🕸️ FORTALEZA POR ÁREA")
    col_r, col_r2 = st.columns([2, 1])
    with col_r:
        st.plotly_chart(grafico_radar(aprobadas_df), use_container_width=True)
    with col_r2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        for area, mats in AREAS.items():
            aprobadas_area = sum(1 for m in mats if m in aprobadas_df["Materia"].values)
            pct = int(aprobadas_area / len(mats) * 100) if mats else 0
            st.markdown(f"**{area}**: {aprobadas_area}/{len(mats)} ({pct}%)")

    st.markdown("---")

    # Árbol de correlativas
    st.markdown("#### 🌐 ÁRBOL DE CORRELATIVAS")
    st.markdown(
        "<div style='display:flex; gap:20px; flex-wrap:wrap; margin-bottom:10px; font-size:13px;'>"
        "<span>🟢 Aprobada</span><span>🟡 Cursando</span>"
        "<span>🔵 Disponible</span><span>⚫ Bloqueada</span></div>",
        unsafe_allow_html=True,
    )
    html_grafo = arbol_correlativas_html(
        aprobadas_df["Materia"].tolist(),
        cursando_df["Materia"].tolist(),
    )
    st.components.v1.html(html_grafo, height=630, scrolling=False)

    st.markdown("---")

    # Calendario de exámenes
    st.markdown("#### 📅 CALENDARIO DE EXÁMENES")
    examenes = _get_examenes_proximos(mis_datos)
    if examenes:
        for ex in examenes:
            dias = ex["dias"]
            if dias is None:
                badge = "📅 fecha inválida"
            elif dias < 0:
                badge = f"⏰ hace {abs(dias)}d"
            elif dias == 0:
                badge = "🚨 HOY"
            elif dias <= 7:
                badge = f"⚠️ en {dias}d"
            else:
                badge = f"📅 en {dias}d"
            urgente = dias is not None and dias <= 7
            clase   = "exam-card exam-urgent" if urgente else "exam-card"
            st.markdown(
                f"<div class='{clase}'>"
                f"<strong>{ex['materia']}</strong> <small style='color:#888'>{ex['tipo']}</small> — {ex['fecha_str']} {badge}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No tenés exámenes cargados. Editá una materia en INICIO (✏️) para agregar fechas.")


# ─────────────────────────────────────────────
# 6. CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(ttl=60)
def cargar_datos(_conn) -> pd.DataFrame | None:
    try:
        df = _conn.read(worksheet=0, ttl=0)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        df = asegurar_columnas(df)
        df = normalizar_estado(df)
        return df
    except Exception as e:
        st.error("❌ ERROR CRÍTICO DE CONEXIÓN")
        st.warning(
            "Google Sheets no responde. "
            "Verificá que el archivo esté compartido con el Service Account como 'Editor'.\n\n"
            f"Detalle: `{e}`"
        )
        return None


# ─────────────────────────────────────────────
# 7. MAIN
# ─────────────────────────────────────────────
def main():
    if "menu" not in st.session_state:
        st.session_state.menu = "Inicio"
    if "show_confetti" not in st.session_state:
        st.session_state.show_confetti = False
    if "play_sound" not in st.session_state:
        st.session_state.play_sound = None

    conn = get_connection()
    df   = cargar_datos(conn)
    if df is None:
        st.stop()

    # MISSION COMPLETE + confetti al aprobar materia
    if st.session_state.show_confetti:
        st.components.v1.html(confetti_html(), height=0)
        st.session_state.show_confetti = False

    # Otros sonidos: disparo, headshot, finishhim, delete, click
    if st.session_state.play_sound:
        st.components.v1.html(sound_html(st.session_state.play_sound), height=0)
        st.session_state.play_sound = None

    # Header
    st.markdown(
        "<h1 class='retro-font' style='text-align:center; font-size:24px;'>SQUAD COMMAND 2026</h1>",
        unsafe_allow_html=True,
    )

    usuarios = sorted(df["Nombre"].dropna().unique().tolist())
    usuario  = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + usuarios, label_visibility="collapsed")
    if usuario == "Seleccionar...":
        return

    # Navegación — 6 secciones
    nav_cols = st.columns(6)
    menus = [
        ("🏠 INICIO",    "Inicio"),
        ("📝 PRÓX.",     "Proximas"),
        ("✅ HIST.",     "Historial"),
        ("👥 GRUPO",    "Grupo"),
        ("📅 HORA.",    "Horarios"),
        ("📊 STATS",    "Stats"),
    ]
    for col, (label, key) in zip(nav_cols, menus):
        if col.button(label, use_container_width=True):
            st.session_state.menu = key
            st.rerun()

    st.markdown("---")

    # Datos del usuario
    mis_datos    = df[df["Nombre"] == usuario].copy()
    aprobadas_df = mis_datos[mis_datos["Estado"] == "Aprobada"]
    cursando_df  = mis_datos[mis_datos["Estado"] == "Cursando"]
    final_df     = mis_datos[mis_datos["Estado"] == "Final"]

    puntos_logrados = sum(PLAN_ESTUDIOS.get(m, {}).get("puntos", 0) for m in aprobadas_df["Materia"])
    promedio_simple = (pd.to_numeric(aprobadas_df["Nota"], errors="coerce").dropna().mean()
                       if not aprobadas_df.empty else 0.0)
    promedio_pond   = calcular_promedio_ponderado(aprobadas_df)

    # Despacho de vistas
    menu = st.session_state.menu

    if menu == "Inicio":
        vista_inicio(conn, df, usuario, mis_datos, aprobadas_df, cursando_df, final_df,
                     puntos_logrados, promedio_simple, promedio_pond)
    elif menu == "Grupo":
        vista_grupo(df)
    elif menu == "Proximas":
        vista_proximas(conn, df, usuario, mis_datos, aprobadas_df)
    elif menu == "Historial":
        vista_historial(conn, df, usuario, mis_datos)
    elif menu == "Horarios":
        vista_horarios(mis_datos)
    elif menu == "Stats":
        vista_estadisticas(df, usuario, mis_datos, aprobadas_df, cursando_df, final_df,
                           puntos_logrados, promedio_simple, promedio_pond)


if __name__ == "__main__":
    main()

