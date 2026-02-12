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
    .missing-badge {
        background-color: #ff4b4b; color: white; font-family: 'Press Start 2P', cursive;
        font-size: 10px; padding: 8px; border-radius: 4px; text-align: center; margin: 10px 0;
    }
    [data-testid="stMetricValue"] { font-family: 'Press Start 2P', cursive; font-size: 20px !important; }
    [data-testid="sidebarSelfHosted"], section[data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS (Completo) ---
PLAN_ESTUDIOS = {
    "Taller de Producción de Textos": {"correlativas": []},
    "Introducción a la Matemática": {"correlativas": []},
    "Contabilidad": {"correlativas": []},
    "Historia Económica Contemporánea": {"correlativas": []},
    "Elementos de Matemática": {"correlativas": ["Introducción a la Matemática"]},
    "Organización y Gestión": {"correlativas": []},
    "Economía y Sociedad": {"correlativas": ["Historia Económica Contemporánea"]},
    "Microeconomía": {"correlativas": ["Historia Económica Contemporánea", "Introducción a la Matemática"]},
    "Derecho Comercial": {"correlativas": ["Organización y Gestión"]},
    "Cálculo Financiero y Est. Aplicado": {"correlativas": ["Elementos de Matemática"]},
    "Costos Empresariales": {"correlativas": ["Elementos de Matemática", "Organización y Gestión"]},
    "Derecho Tributario": {"correlativas": ["Derecho Comercial"]},
    "Macroeconomía": {"correlativas": ["Economía y Sociedad"]},
    "Org. de la Producción y Tecnología": {"correlativas": ["Costos Empresariales"]},
    "Derecho del Trabajo y Seg. Social": {"correlativas": ["Derecho Tributario"]},
    "Comercialización": {"correlativas": ["Costos Empresariales", "Macroeconomía"]},
    "Control de Gestión": {"correlativas": ["Costos Empresariales"]},
    "Macroeconomía y Pol. Económica": {"correlativas": ["Macroeconomía"]},
    "Comercio Exterior y Ec. Int.": {"correlativas": ["Macroeconomía y Pol. Económica"]},
    "Plan de Negocios": {"correlativas": ["Control de Gestión", "Comercialización"]},
    "Financiamiento": {"correlativas": ["Comercialización"]},
    "Taller de Integración I": {"correlativas": ["Comercialización"]},
    "Formulación y Ev. de Proyectos": {"correlativas": ["Comercio Exterior y Ec. Int.", "Plan de Negocios", "Taller de Integración I"]},
    "Sistemas de Organización": {"correlativas": ["Plan de Negocios"]},
    "Economía Industrial": {"correlativas": ["Macroeconomía y Pol. Económica", "Economía Bancaria y Financiera"]},
    "Economía Bancaria y Financiera": {"correlativas": ["Financiamiento"]},
    "Gestión Ambiental y Empresa": {"correlativas": ["Org. de la Producción y Tecnología", "Organización y Gestión"]},
    "Admin. de Recursos Humanos": {"correlativas": ["Gestión Ambiental y Empresa"]},
    "Taller de Integración II": {"correlativas": ["Sistemas de Organización", "Economía Bancaria y Financiera"]},
    "Mediación y Negociación": {"correlativas": ["Admin. de Recursos Humanos"]},
    "Problemas Actuales de la Econ. Arg.": {"correlativas": ["Taller de Integración II"]},
    "Seminario: Resp. Social Empresaria": {"correlativas": ["Ética y Empresa"]},
    "Seminario: Economía Social": {"correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Práctica Pre-Profesional": {"correlativas": ["Taller de Integración II"]},
    "Taller de Trabajo Final Integrador": {"correlativas": ["Taller de Integración II", "Taller de Integración I"]},
    "Ética y Empresa": {"correlativas": ["Admin. de Recursos Humanos"]},
    "Planeamiento Estratégico": {"correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Políticas y Estrategias Des. Reg.": {"correlativas": ["Taller de Integración II"]},
    "Nivel 1 - Inglés": {"correlativas": []},
    "Nivel 2 - Inglés": {"correlativas": ["Nivel 1 - Inglés"]},
    "Informática (Módulos)": {"correlativas": []}
}

TOTAL_MATERIAS = 42

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
    
    if "Nota" not in df.columns:
        df["Nota"] = ""
    
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
    n_aprobadas = len(aprobadas_df)
    
    notas_validas = pd.to_numeric(aprobadas_df["Nota"], errors='coerce').dropna()
    promedio = notas_validas.mean() if not notas_validas.empty else 0.0

    if st.session_state.menu == "Inicio":
        col_av, col_cur = st.columns([1, 2])
        with col_av:
            img_path, lvl_visual = get_avatar_slug(usuario, n_aprobadas)
            st.image(img_path, width=150)
            st.markdown(f"<p class='retro-font' style='text-align:center; font-size:14px;'>{usuario.upper()}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='hp-bar-text' style='text-align:center;'>LVL: {n_aprobadas}</p>", unsafe_allow_html=True)
            st.metric("PROMEDIO", f"{promedio:.2f}")
            st.link_button("📂 DRIVE", "https://google.com", use_container_width=True)
            st.link_button("🏛️ SIU", "https://guarani.unla.edu.ar/unla/", use_container_width=True)
        
        with col_cur:
            st.metric("PROGRESO", f"{int((n_aprobadas/TOTAL_MATERIAS)*100)}%")
            st.markdown(f'<div class="missing-badge">FALTAN: {TOTAL_MATERIAS - n_aprobadas} MATERIAS</div>', unsafe_allow_html=True)
            st.progress(n_aprobadas/TOTAL_MATERIAS)
            
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

    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE")
        
        # --- SECCIÓN NUEVA: CARGA DE NOTAS PENDIENTES ---
        pendientes_nota = aprobadas_df[pd.to_numeric(aprobadas_df["Nota"], errors='coerce').isna()]
        
        if not pendientes_nota.empty:
            st.warning("⚠️ Tienes materias aprobadas sin nota cargada:")
            for j, row in pendientes_nota.iterrows():
                mat_p = row["Materia"]
                with st.expander(f"Cargar nota para: {mat_p}"):
                    with st.form(key=f"pnd_{j}"):
                        nota_p = st.number_input("Nota:", 4, 10, 7)
                        if st.form_submit_button("💾 GUARDAR NOTA"):
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == mat_p), "Nota"] = nota_p
                            conn.update(worksheet=0, data=df)
                            st.success("Nota actualizada!"); st.rerun()
        
        st.markdown("---")
        st.dataframe(mis_datos[["Materia", "Estado", "Nota"]].sort_values("Estado"), use_container_width=True, hide_index=True)

    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        ap_nombres = aprobadas_df["Materia"].tolist()
        disp = [m for m, i in PLAN_ESTUDIOS.items() if m not in ap_nombres and all(c in ap_nombres for c in i["correlativas"])]
        for d in disp: st.success(f"🔓 {d}")

    elif st.session_state.menu == "Grupo":
        st.header("👥 RECUENTO DE TROPAS")
        ranking = df[df["Estado"] == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)

if __name__ == "__main__": main()
