import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_lottie import st_lottie
import requests
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Círculo Rojo UNLa", page_icon="🔴", layout="wide")

# Estilos CSS de alta fidelidad
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
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .kpi-value { font-size: 32px; font-weight: bold; color: #ffffff; }
    .kpi-label { font-size: 14px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; }
    
    .stButton>button {
        border-radius: 12px;
        height: 3.2em;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #800000 !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(128,0,0,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARGA DE ANIMACIONES (MEJORADA) ---
@st.cache_data(ttl=3600)
def load_lottieurl(url: str):
    try:
        # Añadimos un header para evitar bloqueos
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

# --- 3. DATOS Y CONSTANTES ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS = 42

# Usamos links directos de LottieFiles estables
ANIMACIONES = {
    "Robot 🤖": "https://assets10.lottiefiles.com/private_files/lf30_igp67uub.json",
    "Lagarto 🦎": "https://assets1.lottiefiles.com/packages/lf20_hy4per6f.json",
    "Dragón 🐉": "https://assets8.lottiefiles.com/packages/lf20_5mjt84fc.json"
}

# Plan de estudios completo
PLAN_ESTUDIOS = {
    "Taller de Producción de Textos": {"anio": 1, "correlativas": []},
    "Introducción a la Matemática": {"anio": 1, "correlativas": []},
    "Contabilidad": {"anio": 1, "correlativas": []},
    "Historia Económica Contemporánea": {"anio": 1, "correlativas": []},
    "Elementos de Matemática": {"anio": 1, "correlativas": ["Introducción a la Matemática"]},
    "Organización y Gestión": {"anio": 1, "correlativas": []},
    "Economía y Sociedad": {"anio": 1, "correlativas": ["Historia Económica Contemporánea"]},
    "Microeconomía": {"anio": 2, "correlativas": ["Historia Económica Contemporánea", "Introducción a la Matemática"]},
    "Derecho Comercial": {"anio": 2, "correlativas": ["Organización y Gestión"]},
    "Cálculo Financiero y Est. Aplicado": {"anio": 2, "correlativas": ["Elementos de Matemática"]},
    "Costos Empresariales": {"anio": 2, "correlativas": ["Elementos de Matemática", "Organización y Gestión"]},
    "Derecho Tributario": {"anio": 2, "correlativas": ["Derecho Comercial"]},
    "Macroeconomía": {"anio": 2, "correlativas": ["Economía y Sociedad"]},
    "Org. de la Producción y Tecnología": {"anio": 3, "correlativas": ["Costos Empresariales"]},
    "Derecho del Trabajo y Seg. Social": {"anio": 3, "correlativas": ["Derecho Tributario"]},
    "Comercialización": {"anio": 3, "correlativas": ["Costos Empresariales", "Macroeconomía"]},
    "Control de Gestión": {"anio": 3, "correlativas": ["Costos Empresariales"]},
    "Macroeconomía y Pol. Económica": {"anio": 3, "correlativas": ["Macroeconomía"]},
    "Comercio Exterior y Ec. Int.": {"anio": 3, "correlativas": ["Macroeconomía y Pol. Económica"]},
    "Plan de Negocios": {"anio": 3, "correlativas": ["Control de Gestión", "Comercialización"]},
    "Financiamiento": {"anio": 3, "correlativas": ["Comercialización"]},
    "Taller de Integración I": {"anio": 3, "correlativas": ["Comercialización"]},
    "Formulación y Ev. de Proyectos": {"anio": 4, "correlativas": ["Comercio Exterior y Ec. Int.", "Plan de Negocios", "Taller de Integración I"]},
    "Sistemas de Organización": {"anio": 4, "correlativas": ["Plan de Negocios"]},
    "Economía Industrial": {"anio": 4, "correlativas": ["Macroeconomía y Pol. Económica", "Economía Bancaria y Financiera"]},
    "Economía Bancaria y Financiera": {"anio": 4, "correlativas": ["Financiamiento"]},
    "Gestión Ambiental y Empresa": {"anio": 4, "correlativas": ["Org. de la Producción y Tecnología", "Organización y Gestión"]},
    "Admin. de Recursos Humanos": {"anio": 4, "correlativas": ["Gestión Ambiental y Empresa"]},
    "Taller de Integración II": {"anio": 4, "correlativas": ["Sistemas de Organización", "Economía Bancaria y Financiera"]},
    "Mediación y Negociación": {"anio": 5, "correlativas": ["Admin. de Recursos Humanos"]},
    "Problemas Actuales de la Econ. Arg.": {"anio": 5, "correlativas": ["Taller de Integración II"]},
    "Seminario: Resp. Social Empresaria": {"anio": 5, "correlativas": ["Ética y Empresa"]},
    "Seminario: Economía Social": {"anio": 5, "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Práctica Pre-Profesional": {"anio": 5, "correlativas": ["Taller de Integración II"]},
    "Taller de Trabajo Final Integrador": {"anio": 5, "correlativas": ["Taller de Integración II", "Taller de Integración I"]},
    "Ética y Empresa": {"anio": 5, "correlativas": ["Admin. de Recursos Humanos"]},
    "Planeamiento Estratégico": {"anio": 5, "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Políticas y Estrategias Des. Reg.": {"anio": 5, "correlativas": ["Taller de Integración II"]},
    "Nivel 1 - Inglés": {"anio": 99, "correlativas": []},
    "Nivel 2 - Inglés": {"anio": 99, "correlativas": ["Nivel 1 - Inglés"]},
    "Informática (Módulos)": {"anio": 99, "correlativas": []}
}

# --- 4. LÓGICA DE APLICACIÓN ---
def main():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("⚠️ No se pudo conectar con la base de datos.")
        return

    with st.sidebar:
        st.markdown("<h1 style='color:#800000; text-align:center;'>🔴 CÍRCULO ROJO</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 ¿Quién sos?", LISTA_CHICOS, key="user_sel")
        st.markdown("---")
        
        if "menu" not in st.session_state: st.session_state.menu = "Inicio"
        
        if st.button("🏠 Inicio", key="btn_i"): st.session_state.menu = "Inicio"
        if st.button("📊 Mi Historial", key="btn_h"): st.session_state.menu = "Historial"
        if st.button("📝 Inscribirse", key="btn_ins"): st.session_state.menu = "Inscripcion"
        
        st.markdown("---")
        st.link_button("🔗 SIU Guaraní", "https://guarani.unla.edu.ar/unla/")

    if usuario == "Seleccionar...":
        st.title("Planificador de Carrera")
        st.info("👋 Selecciona tu nombre en la barra lateral para comenzar.")
        return

    # Cálculos de KPI
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = len(mis_datos[mis_datos["Estado"] == "Aprobada"])
    cursando = len(mis_datos[mis_datos["Estado"] == "Cursando"])
    restantes = TOTAL_MATERIAS - aprobadas
    progreso_ratio = aprobadas / TOTAL_MATERIAS

    # Header con KPIs Modernos
    st.markdown(f"## ¡Hola, {usuario}! ✨")
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Materias Aprobadas</div><div class='kpi-value'>{aprobadas}</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Cursando</div><div class='kpi-value'>{cursando}</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Restantes</div><div class='kpi-value'>{restantes}</div></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avance Carrera</div><div class='kpi-value'>{int(progreso_ratio*100)}%</div></div>", unsafe_allow_html=True)
    
    st.progress(progreso_ratio)

    # Navegación
    menu = st.session_state.menu

    if menu == "Inicio":
        c_avatar, c_info = st.columns([1, 1.5])
        with c_avatar:
            st.subheader("Tu Avatar")
            mascota = st.selectbox("Elegí tu compañero:", list(ANIMACIONES.keys()), key="masc_sel")
            anim = load_lottieurl(ANIMACIONES[mascota])
            if anim:
                # El avatar se mueve a una velocidad basada en tu progreso
                st_lottie(anim, height=280, key=f"anim_{usuario}_{mascota}", speed=1 + progreso_ratio)
            else:
                st.warning("🔄 El servidor de animaciones está tardando. Reintenta en unos segundos...")
        
        with c_info:
            st.subheader("📖 Cursadas actuales")
            materias_c = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if materias_c:
                for m in materias_c: st.success(f"📌 {m}")
            else:
                st.info("No tenés materias en curso.")

    elif menu == "Historial":
        st.subheader("Gestionar mis materias")
        aprobadas_actuales = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
        seleccion = st.multiselect("Marcá las materias aprobadas:", list(PLAN_ESTUDIOS.keys()), default=aprobadas_actuales)
        
        if st.button("💾 Guardar Historial"):
            df_new = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            nuevos_rows = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada", "Modalidad": "Regular"} for m in seleccion]
            df_final = pd.concat([df_new, pd.DataFrame(nuevos_rows)], ignore_index=True)
            conn.update(worksheet=0, data=df_final)
            st.cache_data.clear()
            st.success("¡Progreso actualizado!")
            st.rerun()

if __name__ == "__main__":
    main()
