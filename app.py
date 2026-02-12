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
    .mission-card {
        background: linear-gradient(135deg, #1a1c23 0%, #0d0e12 100%);
        border: 2px solid #444; border-left: 5px solid #ff4b4b;
        padding: 12px; border-radius: 8px; margin-bottom: 10px; box-shadow: 3px 3px 0px #000;
    }
    .avatar-frame {
        background: #161a1e; border: 3px double #f1c40f; padding: 15px;
        border-radius: 5px; text-align: center; max-width: 160px; margin: 0 auto;
    }
    .retro-font { font-family: 'Press Start 2P', cursive; color: #f1c40f; text-shadow: 2px 2px #000; }
    .hp-bar-text { font-family: 'Press Start 2P', cursive; font-size: 9px; color: #ff4b4b; }
    [data-testid="stMetricValue"] { font-family: 'Press Start 2P', cursive; font-size: 20px !important; color: #2ecc71 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS ---
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

# --- 3. FUNCIONES ---
def get_avatar_slug(usuario, n_aprobadas):
    squad = {"Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa", "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma"}
    char_base = squad.get(usuario, "Marco")
    if n_aprobadas <= 10: nivel = 1
    elif n_aprobadas <= 20: nivel = 2
    elif n_aprobadas <= 30: nivel = 3
    else: nivel = 4
    path = os.path.join("assets", f"{char_base}_{nivel}.gif")
    if os.path.exists(path): return path, nivel
    return f"https://api.dicebear.com/7.x/pixel-art/svg?seed={usuario}", 1

# --- 4. APP ---
def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        df["Nombre"] = df["Nombre"].replace(["Facu Uriarte", "Facundo Uriarte"], "Facu").replace(["Juli la mas genia"], "Juli")
    except Exception:
        st.error("Error de conexión.")
        return

    with st.sidebar:
        st.markdown("<h1 class='retro-font' style='font-size:16px;'>CIRCULO ROJO</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + sorted(list(df["Nombre"].unique())))
        st.markdown("---")
        if st.button("🏠 INICIO", use_container_width=True): st.session_state.menu = "Inicio"; st.rerun()
        if st.button("✅ HISTORIAL", use_container_width=True): st.session_state.menu = "Historial"; st.rerun()
        if st.button("📝 PRÓXIMAS", use_container_width=True): st.session_state.menu = "Proximas"; st.rerun()
        if st.button("👥 EL GRUPO", use_container_width=True): st.session_state.menu = "Grupo"; st.rerun()
        st.markdown("---")
        st.link_button("📚 DRIVE RESÚMENES", "https://google.com")
        st.link_button("🏫 CAMPUS", "https://campus.unla.edu.ar/")
        st.link_button("🏛️ SIU", "https://guarani.unla.edu.ar/unla/")

    if usuario == "Seleccionar...":
        st.title("SQUAD COMMAND - UNLa")
        return

    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Aprobada"]
    cursando = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Cursando"]
    n_aprobadas = len(aprobadas)

    if st.session_state.menu == "Inicio":
        col_av, col_cur = st.columns([1, 2])
        
        with col_av:
            img_path, lvl_actual = get_avatar_slug(usuario, n_aprobadas)
            st.markdown('<div class="avatar-frame">', unsafe_allow_html=True)
            st.image(img_path, width=100)
            st.markdown(f'<p class="retro-font" style="font-size:12px;">{usuario.upper()}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="hp-bar-text" style="color:#2ecc71;">LVL: {n_aprobadas}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # SUSTITUIMOS REPETICIÓN POR UN ESPACIO DE "STATUS"
            st.markdown("---")
            st.markdown("<p class='hp-bar-text'>📜 EQUIPO:</p>", unsafe_allow_html=True)
            st.write("• Laptop Gamer (Cansada)")
            st.write("• Café Frío x2")
            st.write("• Ganas de Recibirse")
        
        with col_cur:
            st.metric("AVANCE DE CARRERA", f"{int((n_aprobadas/42)*100)}%")
            st.progress(n_aprobadas/42)
            st.markdown("#### ⚔️ MATERIAS EN CURSO:")
            if not cursando.empty:
                for m in cursando["Materia"]:
                    st.markdown(f'<div class="mission-card">{m}</div>', unsafe_allow_html=True)
            else:
                st.info("Sin misiones activas.")

    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE")
        st.dataframe(mis_datos[["Materia", "Estado", "Nota"]].sort_values("Estado"), use_container_width=True, hide_index=True)

    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        ap_nombres = aprobadas["Materia"].tolist()
        disp = [m for m, i in PLAN_ESTUDIOS.items() if m not in ap_nombres and all(c in ap_nombres for c in i["correlativas"])]
        for d in disp: st.success(f"🔓 {d}")

    elif st.session_state.menu == "Grupo":
        st.header("👥 RECUENTO DE TROPAS")
        ranking = df[df["Estado"].str.strip().str.capitalize() == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)

if __name__ == "__main__":
    main()
