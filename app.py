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

# --- 2. PLAN DE ESTUDIOS 2026 (ACTUALIZADO) ---
PLAN_ESTUDIOS = {
    "Introducción a Economía Empresarial": {"is_tech": True, "correlativas": []},
    "Historia Económica Contemporánea": {"is_tech": True, "correlativas": []},
    "Contabilidad": {"is_tech": True, "correlativas": []},
    "Matemática I": {"is_tech": True, "correlativas": []},
    "Taller de Comunicación y Producción de Textos": {"is_tech": True, "correlativas": []},
    "Empresa, Economía y Sociedad": {"is_tech": True, "correlativas": ["Historia Económica Contemporánea"]},
    "Organización y Gestión": {"is_tech": True, "correlativas": []},
    "Matemática II": {"is_tech": True, "correlativas": ["Matemática I"]},
    "Derecho Comercial": {"is_tech": True, "correlativas": ["Organización y Gestión"]},
    "Seminario de Justicia y Derechos Humanos": {"is_tech": True, "correlativas": []},
    "Microeconomía I": {"is_tech": True, "correlativas": ["Empresa, Economía y Sociedad", "Matemática I"]},
    "Cálculo Financiero": {"is_tech": True, "correlativas": ["Matemática II"]},
    "Comercialización": {"is_tech": True, "correlativas": ["Organización y Gestión"]},
    "Costos Empresariales": {"is_tech": True, "correlativas": ["Contabilidad", "Matemática II"]},
    "Seminario de Pensamiento Nacional Latinoamericano": {"is_tech": True, "correlativas": []},
    "Macroeconomía": {"is_tech": True, "correlativas": ["Microeconomía I"]},
    "Estadística": {"is_tech": True, "correlativas": ["Matemática II"]},
    "Sistemas de Información": {"is_tech": True, "correlativas": ["Contabilidad"]},
    "Administración Financiera": {"is_tech": True, "correlativas": ["Cálculo Financiero"]},
    "Derecho del Trabajo y la Seguridad Social": {"is_tech": True, "correlativas": ["Derecho Comercial"]},
    "Microeconomía II": {"is_tech": True, "correlativas": ["Microeconomía I"]},
    "Investigación de Operaciones": {"is_tech": True, "correlativas": ["Estadística"]},
    "Principios de Tributación": {"is_tech": True, "correlativas": ["Derecho Comercial", "Costos Empresariales"]},
    "Seminario de Integración I": {"is_tech": True, "correlativas": ["Comercialización", "Administración Financiera"]},
    "Taller de Práctica Preprofesional": {"is_tech": True, "correlativas": ["Seminario de Integración I"]},
    "Macroeconomía y Política Económica": {"is_tech": False, "correlativas": ["Macroeconomía"]},
    "Tecnología y Ciencia de Datos": {"is_tech": False, "correlativas": ["Investigación de Operaciones"]},
    "Seminario Optativo 1": {"is_tech": False, "correlativas": []},
    "Seminario Optativo 2": {"is_tech": False, "correlativas": []},
    "Gestión Ambiental y Empresa": {"is_tech": False, "correlativas": ["Organización y Gestión"]},
    "Taller de Proyecto Empresarial": {"is_tech": False, "correlativas": ["Seminario de Integración I"]},
    "Planeamiento Estratégico": {"is_tech": False, "correlativas": ["Seminario de Integración I"]},
    "Seminario Optativo 3": {"is_tech": False, "correlativas": []},
    "Política Económica": {"is_tech": False, "correlativas": ["Macroeconomía y Política Económica"]},
    "Inteligencia de Negocios": {"is_tech": False, "correlativas": ["Tecnología y Ciencia de Datos"]},
    "Comercio Exterior": {"is_tech": False, "correlativas": ["Macroeconomía y Política Económica"]},
    "Inglés I": {"is_tech": False, "correlativas": []},
    "Seminario Optativo 4": {"is_tech": False, "correlativas": []},
    "Taller de Trabajo Final Integrador": {"is_tech": False, "correlativas": ["Taller de Proyecto Empresarial"]},
    "Inglés II": {"is_tech": False, "correlativas": ["Inglés I"]}
}

TOTAL_LICENCIATURA = 40
TOTAL_TECNICATURA = 25

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
    
    st.markdown("<h1 class='retro-font' style='text-align:center; font-size:24px;'>SQUAD COMMAND 2026</h1>", unsafe_allow_html=True)
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
    ap_nombres = aprobadas_df["Materia"].tolist()
    
    # Lógica de Tecnicatura
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
            st.link_button("🏛️ SIU", "https://estudiantes.unla.edu.ar/autogestion3w/acceso", use_container_width=True)
        
        with col_cur:
            st.markdown("#### 🏆 OBJETIVOS 2026:")
            prog_tech = int((n_tech / TOTAL_TECNICATURA) * 100)
            st.markdown(f"<p class='hp-bar-text'>TECNICATURA: {prog_tech}%</p>", unsafe_allow_html=True)
            st.progress(n_tech / TOTAL_TECNICATURA)
            
            prog_lic = int((len(aprobadas_df) / TOTAL_LICENCIATURA) * 100)
            st.markdown(f"<p class='hp-bar-text'>LICENCIATURA: {prog_lic}%</p>", unsafe_allow_html=True)
            st.progress(len(aprobadas_df) / TOTAL_LICENCIATURA)
            
            k1, k2 = st.columns(2)
            k1.markdown(f'<div class="tech-badge">🎓 TÉCNICO: FALTAN {TOTAL_TECNICATURA - n_tech}</div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="missing-badge">⚔️ LICENCIADO: FALTAN {TOTAL_LICENCIATURA - len(aprobadas_df)}</div>', unsafe_allow_html=True)

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

    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE 2026")
        st.dataframe(mis_datos[["Materia", "Estado", "Nota"]].sort_values("Estado"), use_container_width=True, hide_index=True)

    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        # Identificar qué tiene el alumno ya en su registro (aprobada o cursando)
        materias_en_registro = mis_datos["Materia"].tolist()
        
        # Filtrar materias desbloqueadas que NO estén en el registro y correlativas aprobadas
        disp = [m for m, i in PLAN_ESTUDIOS.items() if m not in materias_en_registro and all(c in ap_nombres for c in i["correlativas"])]
        
        if not disp:
            st.warning("No hay materias desbloqueadas actualmente. ¡Rinde finales para desbloquear!")
        else:
            for d in disp:
                c_mat, c_btn = st.columns([3, 1])
                c_mat.success(f"🔓 **{d}**")
                if c_btn.button(f"⚔️ CURSAR", key=f"inscribir_{d}"):
                    # Añadir nueva fila al Excel
                    nueva_materia = pd.DataFrame([{"Nombre": usuario, "Materia": d, "Estado": "Cursando", "Nota": ""}])
                    df_final = pd.concat([df, nueva_materia], ignore_index=True)
                    conn.update(worksheet=0, data=df_final)
                    st.toast(f"¡Te has inscripto en {d}!")
                    st.rerun()

    elif st.session_state.menu == "Grupo":
        st.header("👥 RECUENTO DE TROPAS")
        ranking = df[df["Estado"] == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)

if __name__ == "__main__": main()
