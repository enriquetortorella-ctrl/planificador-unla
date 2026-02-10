import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo - SQUAD", page_icon="🔫", layout="wide")

# CSS Avanzado: Estilo "Mission Start" y Pixel Art
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    
    /* Fondo General Dark */
    .stApp { background-color: #0b0d11; color: #e0e0e0; }

    /* Tarjetas de Materias Estilo Misión */
    .mission-card {
        background: linear-gradient(135deg, #1a1c23 0%, #0d0e12 100%);
        border: 2px solid #444;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 3px 3px 0px #000;
    }

    /* Contenedor del Avatar Retro */
    .avatar-frame {
        background: #161a1e;
        border: 4px double #f1c40f;
        padding: 20px;
        border-radius: 5px;
        text-align: center;
        box-shadow: 0 0 15px rgba(241, 196, 15, 0.2);
    }

    /* Textos con Fuentes de Videojuego */
    .retro-font { font-family: 'Press Start 2P', cursive; color: #f1c40f; text-shadow: 2px 2px #000; }
    .hp-bar-text { font-family: 'Press Start 2P', cursive; font-size: 11px; color: #ff4b4b; margin-bottom: 5px; }
    
    /* Personalización de Métricas de Streamlit */
    [data-testid="stMetricValue"] { font-family: 'Press Start 2P', cursive; font-size: 22px !important; color: #2ecc71 !important; }
    
    /* Botones Sidebar */
    .stButton>button {
        font-family: 'Press Start 2P', cursive;
        font-size: 10px !important;
        background-color: #1e1e26 !important;
        border: 2px solid #444 !important;
        color: white !important;
    }
    .stButton>button:hover { border-color: #f1c40f !important; color: #f1c40f !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PLAN DE ESTUDIOS COMPLETO ---
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

# --- 3. LÓGICA DE AVATARES Y EVOLUCIÓN ---
def get_avatar_slug(usuario, n_aprobadas):
    # Coincidencia con tus archivos de GitHub (Mayúsculas)
    squad = {
        "Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa", 
        "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma"
    }
    char_base = squad.get(usuario, "Marco")
    
    if n_aprobadas <= 10: nivel = 1
    elif n_aprobadas <= 20: nivel = 2
    elif n_aprobadas <= 30: nivel = 3
    else: nivel = 4
    
    nombre_archivo = f"{char_base}_{nivel}.gif"
    path = os.path.join("assets", nombre_archivo)
    
    if os.path.exists(path):
        return path, nivel
    return f"https://api.dicebear.com/7.x/pixel-art/svg?seed={usuario}", 1

# --- 4. APP PRINCIPAL ---
def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        
        # Estandarización de Columnas
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        
        # Limpieza de Nombres de Soldados
        if "Nombre" in df.columns:
            df["Nombre"] = df["Nombre"].replace(["Facu Uriarte", "Facundo Uriarte"], "Facu")
            df["Nombre"] = df["Nombre"].replace(["Juli la mas genia"], "Juli")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    # Menú Lateral
    with st.sidebar:
        st.markdown("<h1 class='retro-font' style='font-size:18px;'>CIRCULO ROJO</h1>", unsafe_allow_html=True)
        nombres = sorted(list(df["Nombre"].unique()))
        usuario = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + nombres)
        st.markdown("---")
        if st.button("🏠 INICIO", use_container_width=True): st.session_state.menu = "Inicio"; st.rerun()
        if st.button("✅ HISTORIAL", use_container_width=True): st.session_state.menu = "Historial"; st.rerun()
        if st.button("📝 PRÓXIMAS", use_container_width=True): st.session_state.menu = "Proximas"; st.rerun()
        if st.button("👥 EL GRUPO", use_container_width=True): st.session_state.menu = "Grupo"; st.rerun()
        st.markdown("---")
        st.link_button("🏫 SIU GUARANÍ", "https://guarani.unla.edu.ar/unla/")

    if usuario == "Seleccionar...":
        st.title("SQUAD COMMAND - UNLa")
        st.info("👈 Selecciona tu soldado en el menú lateral.")
        return

    # Lógica de Datos
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Aprobada"]
    cursando = mis_datos[mis_datos["Estado"].str.strip().str.capitalize() == "Cursando"]
    
    n_aprobadas = len(aprobadas)
    n_cursando = len(cursando)
    aprobadas_nombres = aprobadas["Materia"].tolist()

    # --- PÁGINA: INICIO ---
    if st.session_state.menu == "Inicio":
        st.markdown(f"### ¡Bienvenido, Soldado {usuario}! 👋")
        
        col_av, col_cur = st.columns([1, 2])
        
        with col_av:
            img_path, lvl_actual = get_avatar_slug(usuario, n_aprobadas)
            armas = ["Pistola", "HMG", "Shotgun", "TANK MODE"]
            
            st.markdown('<div class="avatar-frame">', unsafe_allow_html=True)
            st.markdown(f'<p class="hp-bar-text">GEAR: {armas[lvl_actual-1]}</p>', unsafe_allow_html=True)
            st.image(img_path, use_container_width=True)
            st.markdown(f'<p class="retro-font" style="font-size:14px; margin-top:10px;">{usuario.upper()}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="hp-bar-text" style="color:#2ecc71;">LVL: {n_aprobadas}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_cur:
            st.markdown("<p class='retro-font' style='font-size:12px;'>📊 ESTADO ACTUAL</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("AVANCE", f"{int((n_aprobadas/42)*100)}%")
            c2.metric("CURSANDO", n_cursando)
            
            st.progress(n_aprobadas/42)
            st.markdown(f"<p class='hp-bar-text'>↑ {42 - n_aprobadas} MISIONES RESTANTES</p>", unsafe_allow_html=True)
            
            st.markdown("#### 📖 MATERIAS EN CURSO:")
            if not cursando.empty:
                for m in cursando["Materia"]:
                    st.markdown(f"""
                        <div class="mission-card">
                            <span style="color:#888; font-size:10px;">OBJECTIVE:</span><br>
                            <b style="font-size:15px; color:#fff;">{m}</b>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No hay misiones activas. ¡Inscríbete!")

    # --- PÁGINA: HISTORIAL ---
    elif st.session_state.menu == "Historial":
        st.header("✅ REGISTRO DE COMBATE")
        cols_hist = [c for c in ["Materia", "Estado", "Nota"] if c in df.columns]
        st.dataframe(mis_datos[cols_hist].sort_values("Estado"), use_container_width=True, hide_index=True)

    # --- PÁGINA: PRÓXIMAS ---
    elif st.session_state.menu == "Proximas":
        st.header("📝 PRÓXIMOS OBJETIVOS")
        disponibles = [m for m, i in PLAN_ESTUDIOS.items() if m not in aprobadas_nombres and all(c in aprobadas_nombres for c in i["correlativas"])]
        if disponibles:
            for d in disponibles:
                st.markdown(f"<div class='mission-card' style='border-left-color:#2ecc71;'>🔓 {d}</div>", unsafe_allow_html=True)
        else:
            st.error("⚠️ Sin misiones desbloqueadas. Revisa tus correlativas.")

    # --- PÁGINA: GRUPO ---
    elif st.session_state.menu == "Grupo":
        st.header("👥 RECUENTO DE TROPAS")
        # Ranking
        ranking = df[df["Estado"].str.strip().str.capitalize() == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)
        
        st.markdown("---")
        st.subheader("📋 LISTADO ESTRATÉGICO POR MATERIA")
        
        # Cuadro de cursadas grupales
        cursando_ahora = df[df["Estado"].str.strip().str.capitalize() == "Cursando"]
        if not cursando_ahora.empty:
            tabla_grupo = cursando_ahora.groupby("Materia")["Nombre"].agg(['count', lambda x: ', '.join(x)]).reset_index()
            tabla_grupo.columns = ["MATERIA", "SOLDADOS", "INTEGRANTES"]
            st.dataframe(tabla_grupo.sort_values("SOLDADOS", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nadie está cursando materias actualmente.")

if __name__ == "__main__":
    main()
