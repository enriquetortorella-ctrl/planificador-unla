import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Círculo Rojo RPG", page_icon="⚔️", layout="wide")

# Estilos Pro
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Inter:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .pixel-box {
        background: #1e1e26;
        border: 4px solid #ffffff;
        box-shadow: 6px 6px 0px #800000;
        padding: 20px;
        text-align: center;
        border-radius: 4px;
    }
    
    .retro-title {
        font-family: 'Press Start 2P', cursive;
        color: #ff4b4b;
        font-size: 14px;
        text-shadow: 2px 2px #000;
        margin-bottom: 20px;
    }

    .item-card {
        background: #2d2d3a;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        font-size: 0.85em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATOS: PLAN DE ESTUDIOS Y RECOMPENSAS ---
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

RECOMPENSAS = {
    1: "☕ Café Frío", 5: "🎒 Mochila UNLa", 10: "🎧 Lo-Fi Beats", 
    20: "🔥 Aura Roja", 30: "🪄 Varita de Aprobación", 42: "👑 TITULO"
}

# --- 3. LÓGICA DE AVATARES ---
def get_avatar_url(seed, level):
    if level < 10: style = "pixel-art"
    elif level < 25: style = "avataaars"
    else: style = "bottts-neutral"
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"

# --- 4. APP PRINCIPAL ---
def main():
    if "menu" not in st.session_state: st.session_state.menu = "Status"

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("Error de conexión con la base de datos.")
        return

    with st.sidebar:
        st.markdown("<p class='retro-title'>RED CIRCLE RPG</p>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 JUGADOR", ["Seleccionar..."] + list(df["Nombre"].unique()))
        
        st.markdown("---")
        if st.button("🏠 Mi Status", use_container_width=True): 
            st.session_state.menu = "Status"
            st.rerun()
        if st.button("📊 Plan de Carrera", use_container_width=True): 
            st.session_state.menu = "Plan"
            st.rerun()
        if st.button("🎒 Inventario", use_container_width=True): 
            st.session_state.menu = "Inventario"
            st.rerun()

    if usuario == "Seleccionar...":
        st.title("🕹️ Bienvenido al Planificador RPG")
        st.info("Elegí tu nombre para cargar tu progreso.")
        return

    # Cálculos
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = list(mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"])
    n_aprobadas = len(aprobadas)

    if st.session_state.menu == "Status":
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.markdown("<div class='pixel-box'>", unsafe_allow_html=True)
            st.image(get_avatar_url(usuario, n_aprobadas), width=180)
            st.markdown(f"**LVL {n_aprobadas}**")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.header(f"Player: {usuario}")
            st.metric("Materias Conquistadas", f"{n_aprobadas}/42")
            st.progress(n_aprobadas/42)
            
            cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if cursando:
                st.subheader("⚔️ Misiones en curso")
                for c in cursando: st.success(c)

    elif st.session_state.menu == "Plan":
        st.header("📊 Hoja de Ruta")
        
        tab1, tab2 = st.tabs(["Materias Disponibles", "Carrera Completa"])
        
        with tab1:
            st.subheader("Disponibles para cursar ahora:")
            disponibles = []
            for mat, info in PLAN_ESTUDIOS.items():
                if mat not in aprobadas:
                    correlativas_ok = all(corr in aprobadas for corr in info["correlativas"])
                    if correlativas_ok: disponibles.append(mat)
            
            if disponibles:
                for d in disponibles: st.info(f"✅ {d}")
            else:
                st.write("No tenés materias disponibles por ahora.")

        with tab2:
            st.write("Estado de todas las materias:")
            for mat in PLAN_ESTUDIOS.keys():
                if mat in aprobadas:
                    st.write(f"🟢 {mat} (Aprobada)")
                else:
                    st.write(f"⚪ {mat}")

    elif st.session_state.menu == "Inventario":
        st.header("🎒 Inventario RPG")
        mis_items = [v for k, v in RECOMPENSAS.items() if n_aprobadas >= k]
        if mis_items:
            cols = st.columns(3)
            for i, item in enumerate(mis_items):
                cols[i%3].markdown(f"<div class='item-card'>{item}</div>", unsafe_allow_html=True)
        else:
            st.write("Tu mochila está vacía.")

if __name__ == "__main__":
    main()
