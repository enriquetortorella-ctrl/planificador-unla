import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_lottie import st_lottie
import requests
from datetime import datetime, date

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo v2.6", page_icon="🔴", layout="wide")

# Estilos CSS personalizados
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
    .kpi-label { font-size: 14px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; }
    
    .stButton>button {
        border-radius: 12px;
        height: 3em;
        transition: all 0.3s ease;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #800000 !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(128,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE APOYO ---
@st.cache_data(ttl=3600)
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 3. CONSTANTES Y DATOS ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS_CARRERA = 42

ANIMACIONES = {
    "Lagarto 🦎": "https://assets10.lottiefiles.com/packages/lf20_hy4per6f.json",
    "Dragón 🐉": "https://assets8.lottiefiles.com/packages/lf20_5mjt84fc.json",
    "Robot 🤖": "https://assets10.lottiefiles.com/private_files/lf30_igp67uub.json"
}

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

# --- 4. APLICACIÓN PRINCIPAL ---
def main():
    # Conexión a GSheets
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("⚠️ Error de conexión con la base de datos.")
        return

    # SIDEBAR
    with st.sidebar:
        st.markdown("<h1 style='color:#800000; text-align:center; margin-bottom:0;'>🔴 CÍRCULO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#888; margin-top:0;'>PLANIFICADOR UNLa</p>", unsafe_allow_html=True)
        
        # Selector de usuario con KEY única para evitar errores de duplicado
        usuario = st.selectbox("👤 ¿Quién eres?", LISTA_CHICOS, key="main_user_selector")
        
        st.markdown("---")
        if "menu" not in st.session_state:
            st.session_state.menu = "Inicio"
            
        if st.button("🏠 Inicio", key="nav_home"): st.session_state.menu = "Inicio"
        if st.button("📊 Mi Progreso", key="nav_prog"): st.session_state.menu = "Progreso"
        
        st.markdown("---")
        st.caption("Versión 2026.2.9")

    # PANTALLA DE BIENVENIDA SI NO HAY USUARIO
    if usuario == "Seleccionar...":
        st.title("Bienvenido al Planificador")
        st.info("Elegí tu nombre en la barra lateral para cargar tus datos y tu avatar.")
        return

    # FILTRADO DE DATOS
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    cursando_list = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
    
    num_aprobadas = len(aprobadas_list)
    num_cursando = len(cursando_list)
    progreso_ratio = num_aprobadas / TOTAL_MATERIAS_CARRERA

    # HEADER CON KPIs MODERNOS
    st.markdown(f"## ¡Hola, {usuario}! 👋")
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Materias Aprobadas</div><div class='kpi-value'>{num_aprobadas}</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>En Cursada</div><div class='kpi-value'>{num_cursando}</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Materias Restantes</div><div class='kpi-value'>{TOTAL_MATERIAS_CARRERA - num_aprobadas}</div></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avance Total</div><div class='kpi-value'>{int(progreso_ratio*100)}%</div></div>", unsafe_allow_html=True)
    
    st.progress(progreso_ratio)
    st.markdown("---")

    # LÓGICA DE MENÚ
    if st.session_state.menu == "Inicio":
        col_avatar, col_status = st.columns([1, 1.5])
        
        with col_avatar:
            st.subheader("Tu Avatar")
            mascota_fav = st.selectbox("Elegí tu compañero:", list(ANIMACIONES.keys()), key="avatar_selector")
            anim_data = load_lottieurl(ANIMACIONES[mascota_fav])
            
            if anim_data:
                # La velocidad aumenta con el progreso
                st_lottie(anim_data, height=280, key=f"lottie_{usuario}", speed=1 + progreso_ratio)
            else:
                st.warning("🔄 Conectando con servidor de animaciones...")

        with col_status:
            st.subheader("📌 Cursadas Actuales")
            if cursando_list:
                for m in cursando_list:
                    st.success(f"📖 **{m}**")
            else:
                st.info("No tienes materias en curso actualmente. ¡Anotate en la próxima inscripción!")

    elif st.session_state.menu == "Progreso":
        st.subheader("Actualizar Historial de Materias")
        st.write("Seleccioná todas las materias que ya tenés aprobadas (por final o promoción):")
        
        nuevas_aprobadas = st.multiselect(
            "Materias aprobadas:", 
            list(PLAN_ESTUDIOS.keys()), 
            default=aprobadas_list,
            key="multi_aprobadas_update"
        )
        
        if st.button("💾 Guardar Mi Progreso", key="save_progress_btn"):
            # Limpiamos registros anteriores de 'Aprobada' para este usuario
            df_limpio = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            
            # Creamos los nuevos registros
            nuevos_rows = []
            for m in nuevas_aprobadas:
                nuevos_rows.append({
                    "Nombre": usuario,
                    "Materia": m,
                    "Estado": "Aprobada",
                    "Modalidad": "Regular"
                })
            
            df_final = pd.concat([df_limpio, pd.DataFrame(nuevos_rows)], ignore_index=True)
            
            # Guardamos en Google Sheets
            conn.update(worksheet=0, data=df_final)
            st.cache_data.clear()
            st.success("¡Historial actualizado correctamente!")
            st.rerun()

if __name__ == "__main__":
    main()
