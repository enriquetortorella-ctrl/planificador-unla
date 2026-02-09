import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_lottie import st_lottie
import requests
from datetime import datetime, date

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Círculo Rojo v2.6", page_icon="🔴", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .kpi-card {
        background-color: #1e1e26;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #800000;
        margin-bottom: 10px;
    }
    .kpi-value { font-size: 30px; font-weight: bold; color: #ffffff; }
    .kpi-label { font-size: 14px; color: #a0a0a0; text-transform: uppercase; }
    
    .stButton>button {
        border-radius: 12px;
        transition: all 0.3s;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #800000 !important;
        color: white !important;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE APOYO ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

# --- 3. DATOS Y CALENDARIO ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS = 42

ANIMACIONES = {
    "Lagarto 🦎": "https://assets10.lottiefiles.com/packages/lf20_hy4per6f.json",
    "Dragón 🐉": "https://assets8.lottiefiles.com/packages/lf20_5mjt84fc.json",
    "Robot 🤖": "https://assets10.lottiefiles.com/private_files/lf30_igp67uub.json"
}

# Plan de estudios (Resumido para el ejemplo, agrega las tuyas aquí)
PLAN_ESTUDIOS = {
    "Taller de Producción de Textos": {"anio": 1, "correlativas": []},
    "Introducción a la Matemática": {"anio": 1, "correlativas": []},
    "Contabilidad": {"anio": 1, "correlativas": []},
    "Historia Económica Contemporánea": {"anio": 1, "correlativas": []},
    "Elementos de Matemática": {"anio": 1, "correlativas": ["Introducción a la Matemática"]},
    # ... (Agregá el resto de la lista que tenías)
}

# --- 4. APP PRINCIPAL ---
def main():
    # Conexión
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("Error de conexión con Google Sheets.")
        return

    with st.sidebar:
        st.markdown("<h1 style='color:#800000; text-align:center;'>🔴 CÍRCULO ROJO</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 Perfil", LISTA_CHICOS)
        st.markdown("---")
        
        if "menu" not in st.session_state: st.session_state.menu = "Inicio"
        if st.button("🏠 Inicio"): st.session_state.menu = "Inicio"
        if st.button("📊 Mi Progreso"): st.session_state.menu = "Progreso"
        if st.button("📝 Inscripción"): st.session_state.menu = "Inscripcion"
        
    if usuario == "Seleccionar...":
        st.title("Planificador UNLa 2026")
        st.info("Elegí tu nombre a la izquierda para ver tu avance.")
        return

    # Cálculos de KPI
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = len(mis_datos[mis_datos["Estado"] == "Aprobada"])
    cursando = len(mis_datos[mis_datos["Estado"] == "Cursando"])
    progreso = aprobadas / TOTAL_MATERIAS

    # Header con KPIs
    st.markdown(f"## ¡Hola, {usuario}! ✨")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Aprobadas</div><div class='kpi-value'>{aprobadas}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Cursando</div><div class='kpi-value'>{cursando}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Restantes</div><div class='kpi-value'>{TOTAL_MATERIAS - aprobadas}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avance</div><div class='kpi-value'>{int(progreso*100)}%</div></div>", unsafe_allow_html=True)
    
    st.progress(progreso)

    # Contenido Dinámico
    if st.session_state.menu == "Inicio":
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.subheader("Tu Avatar")
            mascota = st.selectbox("Elegí tu compañero:", list(ANIMACIONES.keys()))
            anim = load_lottieurl(ANIMACIONES[mascota])
            if anim:
                st_lottie(anim, height=250, key="lottie_main", speed=1 + progreso)
            else:
                st.write("🐱 (Animación cargando...)")
        
        with col2:
            st.subheader("📌 Estado Actual")
            actuales = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if actuales:
                for m in actuales: st.success(f"📖 {m}")
            else:
                st.info("No hay materias en curso.")

    elif st.session_state.menu == "Progreso":
        st.subheader("Actualizar Historial")
        # Aquí va tu lógica de multiselect para aprobadas...

if __name__ == "__main__":
    main()

    # (Aquí irían las demás secciones: Progreso, Inscripción, etc. con la misma lógica que ya teníamos)

if __name__ == "__main__":
    main()

