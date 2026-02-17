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
        margin-bottom: 5px !important;
    }
    .retro-font { font-family: 'Press Start 2P', cursive; color: #f1c40f; text-shadow: 2px 2px #000; }
    .hp-bar-text { font-family: 'Press Start 2P', cursive; font-size: 10px; color: #ff4b4b; }
    .info-text { font-size: 10px; color: #aaa; margin-bottom: 10px; }
    .tech-badge {
        background-color: #2ecc71; color: black; font-family: 'Press Start 2P', cursive;
        font-size: 9px; padding: 5px; border-radius: 4px; text-align: center; margin: 5px 0;
    }
    .missing-badge {
        background-color: #ff4b4b; color: white; font-family: 'Press Start 2P', cursive;
        font-size: 9px; padding: 8px; border-radius: 4px; text-align: center; margin: 5px 0;
    }
    [data-testid="stMetricValue"] { font-family: 'Press Start 2P', cursive; font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS 2026 ---
PLAN_ESTUDIOS = {
    "Introducción a Economía Empresarial": {"is_tech": True, "periodo": "Bimestral", "correlativas": []},
    "Historia Económica Contemporánea": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": []},
    "Contabilidad": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": []},
    "Matemática I": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": []},
    "Taller de Comunicación y Producción de Textos": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": []},
    "Empresa, Economía y Sociedad": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Historia Económica Contemporánea"]},
    "Organización y Gestión": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": []},
    "Matemática II": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Matemática I"]},
    "Derecho Comercial": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Organización y Gestión"]},
    "Seminario de Justicia y Derechos Humanos": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": []},
    "Microeconomía I": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Empresa, Economía y Sociedad", "Matemática I"]},
    "Cálculo Financiero": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Matemática II"]},
    "Comercialización": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Organización y Gestión"]},
    "Costos Empresariales": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Contabilidad", "Matemática II"]},
    "Seminario de Pensamiento Nacional Latinoamericano": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": []},
    "Macroeconomía": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Microeconomía I"]},
    "Estadística": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Matemática II"]},
    "Sistemas de Información": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Contabilidad"]},
    "Administración Financiera": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Cálculo Financiero"]},
    "Derecho del Trabajo y la Seguridad Social": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Derecho Comercial"]},
    "Microeconomía II": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Microeconomía I"]},
    "Investigación de Operaciones": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Estadística"]},
    "Principios de Tributación": {"is_tech": True, "periodo": "1° Cuat.", "correlativas": ["Derecho Comercial", "Costos Empresariales"]},
    "Seminario de Integración I": {"is_tech": True, "periodo": "Anual", "correlativas": ["Comercialización", "Administración Financiera"]},
    "Taller de Práctica Preprofesional": {"is_tech": True, "periodo": "2° Cuat.", "correlativas": ["Seminario de Integración I"]},
    "Macroeconomía y Política Económica": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": ["Macroeconomía"]},
    "Tecnología y Ciencia de Datos": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": ["Investigación de Operaciones"]},
    "Seminario Optativo 1": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": []},
    "Seminario Optativo 2": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": []},
    "Gestión Ambiental y Empresa": {"is_tech": False, "periodo": "2° Cuat.", "correlativas": ["Organización y Gestión"]},
    "Taller de Proyecto Empresarial": {"is_tech": False, "periodo": "Anual", "correlativas": ["Seminario de Integración I"]},
    "Planeamiento Estratégico": {"is_tech": False, "periodo": "2° Cuat.", "correlativas": ["Seminario de Integración I"]},
    "Seminario Optativo 3": {"is_tech": False, "periodo": "2° Cuat.", "correlativas": []},
    "Política Económica": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": ["Macroeconomía y Política Económica"]},
    "Inteligencia de Negocios": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": ["Tecnología y Ciencia de Datos"]},
    "Comercio Exterior": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": ["Macroeconomía y Política Económica"]},
    "Inglés I": {"is_tech": False, "periodo": "1° Cuat.", "correlativas": []},
    "Seminario Optativo 4": {"is_tech": False, "periodo": "2° Cuat.", "correlativas": []},
    "Taller de Trabajo Final Integrador": {"is_tech": False, "periodo": "Anual", "correlativas": ["Taller de Proyecto Empresarial"]},
    "Inglés II": {"is_tech": False, "periodo": "2° Cuat.", "correlativas": ["Inglés I"]}
}

TOTAL_LICENCIATURA = 40
TOTAL_TECNICATURA = 25

def get_avatar_slug(usuario, n_aprobadas):
    squad = {"Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa", "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma"}
    char_base = squad.get(usuario, "Marco")
    nivel = 1 if n_aprobadas <= 10 else 2 if n_aprobadas <= 20 else 3 if n_aprobadas <= 30 else 4
    path = os.path.join("assets", f"{char_base}_{nivel}.gif")
    if os.path.exists(path): return path, nivel
    return f"https://api.dicebear.com/7.x/pixel-art/svg?seed={usuario}", nivel

def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=0, ttl=0)
    df.columns = [str(c).strip().capitalize() for c in df.columns]
    
    # Asegurar que las columnas existan
    if "Nota" not in df.columns: df["Nota"] = ""
    if "Cursada" not in df.columns: df["Cursada"] = "Regular"
    
    st.markdown("<h1 class='retro-font' style='text-align:center; font-size:24px;'>SQUAD COMMAND 2026</h1>", unsafe_allow_html=True)
    usuarios = sorted(list(df["Nombre"].unique()))
    usuario = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + usuarios, label_visibility="collapsed")
    
    if usuario == "Seleccionar...": return

    nav_cols = st.columns(4)
    if nav_cols[0].button("🏠 INICIO"): st.session_state.menu = "Inicio"; st.rerun()
    if nav_cols[1].button("📝 PRÓX."): st.session_state.menu = "Proximas"; st.rerun()
    if nav_cols[2].button("✅ HIST."): st.session_state.menu = "Historial"; st.rerun()
    if nav_cols[3].button("👥 GRUPO"): st.session_state.menu = "Grupo"; st.rerun()

    st.markdown("---")

    mis_datos = df[df["Nombre"] == usuario].copy()
    aprobadas_df = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Aprobada"]
    cursando_df = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Cursando"]
    ap_nombres = aprobadas_df["Materia"].tolist()
    
    promedio = pd.to_numeric(aprobadas_df["Nota"], errors='coerce').dropna().mean() if not aprobadas_df.empty else 0.0

    if st.session_state.menu == "Inicio":
        col_av, col_cur = st.columns([1, 2])
        with col_av:
            img_path, _ = get_avatar_slug(usuario, len(aprobadas_df))
            st.image(img_path, width=150)
            st.markdown(f"<p class='retro-font' style='text-align:center; font-size:14px;'>{usuario.upper()}</p>", unsafe_allow_html=True)
            st.metric("PROMEDIO", f"{promedio:.2f}")
            st.link_button("📂 DRIVE SQUAD", "https://drive.google.com/drive/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs", use_container_width=True)
            st.link_button("🏛️ SIU GUARANÍ", "https://estudiantes.unla.edu.ar/autogestion3w/acceso", use_container_width=True)
            st.link_button("💻 CAMPUS UNLA", "https://campus.unla.edu.ar/aulas/login/index.php", use_container_width=True)
        
        with col_cur:
            st.markdown("#### 🏆 OBJETIVOS 2026:")
            st.progress(len(aprobadas_df) / TOTAL_LICENCIATURA)
            st.markdown(f"<p class='hp-bar-text'>PROGRESO TOTAL: {int((len(aprobadas_df)/TOTAL_LICENCIATURA)*100)}%</p>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### ⚔️ MATERIAS EN CURSO:")
            for i, materia in enumerate(cursando_df["Materia"]):
                tipo_c = cursando_df.iloc[i]["Cursada"]
                c_btn_m, c_btn_del = st.columns([4, 1])
                
                if c_btn_m.button(f"✅ {materia} [{tipo_c}]", key=f"mision_{i}"):
                    st.session_state[f"aprobar_{materia}"] = True
                
                if c_btn_del.button("❌", key=f"del_{i}"):
                    df = df.drop(df[(df["Nombre"] == usuario) & (df["Materia"] == materia)].index)
                    conn.update(worksheet=0, data=df)
                    st.rerun()

                if st.session_state.get(f"aprobar_{materia}", False):
                    with st.form(key=f"form_{i}"):
                        nota_input = st.number_input(f"Nota final:", 4, 10, 7)
                        if st.form_submit_button("🎖️ REGISTRAR VICTORIA"):
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == materia), "Estado"] = "Aprobada"
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == materia), "Nota"] = nota_input
                            conn.update(worksheet=0, data=df)
                            st.session_state[f"aprobar_{materia}"] = False
                            st.rerun()

    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        materias_en_registro = mis_datos["Materia"].tolist()
        disp = [m for m, i in PLAN_ESTUDIOS.items() if m not in materias_en_registro and all(c in ap_nombres for c in i["correlativas"])]
        
        for d in disp:
            info = PLAN_ESTUDIOS[d]
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.success(f"🔓 **{d}**")
            tipo_cursada = c2.selectbox("Modalidad:", ["Regular", "Contracursada"], key=f"tipo_{d}")
            if c3.button(f"⚔️ CURSAR", key=f"inscribir_{d}"):
                nueva = pd.DataFrame([{"Nombre": usuario, "Materia": d, "Estado": "Cursando", "Nota": "", "Cursada": tipo_cursada}])
                df_final = pd.concat([df, nueva], ignore_index=True)
                conn.update(worksheet=0, data=df_final)
                st.rerun()

    elif st.session_state.menu == "Grupo":
        st.header("👥 RECUENTO DE TROPAS")
        # Filtramos solo lo que están cursando para ver coincidencias
        en_curso_grupo = df[df["Estado"].str.strip().str.capitalize() == "Cursando"]
        
        if en_curso_grupo.empty:
            st.info("Nadie está cursando materias actualmente.")
        else:
            # Agrupamos por materia para ver quiénes están juntos
            materias_activas = en_curso_grupo["Materia"].unique()
            for mat in materias_activas:
                estudiantes = en_curso_grupo[en_curso_grupo["Materia"] == mat]
                nombres_juntos = ", ".join(estudiantes["Nombre"].tolist())
                cursada_info = estudiantes.iloc[0]["Cursada"]
                st.markdown(f"**{mat}** ({cursada_info})")
                st.info(f"🎖️ Soldados: {nombres_juntos}")

    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE")
        st.dataframe(mis_datos[["Materia", "Estado", "Nota", "Cursada"]].sort_values("Estado"), use_container_width=True, hide_index=True)

if __name__ == "__main__": main()
