import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo - UNLa", page_icon="🔴", layout="wide")

# Estilos CSS (RPG Dark Mode & Pixel Art)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Inter:wght@400;700&display=swap');
    
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    .avatar-container {
        border: 4px solid #5d6d7e;
        background: #2c3e50;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 8px 8px 0px #000000;
        margin-bottom: 20px;
    }
    
    .retro-font { 
        font-family: 'Press Start 2P', cursive; 
        font-size: 10px; 
        color: #f1c40f; 
        text-shadow: 2px 2px #000;
    }
    
    .main-card { 
        background-color: #1e1e26; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #800000; 
        margin-bottom: 10px; 
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
    1: "☕ Café Frío", 5: "🎒 Mochila UNLa", 10: "🎧 Auriculares Pro", 
    20: "🔥 Aura Roja", 30: "🗡️ Espada de Tesis", 42: "👑 TITULO"
}

# --- 3. FUNCIONES ---
def get_avatar_slug(usuario):
    # Diccionario ajustado a tus archivos en carpeta assets
    personajes = {
        "Facu": "assets/trevor1.gif",
        "Kike": "assets/trevor2.gif",
        "Sofia": "assets/eri_lv1.gif",
        "Javier": "assets/tarma_lv1.gif",
        "Elena": "assets/fio_lv1.gif"
    }
    path = personajes.get(usuario, "")
    if path and os.path.exists(path):
        return path
    return "https://api.dicebear.com/7.x/pixel-art/svg?seed=placeholder"

# --- 4. APP PRINCIPAL ---
def main():
    if "menu" not in st.session_state:
        st.session_state.menu = "Inicio"

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        
        # Limpieza de Nombres
        df["Nombre"] = df["Nombre"].replace(
            ["Facu Uriarte", "facu uriarte", "Facundo Uriarte", "FACU"], "Facu"
        )
    except Exception as e:
        st.error(f"❌ Error conectando a Google Sheets: {e}")
        return

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("<p class='retro-font' style='font-size:15px;'>CIRCULO ROJO</p>", unsafe_allow_html=True)
        nombres_disponibles = sorted(list(df["Nombre"].unique()))
        usuario = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + nombres_disponibles)
        
        st.markdown("---")
        if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Inicio"; st.rerun()
        if st.button("✅ Mi Historial", use_container_width=True): st.session_state.menu = "Historial"; st.rerun()
        if st.button("📝 Inscribirse", use_container_width=True): st.session_state.menu = "Inscripcion"; st.rerun()
        if st.button("👥 El Grupo", use_container_width=True): st.session_state.menu = "Grupo"; st.rerun()
        if st.button("🎒 Inventario", use_container_width=True): st.session_state.menu = "Inventario"; st.rerun()
        st.markdown("---")
        st.link_button("🏫 SIU Guaraní", "https://guarani.unla.edu.ar/unla/")

    if usuario == "Seleccionar...":
        st.title("Gestión de Carrera - UNLa")
        st.info("👈 Selecciona tu nombre en el panel lateral para cargar tu perfil.")
        return

    # Datos filtrados
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    n_aprobadas = len(aprobadas_list)

    # --- RENDERIZADO DE PÁGINAS ---

    if st.session_state.menu == "Inicio":
        st.subheader(f"¡Bienvenido, {usuario}! 👋")
        
        col_av, col_cur = st.columns([1, 1.5])
        with col_av:
            path_img = get_avatar_slug(usuario)
            st.markdown('<div class="avatar-container">', unsafe_allow_html=True)
            st.markdown('<p class="retro-font" style="font-size:8px;">MISSION START</p>', unsafe_allow_html=True)
            st.image(path_img, width=150)
            st.markdown(f"""
                <div style="background:#1a252f; padding:5px; margin-top:10px; border:2px solid #f1c40f;">
                    <p class="retro-font" style="margin:0;">{usuario.upper()}</p>
                    <p class="retro-font" style="color:#2ecc71; font-size:8px; margin:0;">LVL: {n_aprobadas}</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_cur:
            st.markdown("### 📊 ESTADO ACTUAL")
            c1, c2 = st.columns(2)
            c1.metric("PROGRESO", f"{int((n_aprobadas/42)*100)}%")
            c2.metric("CURSANDO", len(mis_datos[mis_datos["Estado"] == "Cursando"]))
            st.progress(n_aprobadas/42)
            
            st.markdown("#### 📖 CURSANDO AHORA:")
            cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if cursando:
                for m in cursando: st.markdown(f"<div class='main-card'>⚔️ {m}</div>", unsafe_allow_html=True)
            else: st.info("No tienes materias en curso.")

    elif st.session_state.menu == "Historial":
        st.header("✅ Mi Historial Académico")
        st.dataframe(mis_datos[["Materia", "Estado", "Nota"]].sort_values("Estado"), use_container_width=True)

    elif st.session_state.menu == "Inscripcion":
        st.header("📝 Próximas Materias")
        st.write("Materias que puedes cursar según tus correlativas:")
        disponibles = [m for m, i in PLAN_ESTUDIOS.items() if m not in aprobadas_list and all(c in aprobadas_list for c in i["correlativas"])]
        if disponibles:
            for d in disponibles: st.success(f"🔓 **{d}**")
        else: st.warning("No tienes nuevas materias disponibles.")

    elif st.session_state.menu == "Grupo":
        st.header("👥 El Grupo")
        ranking = df[df["Estado"] == "Aprobada"].groupby("Nombre")["Materia"].count().sort_values(ascending=False)
        st.bar_chart(ranking)
        st.dataframe(ranking)

    elif st.session_state.menu == "Inventario":
        st.header("🎒 Inventario RPG")
        ganados = [v for k, v in RECOMPENSAS.items() if n_aprobadas >= k]
        if ganados:
            for g in ganados: st.markdown(f"<div class='main-card' style='border-left-color: gold;'>{g}</div>", unsafe_allow_html=True)
        else: st.info("Sigue aprobando para desbloquear objetos.")

if __name__ == "__main__":
    main()
