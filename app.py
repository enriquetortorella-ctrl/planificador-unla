import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_lottie import st_lottie
import requests
from datetime import datetime, date

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Círculo Rojo v2.6", page_icon="🔴", layout="wide")

# Estilos (Mantenemos los que te gustaron)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e1117; }
    .kpi-card { background-color: #1e1e26; padding: 20px; border-radius: 15px; border-left: 5px solid #800000; margin-bottom: 10px; }
    .kpi-value { font-size: 30px; font-weight: bold; color: #ffffff; }
    .kpi-label { font-size: 14px; color: #a0a0a0; text-transform: uppercase; }
    .stButton>button { border-radius: 12px; transition: all 0.3s; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #800000 !important; color: white !important; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES ---
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 3. DATOS ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS = 42

# URLs de Lottie actualizadas para máxima compatibilidad
ANIMACIONES = {
    "Lagarto 🦎": "https://lottie.host/626d0130-9d93-4702-9093-90343729e205/S0P7N9N7N9.json",
    "Dragón 🐉": "https://lottie.host/8167f474-0466-419b-9807-f8271035c916/J8X5F5F5F5.json",
    "Robot 🤖": "https://lottie.host/5a7f052d-3c22-4299-8086-53818610b784/A9N9N9N9N9.json"
}

# (Tu diccionario de PLAN_ESTUDIOS se mantiene igual)
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

# --- 4. FUNCIÓN PRINCIPAL ---
def main():
    # Conexión con manejo de errores
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except Exception as e:
        st.error("⚠️ Error de conexión. Revisa tus secretos o el archivo Excel.")
        return

    # Sidebar - SELECTOR CON KEY ÚNICA PARA EVITAR EL ERROR
    with st.sidebar:
        st.markdown("<h1 style='color:#800000; text-align:center;'>🔴 CÍRCULO ROJO</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 Perfil", LISTA_CHICOS, key="selector_usuario_principal")
        st.markdown("---")
        
        if "menu" not in st.session_state: st.session_state.menu = "Inicio"
        
        # Botones con Keys únicas
        if st.button("🏠 Inicio", key="btn_inicio"): st.session_state.menu = "Inicio"
        if st.button("📊 Mi Progreso", key="btn_progreso"): st.session_state.menu = "Progreso"
        if st.button("📝 Inscripción", key="btn_insc"): st.session_state.menu = "Inscripcion"

    if usuario == "Seleccionar...":
        st.title("Planificador UNLa 2026")
        st.info("👋 Hola! Elegí tu nombre en la barra lateral para ver tus materias y avatar.")
        return

    # Lógica de datos del usuario
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = len(mis_datos[mis_datos["Estado"] == "Aprobada"])
    cursando = len(mis_datos[mis_datos["Estado"] == "Cursando"])
    progreso = aprobadas / TOTAL_MATERIAS

    # Header de bienvenida
    st.markdown(f"## ¡Hola, {usuario}! ✨")
    
    # Tarjetas KPI
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Aprobadas</div><div class='kpi-value'>{aprobadas}</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Cursando</div><div class='kpi-value'>{cursando}</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Restantes</div><div class='kpi-value'>{TOTAL_MATERIAS - aprobadas}</div></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Avance</div><div class='kpi-value'>{int(progreso*100)}%</div></div>", unsafe_allow_html=True)
    
    st.progress(progreso)

    # Navegación
    if st.session_state.menu == "Inicio":
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.subheader("Tu Avatar")
            # Selector de mascota con Key única
            mascota = st.selectbox("Elegí tu compañero:", list(ANIMACIONES.keys()), key="selector_mascota")
            anim = load_lottieurl(ANIMACIONES[mascota])
            if anim:
                st_lottie(anim, height=250, key="lottie_main", speed=1 + progreso)
            else:
                st.write("🎬 Cargando animación...")
        
        with col2:
            st.subheader("📌 Materias que cursás ahora")
            actuales = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if actuales:
                for m in actuales: st.success(f"📖 {m}")
            else:
                st.info("No tenés cursadas activas. ¡Dale a Inscripción!")

    elif st.session_state.menu == "Progreso":
        st.subheader("Actualizar materias metidas")
        # Multiselect con Key única
        lista_aprobadas_actual = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
        nuevas = st.multiselect("Materias con final/promoción:", list(PLAN_ESTUDIOS.keys()), default=lista_aprobadas_actual, key="multi_aprobadas")
        
        if st.button("💾 Guardar Cambios", key="btn_save_progreso"):
            # Borramos lo viejo y guardamos lo nuevo
            df_sin_usuario = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            nuevos_registros = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada", "Modalidad": "Regular"} for m in nuevas]
            df_final = pd.concat([df_sin_usuario, pd.DataFrame(nuevos_registros)], ignore_index=True)
            
            conn.update(worksheet=0, data=df_final)
            st.cache_data.clear()
            st.success("¡Progreso actualizado!")
            st.rerun()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()


