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
    .hp-bar-text { font-family: 'Press Start 2P', cursive; font-size: 10px; color: #ff4b4b; margin-top: 5px; }
    .hp-bar-text-blue { font-family: 'Press Start 2P', cursive; font-size: 10px; color: #3498db; margin-top: 5px; }
    .cuatri-header { 
        font-family: 'Press Start 2P', cursive; 
        color: #3498db; 
        font-size: 16px; 
        margin-top: 30px; 
        padding: 10px;
        border-bottom: 2px solid #3498db;
    }
    .materia-card {
        background-color: #1a1c23;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #f1c40f;
    }
    [data-testid="stMetricValue"] { font-family: 'Press Start 2P', cursive; font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS CON CRÉDITOS (PUNTOS) ---
# Datos extraídos del plan oficial UNLa
PLAN_ESTUDIOS = {
    "Introducción a Economía Empresarial": {"periodo": "1° Cuat.", "puntos": 4, "correlativas": []},
    "Historia Económica Contemporánea": {"periodo": "1° Cuat.", "puntos": 5, "correlativas": []},
    "Contabilidad": {"periodo": "1° Cuat.", "puntos": 8, "correlativas": []},
    "Matemática I": {"periodo": "1° Cuat.", "puntos": 8, "correlativas": []},
    "Taller de Comunicación y Producción de Textos": {"periodo": "1° Cuat.", "puntos": 5, "correlativas": []},
    "Empresa, Economía y Sociedad": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Historia Económica Contemporánea"]},
    "Organización y Gestión": {"periodo": "2° Cuat.", "puntos": 7, "correlativas": []},
    "Matemática II": {"periodo": "2° Cuat.", "puntos": 8, "correlativas": ["Matemática I"]},
    "Derecho Comercial": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Organización y Gestión"]},
    "Seminario de Justicia y Derechos Humanos": {"periodo": "2° Cuat.", "puntos": 3, "correlativas": []},
    "Microeconomía I": {"periodo": "1° Cuat.", "puntos": 8, "correlativas": ["Empresa, Economía y Sociedad", "Matemática I"]},
    "Cálculo Financiero": {"periodo": "1° Cuat.", "puntos": 6, "correlativas": ["Matemática II"]},
    "Comercialización": {"periodo": "1° Cuat.", "puntos": 6, "correlativas": ["Organización y Gestión"]},
    "Costos Empresariales": {"periodo": "1° Cuat.", "puntos": 8, "correlativas": ["Contabilidad", "Matemática II"]},
    "Seminario de Pensamiento Nacional Latinoamericano": {"periodo": "1° Cuat.", "puntos": 3, "correlativas": []},
    "Macroeconomía": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Microeconomía I"]},
    "Estadística": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Matemática II"]},
    "Sistemas de Información": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Contabilidad"]},
    "Administración Financiera": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Cálculo Financiero"]},
    "Derecho del Trabajo y la Seguridad Social": {"periodo": "2° Cuat.", "puntos": 6, "correlativas": ["Derecho Comercial"]},
    "Microeconomía II": {"periodo": "1° Cuat.", "puntos": 6, "correlativas": ["Microeconomía I"]},
    "Investigación de Operaciones": {"periodo": "1° Cuat.", "puntos": 6, "correlativas": ["Estadística"]},
    "Principios de Tributación": {"periodo": "1° Cuat.", "puntos": 6, "correlativas": ["Derecho Comercial", "Costos Empresariales"]},
    "Seminario de Integración I": {"periodo": "Anual", "puntos": 8, "correlativas": ["Comercialización", "Administración Financiera"]},
    "Taller de Práctica Preprofesional": {"periodo": "2° Cuat.", "puntos": 5, "correlativas": ["Seminario de Integración I"]}
}

CREDITOS_TOTAL_TECNICATURA = 120
CREDITOS_TOTAL_LICENCIATURA = 240

def get_avatar_slug(usuario, n_aprobadas):
    squad = {"Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa", "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma"}
    char_base = squad.get(usuario, "Marco")
    nivel = 1 if n_aprobadas <= 10 else 2 if n_aprobadas <= 20 else 3 if n_aprobadas <= 30 else 4
    return os.path.join("assets", f"{char_base}_{nivel}.gif")

def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=0, ttl=0)
    df.columns = [str(c).strip().capitalize() for c in df.columns]
    
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
    
    # --- CÁLCULO DE PUNTOS REALES ---
    puntos_logrados = sum([PLAN_ESTUDIOS.get(m, {}).get("puntos", 0) for m in aprobadas_df["Materia"]])
    promedio = pd.to_numeric(aprobadas_df["Nota"], errors='coerce').dropna().mean() if not aprobadas_df.empty else 0.0

    if st.session_state.menu == "Inicio":
        col_av, col_cur = st.columns([1, 2])
        with col_av:
            img_path = get_avatar_slug(usuario, len(aprobadas_df))
            st.image(img_path, width=150)
            st.metric("PUNTOS", puntos_logrados)
            st.metric("PROMEDIO", f"{promedio:.2f}")
            st.link_button("📂 DRIVE", "https://drive.google.com/drive/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs", use_container_width=True)
        
        with col_cur:
            st.markdown("#### 🏆 PROGRESO POR CRÉDITOS (PUNTOS):")
            
            # HP Barra Tecnicatura
            prog_tec = min(puntos_logrados / CREDITOS_TOTAL_TECNICATURA, 1.0)
            st.progress(prog_tec)
            st.markdown(f"<p class='hp-bar-text-blue'>TECNICATURA: {puntos_logrados}/{CREDITOS_TOTAL_TECNICATURA} pts ({int(prog_tec*100)}%)</p>", unsafe_allow_html=True)
            
            # HP Barra Licenciatura
            prog_lic = min(puntos_logrados / CREDITOS_TOTAL_LICENCIATURA, 1.0)
            st.progress(prog_lic)
            st.markdown(f"<p class='hp-bar-text'>LICENCIATURA: {puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA} pts ({int(prog_lic*100)}%)</p>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### ⚔️ MATERIAS EN CURSO:")
            for i, row in cursando_df.iterrows():
                materia, tipo_c = row["Materia"], row["Cursada"]
                c_btn_m, c_btn_del = st.columns([4, 1])
                if c_btn_m.button(f"✅ {materia} [{tipo_c}]", key=f"mision_{i}"):
                    st.session_state[f"aprobar_{materia}"] = True
                if c_btn_del.button("❌", key=f"del_{i}"):
                    df = df.drop(df[(df["Nombre"] == usuario) & (df["Materia"] == materia)].index)
                    conn.update(worksheet=0, data=df); st.rerun()

                if st.session_state.get(f"aprobar_{materia}", False):
                    with st.form(key=f"form_{i}"):
                        nota_input = st.number_input(f"Nota final:", 4, 10, 7)
                        if st.form_submit_button("🎖️ REGISTRAR VICTORIA"):
                            df.loc[(df["Nombre"] == usuario) & (df["Materia"] == materia), ["Estado", "Nota"]] = ["Aprobada", nota_input]
                            conn.update(worksheet=0, data=df)
                            st.session_state[f"aprobar_{materia}"] = False; st.rerun()

    elif st.session_state.menu == "Grupo":
        st.header("👥 DESPLIEGUE POR CUATRIMESTRE REAL")
        en_curso = df[df["Estado"].str.strip().str.capitalize() == "Cursando"].copy()
        if not en_curso.empty:
            for periodo in ["1° Cuatrimestre", "2° Cuatrimestre"]:
                st.markdown(f"<div class='cuatri-header'>{periodo}</div>", unsafe_allow_html=True)
                materias_periodo = en_curso[en_curso["Materia"].apply(lambda x: PLAN_ESTUDIOS.get(x, {}).get("periodo") == periodo[:7])]
                for mat in materias_periodo["Materia"].unique():
                    soldados = materias_periodo[materias_periodo["Materia"] == mat]
                    lista = ", ".join([f"{r['Nombre']} ({r['Cursada']})" for _, r in soldados.iterrows()])
                    st.markdown(f"<div class='materia-card'><strong>{mat}</strong> ({PLAN_ESTUDIOS.get(mat,{}).get('puntos')} pts)<br>🎖️ {lista}</div>", unsafe_allow_html=True)

    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        ya_registradas = mis_datos["Materia"].tolist()
        aprobadas = aprobadas_df["Materia"].tolist()
        disp = [m for m, i in PLAN_ESTUDIOS.items() if m not in ya_registradas and all(c in aprobadas for c in i["correlativas"])]
        for d in disp:
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.success(f"🔓 **{d}** ({PLAN_ESTUDIOS[d]['puntos']} pts)")
            tipo = c2.selectbox("Modalidad:", ["Regular", "Contracursada"], key=f"t_{d}")
            if c3.button("⚔️ CURSAR", key=f"in_{d}"):
                nueva = pd.DataFrame([{"Nombre": usuario, "Materia": d, "Estado": "Cursando", "Cursada": tipo}])
                df = pd.concat([df, nueva], ignore_index=True)
                conn.update(worksheet=0, data=df); st.rerun()

    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE")
        st.dataframe(mis_datos[["Materia", "Estado", "Nota", "Cursada"]].sort_values("Estado"), use_container_width=True, hide_index=True)

if __name__ == "__main__": main()
