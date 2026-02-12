import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo - SQUAD", page_icon="🔫", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    .stApp { background-color: #0b0d11; color: #e0e0e0; }
    .stButton>button[key^="mision_"] {
        background: linear-gradient(135deg, #1a1c23 0%, #0d0e12 100%) !important;
        border: 2px solid #444 !important;
        border-left: 5px solid #ff4b4b !important;
        color: white !important;
        text-align: left !important;
        padding: 20px !important;
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    .retro-font { font-family: 'Press Start 2P', cursive; color: #f1c40f; text-shadow: 2px 2px #000; }
    .hp-bar-text { font-family: 'Press Start 2P', cursive; font-size: 10px; color: #ff4b4b; }
    .tech-badge {
        background-color: #2ecc71; color: black; font-family: 'Press Start 2P', cursive;
        font-size: 9px; padding: 5px; border-radius: 4px; text-align: center; margin: 5px 0;
    }
    .missing-badge {
        background-color: #ff4b4b; color: white; font-family: 'Press Start 2P', cursive;
        font-size: 9px; padding: 8px; border-radius: 4px; text-align: center; margin: 5px 0;
    }
    [data-testid="stMetricValue"] { font-family: 'Press Start 2P', cursive; font-size: 18px !important; }
    [data-testid="sidebarSelfHosted"], section[data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS (Con marca de Tecnicatura) ---
# He marcado con "is_tech": True las materias que suelen entrar en el título intermedio
PLAN_ESTUDIOS = {
    "Taller de Producción de Textos": {"is_tech": True, "correlativas": []},
    "Introducción a la Matemática": {"is_tech": True, "correlativas": []},
    "Contabilidad": {"is_tech": True, "correlativas": []},
    "Historia Económica Contemporánea": {"is_tech": True, "correlativas": []},
    "Elementos de Matemática": {"is_tech": True, "correlativas": ["Introducción a la Matemática"]},
    "Organización y Gestión": {"is_tech": True, "correlativas": []},
    "Economía y Sociedad": {"is_tech": True, "correlativas": ["Historia Económica Contemporánea"]},
    "Microeconomía": {"is_tech": True, "correlativas": ["Historia Económica Contemporánea", "Introducción a la Matemática"]},
    "Derecho Comercial": {"is_tech": True, "correlativas": ["Organización y Gestión"]},
    "Cálculo Financiero y Est. Aplicado": {"is_tech": True, "correlativas": ["Elementos de Matemática"]},
    "Costos Empresariales": {"is_tech": True, "correlativas": ["Elementos de Matemática", "Organización y Gestión"]},
    "Derecho Tributario": {"is_tech": True, "correlativas": ["Derecho Comercial"]},
    "Macroeconomía": {"is_tech": True, "correlativas": ["Economía y Sociedad"]},
    "Org. de la Producción y Tecnología": {"is_tech": True, "correlativas": ["Costos Empresariales"]},
    "Derecho del Trabajo y Seg. Social": {"is_tech": True, "correlativas": ["Derecho Tributario"]},
    "Comercialización": {"is_tech": True, "correlativas": ["Costos Empresariales", "Macroeconomía"]},
    "Control de Gestión": {"is_tech": True, "correlativas": ["Costos Empresariales"]},
    "Macroeconomía y Pol. Económica": {"is_tech": True, "correlativas": ["Macroeconomía"]},
    "Comercio Exterior y Ec. Int.": {"is_tech": True, "correlativas": ["Macroeconomía y Pol. Económica"]},
    "Plan de Negocios": {"is_tech": True, "correlativas": ["Control de Gestión", "Comercialización"]},
    "Financiamiento": {"is_tech": True, "correlativas": ["Comercialización"]},
    "Taller de Integración I": {"is_tech": True, "correlativas": ["Comercialización"]},
    "Nivel 1 - Inglés": {"is_tech": True, "correlativas": []},
    "Nivel 2 - Inglés": {"is_tech": True, "correlativas": ["Nivel 1 - Inglés"]},
    "Informática (Módulos)": {"is_tech": True, "correlativas": []},
    "Práctica Pre-Profesional": {"is_tech": True, "correlativas": ["Taller de Integración I"]},
    # Materias solo de Licenciatura
    "Formulación y Ev. de Proyectos": {"is_tech": False, "correlativas": ["Comercio Exterior y Ec. Int.", "Plan de Negocios"]},
    "Sistemas de Organización": {"is_tech": False, "correlativas": ["Plan de Negocios"]},
    "Economía Industrial": {"is_tech": False, "correlativas": ["Macroeconomía y Pol. Económica"]},
    "Economía Bancaria y Financiera": {"is_tech": False, "correlativas": ["Financiamiento"]},
    "Gestión Ambiental y Empresa": {"is_tech": False, "correlativas": ["Org. de la Producción y Tecnología"]},
    "Admin. de Recursos Humanos": {"is_tech": False, "correlativas": ["Gestión Ambiental y Empresa"]},
    "Taller de Integración II": {"is_tech": False, "correlativas": ["Sistemas de Organización"]},
    "Mediación y Negociación": {"is_tech": False, "correlativas": ["Admin. de Recursos Humanos"]},
    "Problemas Actuales de la Econ. Arg.": {"is_tech": False, "correlativas": ["Taller de Integración II"]},
    "Seminario: Resp. Social Empresaria": {"is_tech": False, "correlativas": ["Ética y Empresa"]},
    "Seminario: Economía Social": {"is_tech": False, "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Taller de Trabajo Final Integrador": {"is_tech": False, "correlativas": ["Taller de Integración II"]},
    "Ética y Empresa": {"is_tech": False, "correlativas": ["Admin. de Recursos Humanos"]},
    "Planeamiento Estratégico": {"is_tech": False, "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Políticas y Estrategias Des. Reg.": {"is_tech": False, "correlativas": ["Taller de Integración II"]}
}

TOTAL_LICENCIATURA = 42
TOTAL_TECNICATURA = len([m for m, v in PLAN_ESTUDIOS.items() if v["is_tech"]])

def get_avatar_slug(usuario, n_aprobadas):
    squad = {"Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa", "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma"}
    char_base = squad.get(usuario, "Marco")
    if n_aprobadas <= 10: nivel = 1
    elif n_aprobadas <= 20: nivel = 2
    elif n_aprobadas <= 30: nivel = 3
    else: nivel = 4
    path = os.path.join("assets", f"{char_base}_{nivel}.gif")
    if os.path.exists(path): return path, nivel
    return f"https://api.dicebear.com/7.x/pixel-art/svg?seed={usuario}", nivel

def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=0, ttl=0)
    df.columns = [str(c).strip().capitalize() for c in df.columns]
    if "Nota" not in df.columns: df["Nota"] = ""
    
    st.markdown("<h1 class='retro-font' style='text-align:center; font-size:24px;'>SQUAD COMMAND</h1>", unsafe_allow_html=True)
    usuarios = sorted(list(df["Nombre"].unique()))
    usuario = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + usuarios, label_visibility="collapsed")
    
    if usuario == "Seleccionar...": return

    nav_cols = st.columns(4)
    with nav_cols[0]:
        if st.button("🏠 INICIO"): st.session_state.menu = "Inicio"; st.rerun()
    with nav_cols[1]:
        if st.button("📝 PRÓX."): st.session_state.menu = "Proximas"; st.rerun()
    with nav_cols[2]:
        if st.button("✅ HIST."): st.session_state.menu = "Historial"; st.rerun()
    with nav_cols[3]:
        if st.button("👥 GRUPO"): st.session_state.menu = "Grupo"; st.rerun()

    st.markdown("---")

    mis_datos = df[df["Nombre"] == usuario].copy()
    aprobadas_df = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Aprobada"]
    cursando_df = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Cursando"]
    
    # Lógica de Tecnicatura
    ap_nombres = aprobadas_df["Materia"].tolist()
    tech_aprobadas = [m for m in ap_nombres if m in PLAN_ESTUDIOS and PLAN_ESTUDIOS[m]["is_tech"]]
    n_tech = len(tech_aprobadas)
    
    # Promedio
    notas_validas = pd.to_numeric(aprobadas_df["Nota"], errors='coerce').dropna()
    promedio = notas_validas.mean() if not notas_validas.empty else 0.0

    if st.session_state.menu == "Inicio":
        col_av, col_cur = st.columns([1, 2])
        with col_av:
            img_path, _ = get_avatar_slug(usuario, len(aprobadas_df))
            st.image(img_path, width=150)
            st.markdown(f"<p class='retro-font' style='text-align:center; font-size:14px;'>{usuario.upper()}</p>", unsafe_allow_html=True)
            st.metric("PROMEDIO", f"{promedio:.2f}")
            st.link_button("📂 DRIVE", "https://drive.google.com/drive/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs", use_container_width=True)
            st.link_button("🏛️ SIU", "https://guarani.unla.edu.ar/unla/", use_container_width=True)
        
        with col_cur:
            # --- SECCIÓN DE PROGRESO DUAL ---
            st.markdown("#### 🏆 OBJETIVOS:")
            
            # Progress Bar Tecnicatura
            prog_tech = int((n_tech / TOTAL_TECNICATURA) * 100)
            st.markdown(f"<p class='hp-bar-text'>TECNICATURA: {prog_tech}%</p>", unsafe_allow_html=True)
            st.progress(n_tech / TOTAL_TECNICATURA)
            
            # Progress Bar Licenciatura
            prog_lic = int((len(aprobadas_df) / TOTAL_LICENCIATURA) * 100)
            st.markdown(f"<p class='hp-bar-text'>LICENCIATURA: {prog_lic}%</p>", unsafe_allow_html=True)
            st.progress(len(aprobadas_df) / TOTAL_LICENCIATURA)
            
            # KPIs de materias faltantes
            kpi1, kpi2 = st.columns(2)
            with kpi1:
                st.markdown(f'<div class="tech-badge">🎓 TÉCNICO: FALTAN {TOTAL_TECNICATURA - n_tech}</div>', unsafe_allow_html=True)
            with kpi2:
                st.markdown(f'<div class="missing-badge">⚔️ LICENCIADO: FALTAN {TOTAL_LICENCIATURA - len(aprobadas_df)}</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### ⚔️ MATERIAS EN CURSO:")
            for i, materia in enumerate(cursando_df["Materia"]):
                if st.button(f"✅ {materia}", key=f"mision_{i}"):
                    st.session_state[f"aprobar_{materia}"] = True
                
                if st.session_state.get(f"aprobar_{materia}", False):
                    with st.form(key=f"form_{i}"):
                        nota_input = st.number_input(f"Nota final:", 4, 10, 7)
                        if st.form_submit_button("🎖️ REGISTRAR VICTORIA"):
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == materia), "Estado"] = "Aprobada"
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == materia), "Nota"] = nota_input
                            conn.update(worksheet=0, data=df)
                            st.session_state[f"aprobar_{materia}"] = False
                            st.rerun()

    # El resto del código se mantiene igual...
    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE")
        pendientes_nota = aprobadas_df[pd.to_numeric(aprobadas_df["Nota"], errors='coerce').isna()]
        if not pendientes_nota.empty:
            for j, row in pendientes_nota.iterrows():
                mat_p = row["Materia"]
                with st.expander(f"Cargar nota para: {mat_p}"):
                    with st.form(key=f"pnd_{j}"):
                        nota_p = st.number_input("Nota:", 4, 10, 7)
                        if st.form_submit_button("💾 GUARDAR NOTA"):
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == mat_p), "Nota"] = nota_p
                            conn.update(worksheet=0, data=df)
                            st.rerun()
        st.dataframe(mis_datos[["Materia", "Estado", "Nota"]].sort_values("Estado"), use_container_width=True, hide_index=True)

    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        disp = [m for m, i in PLAN_ESTUDIOS.items() if m not in ap_nombres and all(c in ap_nombres for c in i["correlativas"])]
        for d in disp: st.success(f"🔓 {d}")

    elif st.session_state.menu == "Grupo":
        st.header("👥 RECUENTO DE TROPAS")
        ranking = df[df["Estado"] == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)

if __name__ == "__main__": main()

