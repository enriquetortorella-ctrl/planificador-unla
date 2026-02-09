import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_lottie import st_lottie
import requests
from datetime import datetime, date

# --- 1. CONFIGURACIÓN Y ESTILO SUPER MODERNO ---
st.set_page_config(page_title="Círculo Rojo v2.6", page_icon="🔴", layout="wide")

def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        /* Tarjetas de KPI */
        .kpi-card {
            background-color: #1e1e26;
            padding: 20px;
            border-radius: 15px;
            border-left: 5px solid #800000;
            box-shadow: 2px 2px 15px rgba(0,0,0,0.3);
            text-align: center;
        }
        .kpi-value { font-size: 30px; font-weight: bold; color: #ffffff; }
        .kpi-label { font-size: 14px; color: #a0a0a0; text-transform: uppercase; }
        
        /* Botones laterales */
        .stButton>button {
            border-radius: 12px;
            background-color: #262730;
            color: white;
            border: 1px solid #3e3e4e;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #800000;
            border: 1px solid #ff4b4b;
            transform: scale(1.02);
        }
        </style>
        """, unsafe_allow_html=True)

local_css()

# --- 2. CARGA DE ANIMACIONES (LOTTIE) ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# URLs de animaciones gratuitas de LottieFiles
ANIMACIONES = {
    "Lagarto 🦎": "https://assets10.lottiefiles.com/packages/lf20_hy4per6f.json", # Un dinosaurio/lagarto simpático
    "Dragón 🐉": "https://assets8.lottiefiles.com/packages/lf20_5mjt84fc.json",   # Dragón volando
    "Robot 🤖": "https://assets10.lottiefiles.com/private_files/lf30_igp67uub.json" # Robot saludando
}

# --- 3. DATOS ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS = 42

# (Mantenemos el diccionario PLAN_ESTUDIOS que ya tienes)
# ... [Insertar aquí el diccionario PLAN_ESTUDIOS del mensaje anterior] ...

# --- 4. CONEXIÓN ---
def get_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        return df, conn
    except:
        return pd.DataFrame(columns=["Nombre", "Materia", "Estado", "Modalidad"]), None

# --- 5. INTERFAZ ---
def main():
    df, conn = get_data()
    
    with st.sidebar:
        st.markdown("<h1 style='color:#800000; text-align:center;'>🔴 CÍRCULO ROJO</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 Perfil de Usuario", LISTA_CHICOS)
        st.markdown("---")
        
        if "menu" not in st.session_state: st.session_state.menu = "Inicio"
        
        if st.button("🏠 Inicio"): st.session_state.menu = "Inicio"
        if st.button("📊 Mi Progreso"): st.session_state.menu = "Progreso"
        if st.button("📝 Inscripción"): st.session_state.menu = "Inscripcion"
        if st.button("📚 Biblioteca"): st.session_state.menu = "Biblioteca"
        
        st.markdown("---")
        st.caption("v2.6 Premium UI")

    if usuario == "Seleccionar...":
        st.header("Bienvenido al Planificador")
        st.info("Selecciona tu nombre para ver tu evolución animada.")
        return

    # Cálculos
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = len(mis_datos[mis_datos["Estado"] == "Aprobada"])
    cursando = len(mis_datos[mis_datos["Estado"] == "Cursando"])
    restantes = TOTAL_MATERIAS - aprobadas
    porcentaje = int((aprobadas / TOTAL_MATERIAS) * 100)

    # --- HEADER MODERNO CON KPIs ---
    st.markdown(f"## ¡Hola, {usuario}! ✨")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Aprobadas</div><div class='kpi-value'>{aprobadas}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Cursando</div><div class='kpi-value'>{cursando}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Restantes</div><div class='kpi-value'>{restantes}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avance</div><div class='kpi-value'>{porcentaje}%</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- CONTENIDO ---
    menu = st.session_state.menu

    if menu == "Inicio":
        col_anim, col_info = st.columns([1, 1.5])
        
        with col_anim:
            st.subheader("Tu Compañero Dinámico")
            seleccion_mascota = st.selectbox("Elegí tu avatar:", list(ANIMACIONES.keys()))
            lottie_anim = load_lottieurl(ANIMACIONES[seleccion_mascota])
            
            if lottie_anim:
                # Ajustamos la velocidad según el progreso
                velocidad = 1 + (porcentaje / 100)
                st_lottie(lottie_anim, speed=velocidad, height=300, key="avatar")
            
            st.markdown(f"<p style='text-align:center;'>Nivel de evolución: <b>{porcentaje // 20 + 1} / 5</b></p>", unsafe_allow_html=True)

        with col_info:
            st.subheader("📌 Materias en curso")
            materias_actuales = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if materias_actuales:
                for m in materias_actuales:
                    st.markdown(f"✅ **{m}**")
            else:
                st.write("No tienes materias activas.")

    # (Aquí irían las demás secciones: Progreso, Inscripción, etc. con la misma lógica que ya teníamos)

if __name__ == "__main__":
    main()
