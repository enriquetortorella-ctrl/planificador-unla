import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo - SQUAD", page_icon="🔫", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    .stApp { background-color: #0e1117; color: #ffffff; }
    .avatar-container {
        border: 3px solid #f1c40f;
        background: rgba(44, 62, 80, 0.8);
        padding: 20px;
        border-radius: 5px;
        text-align: center;
        box-shadow: 5px 5px 0px #000;
        display: inline-block;
        min-width: 220px;
    }
    .retro-font { font-family: 'Press Start 2P', cursive; font-size: 10px; color: #f1c40f; text-shadow: 2px 2px #000; }
    .main-card { background-color: #1e1e26; padding: 15px; border-radius: 10px; border-left: 5px solid #800000; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS (Resumido para el ejemplo, mantén el tuyo completo) ---
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

# --- 3. LÓGICA DE AVATARES (CORREGIDA PARA MAYÚSCULAS) ---
def get_avatar_slug(usuario, n_aprobadas):
    squad = {
        "Facu": "Allen",
        "Ivan": "Trevor",
        "Maca": "Alisa",
        "Juli": "Nadia",
        "Kike": "Marco",
        "Cristian": "Tarma"
    }
    
    char_base = squad.get(usuario, "Marco")

    # Niveles cada 10 materias
    if n_aprobadas <= 10: nivel = 1
    elif n_aprobadas <= 20: nivel = 2
    elif n_aprobadas <= 30: nivel = 3
    else: nivel = 4

    # Ruta EXACTA como aparece en tu GitHub (Mayúscula_Número.gif)
    nombre_archivo = f"{char_base}_{nivel}.gif"
    path = os.path.join("assets", nombre_archivo)
    
    # Verificación extra: si no existe, intenta con minúsculas por si acaso
    if not os.path.exists(path):
        path = os.path.join("assets", nombre_archivo.lower())

    if os.path.exists(path):
        return path, nivel
    
    # Fallback si nada funciona
    return "https://api.dicebear.com/7.x/pixel-art/svg?seed=army", 1

# --- 4. MAIN ---
def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        df["Nombre"] = df["Nombre"].replace(["Facu Uriarte", "Facundo Uriarte"], "Facu")
    except Exception as e:
        st.error(f"Error: {e}")
        return

    with st.sidebar:
        st.markdown("<p class='retro-font'>SQUAD COMMAND</p>", unsafe_allow_html=True)
        nombres_disponibles = sorted(list(df["Nombre"].unique()))
        usuario = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + nombres_disponibles)
        st.markdown("---")
        if st.button("🏠 INICIO"): st.session_state.menu = "Inicio"; st.rerun()
        if st.button("✅ HISTORIAL"): st.session_state.menu = "Historial"; st.rerun()
        if st.button("📝 PRÓXIMAS"): st.session_state.menu = "Proximas"; st.rerun()
        if st.button("👥 GRUPO"): st.session_state.menu = "Grupo"; st.rerun()

    if usuario == "Seleccionar...":
        st.title("SQUAD COMMAND - UNLa")
        return

    mis_datos = df[df["Nombre"] == usuario]
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    n_aprobadas = len(aprobadas_list)

    if st.session_state.menu == "Inicio":
        col_av, col_cur = st.columns([1, 2])
        with col_av:
            img_path, lvl_actual = get_avatar_slug(usuario, n_aprobadas)
            armas = ["Pistola", "HMG", "Shotgun", "TANK MODE"]
            st.markdown('<div class="avatar-container">', unsafe_allow_html=True)
            st.markdown(f'<p class="retro-font" style="font-size:8px;">GEAR: {armas[lvl_actual-1]}</p>', unsafe_allow_html=True)
            st.image(img_path, width=160)
            st.markdown(f'<p class="retro-font">{usuario.upper()}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_cur:
            st.metric("AVANCE", f"{int((n_aprobadas/42)*100)}%", f"{42-n_aprobadas} materias faltantes")
            st.progress(n_aprobadas/42)
            st.markdown("#### ⚔️ MATERIAS EN CURSO:")
            for m in mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"]:
                st.markdown(f"<div class='main-card'>📖 {m}</div>", unsafe_allow_html=True)

    elif st.session_state.menu == "Historial":
        st.dataframe(mis_datos[["Materia", "Estado", "Nota"]])

    elif st.session_state.menu == "Proximas":
        disponibles = [m for m, i in PLAN_ESTUDIOS.items() if m not in aprobadas_list and all(c in aprobadas_list for c in i["correlativas"])]
        for d in disponibles: st.success(f"🔓 {d}")

    elif st.session_state.menu == "Grupo":
        ranking = df[df["Estado"] == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)

if __name__ == "__main__":
    main()
