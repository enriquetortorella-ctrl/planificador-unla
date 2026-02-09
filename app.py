import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Círculo Rojo", page_icon="🔴", layout="wide")

# Estilos CSS (Recuperando el look oscuro y profesional con toques RPG)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e1117; }
    
    .main-card { background-color: #1e1e26; padding: 20px; border-radius: 15px; border-left: 5px solid #800000; margin-bottom: 15px; }
    .kpi-val { font-size: 28px; font-weight: bold; color: #ff4b4b; }
    .retro-font { font-family: 'Press Start 2P', cursive; font-size: 12px; color: #ff4b4b; }
    
    /* Contenedor Avatar */
    .avatar-frame {
        background: #1e1e26;
        border: 3px solid #ffffff;
        box-shadow: 4px 4px 0px #800000;
        padding: 15px;
        text-align: center;
        border-radius: 10px;
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
def get_avatar_url(seed, level):
    style = "pixel-art" if level < 15 else "bottts-neutral"
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"

# --- 4. APP ---
def main():
    if "menu" not in st.session_state: st.session_state.menu = "Inicio"

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("⚠️ Error conectando a Google Sheets.")
        return

    # --- SIDEBAR (RECUPERADO) ---
    with st.sidebar:
        st.markdown("<h1 style='color:#800000;'>Círculo Rojo</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 ¿Quién sos?", ["Seleccionar..."] + list(df["Nombre"].unique()))
        
        st.markdown("### 📁 MENÚ")
        if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Inicio"; st.rerun()
        if st.button("✅ Mi Historial", use_container_width=True): st.session_state.menu = "Historial"; st.rerun()
        if st.button("📝 Inscribirse", use_container_width=True): st.session_state.menu = "Inscripcion"; st.rerun()
        if st.button("👥 El Grupo", use_container_width=True): st.session_state.menu = "Grupo"; st.rerun()
        if st.button("📚 Apuntes", use_container_width=True): st.session_state.menu = "Apuntes"; st.rerun()
        if st.button("🎒 Inventario RPG", use_container_width=True): st.session_state.menu = "Inventario"; st.rerun()
        
        st.markdown("---")
        st.link_button("🏫 SIU Guaraní", "https://guarani.unla.edu.ar/unla/")

    if usuario == "Seleccionar...":
        st.title("Gestión de Carrera - UNLa")
        st.info("Selecciona tu nombre en el menú lateral.")
        return

    # Datos
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    n_aprobadas = len(aprobadas_list)

    # --- RENDERIZADO DE PÁGINAS ---
    if st.session_state.menu == "Inicio":
        st.subheader(f"¡Hola, {usuario}! 👋")
        
        # KPIs (Recuperados de tu imagen)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Aprobadas", n_aprobadas)
        c2.metric("Cursando", len(mis_datos[mis_datos["Estado"] == "Cursando"]))
        c3.metric("Restantes", 42 - n_aprobadas)
        c4.metric("Progreso", f"{int((n_aprobadas/42)*100)}%")
        st.progress(n_aprobadas/42)

        col_av, col_cur = st.columns([1, 1.5])
        with col_av:
            st.markdown("<div class='avatar-frame'>", unsafe_allow_html=True)
            st.image(get_avatar_url(usuario, n_aprobadas), width=150)
            st.markdown(f"<p class='retro-font'>LVL {n_aprobadas}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_cur:
            st.subheader("📌 Actualmente cursando:")
            cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
            if cursando:
                for m in cursando: st.success(f"📖 {m}")
            else: st.info("No hay cursadas activas.")

    elif st.session_state.menu == "Historial":
        st.header("✅ Mi Historial Académico")
        # Aquí puedes poner la tabla o el multiselect para actualizar
        st.write(mis_datos)

    elif st.session_state.menu == "Inscripcion":
        st.header("📝 Próximas Materias")
        st.write("Materias que ya podés cursar según tus correlativas:")
        disponibles = [m for m, i in PLAN_ESTUDIOS.items() if m not in aprobadas_list and all(c in aprobadas_list for c in i["correlativas"])]
        for d in disponibles: st.info(d)

    elif st.session_state.menu == "Grupo":
        st.header("👥 El Grupo")
        st.write("Aquí va la comparativa de progreso del grupo...")
        st.bar_chart(df.groupby("Nombre")["Estado"].apply(lambda x: (x == "Aprobada").sum()))

    elif st.session_state.menu == "Apuntes":
        st.header("📚 Repositorio de Apuntes")
        st.info("Espacio para compartir drives o carpetas de finales.")

    elif st.session_state.menu == "Inventario":
        st.header("🎒 Inventario RPG")
        ganados = [v for k, v in RECOMPENSAS.items() if n_aprobadas >= k]
        for g in ganados: st.code(g)

if __name__ == "__main__":
    main()
