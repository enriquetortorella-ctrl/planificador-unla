import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo - UNLa", page_icon="🔴", layout="wide")

# Estilos CSS para mejorar la visualización y los KPIs
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px; color: #800000; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 16px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; transition: 0.3s; }
    .stButton>button:hover { background-color: #800000; color: white; border: 1px solid #800000; }
    .main-title { color: #800000; font-weight: bold; font-size: 42px; margin-bottom: 0px; }
    .sub-title { color: #555; font-size: 18px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y CONFIGURACIÓN ---
LISTA_CHICOS = ["Seleccionar...", "Kike", "Maca", "Juli La Más Genia", "Cristian", "Ivan", "Facu Uriarte"]
TOTAL_MATERIAS_CARRERA = 42  # Estimado para Lic. en Economía Empresarial

# --- PLAN DE ESTUDIOS COMPLETO ---
PLAN_ESTUDIOS = {
    "Taller de Producción de Textos": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Introducción a la Matemática": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Contabilidad": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Historia Económica Contemporánea": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Elementos de Matemática": {"anio": 1, "duracion": "2°C", "correlativas": ["Introducción a la Matemática"]},
    "Organización y Gestión": {"anio": 1, "duracion": "2°C", "correlativas": []},
    "Economía y Sociedad": {"anio": 1, "duracion": "2°C", "correlativas": ["Historia Económica Contemporánea"]},
    "Microeconomía": {"anio": 2, "duracion": "ANUAL", "correlativas": ["Historia Económica Contemporánea", "Introducción a la Matemática"]},
    "Derecho Comercial": {"anio": 2, "duracion": "1°C", "correlativas": ["Organización y Gestión"]},
    "Cálculo Financiero y Est. Aplicado": {"anio": 2, "duracion": "ANUAL", "correlativas": ["Elementos de Matemática"]},
    "Costos Empresariales": {"anio": 2, "duracion": "2°C", "correlativas": ["Elementos de Matemática", "Organización y Gestión"]},
    "Derecho Tributario": {"anio": 2, "duracion": "2°C", "correlativas": ["Derecho Comercial"]},
    "Macroeconomía": {"anio": 2, "duracion": "2°C", "correlativas": ["Economía y Sociedad"]},
    "Org. de la Producción y Tecnología": {"anio": 3, "duracion": "1°C", "correlativas": ["Costos Empresariales"]},
    "Derecho del Trabajo y Seg. Social": {"anio": 3, "duracion": "1°C", "correlativas": ["Derecho Tributario"]},
    "Comercialización": {"anio": 3, "duracion": "1°C", "correlativas": ["Costos Empresariales", "Macroeconomía"]},
    "Control de Gestión": {"anio": 3, "duracion": "1°C", "correlativas": ["Costos Empresariales"]},
    "Macroeconomía y Pol. Económica": {"anio": 3, "duracion": "1°C", "correlativas": ["Macroeconomía"]},
    "Comercio Exterior y Ec. Int.": {"anio": 3, "duracion": "1°C", "correlativas": ["Macroeconomía y Pol. Económica"]},
    "Plan de Negocios": {"anio": 3, "duracion": "1°C", "correlativas": ["Control de Gestión", "Comercialización"]},
    "Financiamiento": {"anio": 3, "duracion": "2°C", "correlativas": ["Comercialización"]},
    "Taller de Integración I": {"anio": 3, "duracion": "2°C", "correlativas": ["Comercialización"]},
    "Formulación y Ev. de Proyectos": {"anio": 4, "duracion": "ANUAL", "correlativas": ["Comercio Exterior y Ec. Int.", "Plan de Negocios", "Taller de Integración I"]},
    "Sistemas de Organización": {"anio": 4, "duracion": "1°C", "correlativas": ["Plan de Negocios"]},
    "Economía Industrial": {"anio": 4, "duracion": "1°C", "correlativas": ["Macroeconomía y Pol. Económica", "Economía Bancaria y Financiera"]},
    "Economía Bancaria y Financiera": {"anio": 4, "duracion": "1°C", "correlativas": ["Financiamiento"]},
    "Gestión Ambiental y Empresa": {"anio": 4, "duracion": "1°C", "correlativas": ["Org. de la Producción y Tecnología", "Organización y Gestión"]},
    "Admin. de Recursos Humanos": {"anio": 4, "duracion": "2°C", "correlativas": ["Gestión Ambiental y Empresa"]},
    "Taller de Integración II": {"anio": 4, "duracion": "2°C", "correlativas": ["Sistemas de Organización", "Economía Bancaria y Financiera"]},
    "Mediación y Negociación": {"anio": 5, "duracion": "1°C", "correlativas": ["Admin. de Recursos Humanos"]},
    "Problemas Actuales de la Econ. Arg.": {"anio": 5, "duracion": "1°C", "correlativas": ["Taller de Integración II"]},
    "Seminario: Resp. Social Empresaria": {"anio": 5, "duracion": "2°C", "correlativas": ["Ética y Empresa"]},
    "Seminario: Economía Social": {"anio": 5, "duracion": "2°C", "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Práctica Pre-Profesional": {"anio": 5, "duracion": "2°C", "correlativas": ["Taller de Integración II"]},
    "Taller de Trabajo Final Integrador": {"anio": 5, "duracion": "ANUAL", "correlativas": ["Taller de Integración II", "Taller de Integración I"]},
    "Ética y Empresa": {"anio": 5, "duracion": "2°C", "correlativas": ["Admin. de Recursos Humanos"]},
    "Planeamiento Estratégico": {"anio": 5, "duracion": "2°C", "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Políticas y Estrategias Des. Reg.": {"anio": 5, "duracion": "2°C", "correlativas": ["Taller de Integración II"]},
    "Nivel 1 - Inglés": {"anio": 99, "duracion": "Requisito", "correlativas": []},
    "Nivel 2 - Inglés": {"anio": 99, "duracion": "Requisito", "correlativas": ["Nivel 1 - Inglés"]},
    "Informática (Módulos)": {"anio": 99, "duracion": "Requisito", "correlativas": []}
}

MASCOTAS = {
    "Lagarto 🦎": ["🥚", "🦎", "🐊", "🦖", "👑🦖👑"],
    "Dragón 🐉": ["🥚", "🦎", "🐲", "🐉", "🔥🐲🔥"],
    "Robot 🤖": ["🔩", "🔋", "🦾", "🤖", "🚀🤖🚀"]
}

# --- 3. FUNCIONES DE CONEXIÓN ---
def obtener_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        if "Modalidad" not in df.columns: df["Modalidad"] = "Regular"
        return df, conn
    except:
        return pd.DataFrame(columns=["Nombre", "Materia", "Estado", "Modalidad"]), None

def guardar_cambios(conn, df):
    conn.update(worksheet=0, data=df)
    st.cache_data.clear()
    st.rerun()

# --- 4. LÓGICA DE CALENDARIO AUTOMÁTICO ---
anio_act = datetime.now().year
CALENDARIO_2026 = [
    {"fecha": date(anio_act, 2, 9), "evento": "Inscripción Finales (Feb/Mar)"},
    {"fecha": date(anio_act, 3, 17), "evento": "Inscripción Cursada 1° Cuatrimestre"},
    {"fecha": date(anio_act, 7, 4), "evento": "Inscripción Finales (Julio)"},
    {"fecha": date(anio_act, 7, 28), "evento": "Inscripción Cursada 2° Cuatrimestre"},
]

# --- 5. ESTRUCTURA PRINCIPAL ---
def main():
    df, conn = obtener_datos()
    
    # --- SIDEBAR (BARRA LATERAL) ---
    with st.sidebar:
        st.markdown("<h1 style='color: #800000;'>Círculo Rojo</h1>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 ¿Quién sos?", LISTA_CHICOS)
        st.markdown("---")
        
        # Botones de navegación en lugar de pestañas
        st.write("📂 **MENÚ**")
        if "menu_opcion" not in st.session_state: st.session_state.menu_opcion = "🏠 Inicio"
        
        if st.button("🏠 Inicio"): st.session_state.menu_opcion = "🏠 Inicio"
        if st.button("✅ Mi Historial"): st.session_state.menu_opcion = "✅ Mi Historial"
        if st.button("📅 Inscribirse"): st.session_state.menu_opcion = "📅 Inscribirse"
        if st.button("👥 El Grupo"): st.session_state.menu_opcion = "👥 El Grupo"
        if st.button("📚 Apuntes"): st.session_state.menu_opcion = "📚 Apuntes"
        
        st.markdown("---")
        st.link_button("🏫 SIU Guaraní", "https://estudiantes.unla.edu.ar/")

    if usuario == "Seleccionar...":
        st.markdown("<p class='main-title'>🔴 Planificador UNLa</p>", unsafe_allow_html=True)
        st.info("👈 Seleccioná tu nombre en el menú lateral para cargar tu perfil.")
        return

    # DATOS FILTRADOS
    mis_datos = df[df["Nombre"] == usuario]
    aprobadas = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()
    
    # --- CABECERA CON KPIs ---
    st.markdown(f"<p class='main-title'>¡Hola, {usuario}! 👋</p>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Gestioná tu carrera de Economía Empresarial</p>", unsafe_allow_html=True)
    
    # Alertas automáticas de calendario
    hoy = date.today()
    for ev in CALENDARIO_2026:
        diff = (ev["fecha"] - hoy).days
        if 0 <= diff <= 7:
            st.error(f"🚨 **{ev['evento']}**: {'¡HOY!' if diff == 0 else f'En {diff} días'}")

    # FILA DE KPIs
    k1, k2, k3, k4 = st.columns(4)
    progreso = len(aprobadas) / TOTAL_MATERIAS_CARRERA
    k1.metric("Aprobadas", f"{len(aprobadas)}")
    k2.metric("Cursando", f"{len(cursando)}")
    k3.metric("Finales Restantes", f"{TOTAL_MATERIAS_CARRERA - len(aprobadas)}")
    k4.metric("Progreso", f"{int(progreso*100)}%")
    st.progress(progreso)
    st.markdown("---")

    # --- LÓGICA DE NAVEGACIÓN ---
    opcion = st.session_state.menu_opcion

    if opcion == "🏠 Inicio":
        col_m, col_t = st.columns([1, 2])
        with col_m:
            st.subheader("👾 Tu Mascota")
            masc_tipo = st.selectbox("Elegí:", list(MASCOTAS.keys()))
            evolucion = 0
            if progreso >= 0.8: evolucion = 4
            elif progreso >= 0.5: evolucion = 2
            elif progreso >= 0.2: evolucion = 1
            st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{MASCOTAS[masc_tipo][evolucion]}</h1>", unsafe_allow_html=True)
        with col_t:
            st.subheader("📝 Actualmente cursando:")
            if cursando:
                for m in cursando: st.success(f"📖 {m}")
            else:
                st.info("No tenés cursadas activas. ¡Anotate en la pestaña de Inscripción!")

    elif opcion == "✅ Mi Historial":
        st.subheader("Actualizar Materias Aprobadas")
        nuevas_aprobadas = st.multiselect("Marcá las materias que ya metiste el final:", list(PLAN_ESTUDIOS.keys()), default=aprobadas)
        if st.button("💾 Guardar mi historial"):
            df = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            nuevos_rows = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada", "Modalidad": "Regular"} for m in nuevas_aprobadas]
            df = pd.concat([df, pd.DataFrame(nuevos_rows)], ignore_index=True)
            guardar_cambios(conn, df)

    elif opcion == "📅 Inscribirse":
        st.subheader("Inscripción Ciclo 2026")
        # Lógica de correlatividades
        habilitadas = []
        for mat, info in PLAN_ESTUDIOS.items():
            if mat not in aprobadas and mat not in cursando:
                if all(corr in aprobadas for corr in info["correlativas"]):
                    habilitadas.append(mat)
        
        if habilitadas:
            seleccion = st.multiselect("Materias que podés cursar ahora:", habilitadas)
            mod = st.radio("Modalidad:", ["Regular", "Contra Cursada"])
            if st.button("📝 Confirmar Inscripción"):
                nuevos_registros = [{"Nombre": usuario, "Materia": m, "Estado": "Cursando", "Modalidad": mod} for m in seleccion]
                df = pd.concat([df, pd.DataFrame(nuevos_registros)], ignore_index=True)
                guardar_cambios(conn, df)
        else:
            st.warning("No tenés materias habilitadas por correlatividades o ya estás anotado a todo.")

    elif opcion == "👥 El Grupo":
        st.subheader("📊 Lo que están cursando los demás")
        df_c = df[df["Estado"] == "Cursando"]
        if not df_c.empty:
            resumen = df_c.groupby("Materia")["Nombre"].apply(lambda x: ", ".join(x)).reset_index()
            st.dataframe(resumen, use_container_width=True, hide_index=True)
        else:
            st.write("Nadie se anotó a cursar todavía.")

    elif opcion == "📚 Apuntes":
        st.subheader("Recursos de Estudio")
        st.link_button("📂 Ir al Google Drive del Grupo", "https://drive.google.com/drive/u/0/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs")
        st.info("💡 Recordá subir tus resúmenes para sumar puntos con el grupo.")

if __name__ == "__main__":
    main()
