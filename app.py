import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_lottie import st_lottie
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Círculo Rojo v2.7", page_icon="🔴", layout="wide")

# Estilos CSS PRO
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e1117; }
    .kpi-card {
        background-color: #1e1e26;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #800000;
        margin-bottom: 15px;
        text-align: center;
    }
    .kpi-value { font-size: 32px; font-weight: bold; color: #ffffff; }
    .kpi-label { font-size: 14px; color: #a0a0a0; text-transform: uppercase; }
    .stButton>button { border-radius: 12px; height: 3em; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background-color: #800000 !important; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARGA DE ANIMACIONES ---
@st.cache_data(ttl=3600)
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

# Enlaces actualizados y súper estables
ANIMACIONES = {
    "Lagarto 🦎": "https://assets1.lottiefiles.com/packages/lf20_hy4per6f.json",
    "Robot 🤖": "https://assets10.lottiefiles.com/private_files/lf30_igp67uub.json",
    "Dragón 🐉": "https://assets8.lottiefiles.com/packages/lf20_5mjt84fc.json"
}

# --- 3. DATOS ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS = 42

# --- 4. APP ---
def main():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("⚠️ Error de conexión.")
        return

    with st.sidebar:
        st.markdown("<h1 style='color:#800000; text-align:center;'>🔴 CÍRCULO ROJO</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 ¿Quién sos?", LISTA_CHICOS, key="user_sel")
        st.markdown("---")
        if "menu" not in st.session_state: st.session_state.menu = "Inicio"
        if st.button("🏠 Inicio"): st.session_state.menu = "Inicio"
        if st.button("📊 Mi Historial"): st.session_state.menu = "Historial"

    if usuario == "Seleccionar...":
        st.title("Planificador 2026")
        st.info("Elegí tu nombre para ver tu progreso.")
        return

    # Cálculos
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = len(mis_datos[mis_datos["Estado"] == "Aprobada"])
    cursando = len(mis_datos[mis_datos["Estado"] == "Cursando"])
    progreso = aprobadas / TOTAL_MATERIAS

    st.markdown(f"## ¡Hola, {usuario}! 👋")
    
    # KPIs MODERNOS (Cambiado 'Finales' por 'Materias')
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Materias Aprobadas</div><div class='kpi-value'>{aprobadas}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Cursando</div><div class='kpi-value'>{cursando}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Restantes</div><div class='kpi-value'>{TOTAL_MATERIAS - aprobadas}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avance Total</div><div class='kpi-value'>{int(progreso*100)}%</div></div>", unsafe_allow_html=True)
    
    st.progress(progreso)

    if st.session_state.menu == "Inicio":
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.subheader("Tu Avatar")
            mascota = st.selectbox("Elegí tu compañero:", list(ANIMACIONES.keys()), key="masc_sel")
            anim = load_lottieurl(ANIMACIONES[mascota])
            if anim:
                st_lottie(anim, height=280, key=f"lottie_{mascota}", speed=1 + progreso)
            else:
                # Respaldo visual si internet falla
                st.markdown(f"<h1 style='font-size: 150px; text-align: center;'>{mascota[-2:]}</h1>", unsafe_allow_html=True)
                st.caption("Cargando animación completa...")
        
        with col2:
            st.subheader("📌 Cursando ahora")
            actuales = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if actuales:
                for m in actuales: st.success(f"📖 {m}")
            else:
                st.info("Sin cursadas activas.")

if __name__ == "__main__":
    main()
