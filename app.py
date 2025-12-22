import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA (Icono Círculo Rojo) ---
st.set_page_config(page_title="Círculo Rojo - UNLa", page_icon="🔴", layout="wide")

# --- BASE DE DATOS DE FECHAS (Calendario Académico 2025-2026) ---
CALENDARIO = [
    # --- 2025 ---
    {"fecha": "2025-02-24", "evento": "Inscripción Cursada 1° Cuatrimestre 2025"},
    {"fecha": "2025-04-22", "evento": "Inscripción Finales (Turno Mayo)"},
    {"fecha": "2025-05-05", "evento": "Inicio Finales (Turno Mayo)"},
    {"fecha": "2025-07-04", "evento": "Inscripción Finales (Turno Julio - 1° y 2° Llamado)"},
    {"fecha": "2025-07-21", "evento": "Inscripción Finales (Turno Julio - 2° Llamado Complementario)"},
    {"fecha": "2025-08-05", "evento": "Inscripción Cursada 2° Cuatrimestre 2025"},
    {"fecha": "2025-09-20", "evento": "Inscripción Finales (Turno Septiembre)"},
    {"fecha": "2025-11-24", "evento": "Inscripción Finales (Turno Diciembre - 1° y 2° Llamado)"},
    {"fecha": "2025-12-09", "evento": "Inscripción Finales (Turno Diciembre - 2° Llamado Complementario)"},
    
    # --- 2026 ---
    {"fecha": "2026-02-09", "evento": "Inscripción Cursada (Trayecto Inicial 2026)"},
    {"fecha": "2026-03-17", "evento": "Inscripción Cursada 1° Cuatrimestre 2026 (General)"},
    {"fecha": "2026-04-20", "evento": "Inscripción Finales (Turno Mayo 2026)"},
    {"fecha": "2026-07-06", "evento": "Inscripción Finales (Turno Julio 2026)"},
    {"fecha": "2026-08-07", "evento": "Inscripción Cursada 2° Cuatrimestre 2026"},
    {"fecha": "2026-11-30", "evento": "Inscripción Finales (Turno Diciembre 2026)"}
]

# --- PLAN DE ESTUDIOS 2025 ---
PLAN_ESTUDIOS = {
    # 1ER AÑO
    "Taller de Producción de Textos": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Introducción a la Matemática": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Contabilidad": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Historia Económica Contemporánea": {"anio": 1, "duracion": "1°C", "correlativas": []},
    "Elementos de Matemática": {"anio": 1, "duracion": "2°C", "correlativas": ["Introducción a la Matemática"]},
    "Organización y Gestión": {"anio": 1, "duracion": "2°C", "correlativas": []},
    "Economía y Sociedad": {"anio": 1, "duracion": "2°C", "correlativas": ["Historia Económica Contemporánea"]},
    
    # 2DO AÑO
    "Microeconomía": {"anio": 2, "duracion": "ANUAL", "correlativas": ["Historia Económica Contemporánea", "Introducción a la Matemática"]},
    "Derecho Comercial": {"anio": 2, "duracion": "1°C", "correlativas": ["Organización y Gestión"]},
    "Cálculo Financiero y Est. Aplicado": {"anio": 2, "duracion": "ANUAL", "correlativas": ["Elementos de Matemática"]},
    "Costos Empresariales": {"anio": 2, "duracion": "2°C", "correlativas": ["Elementos de Matemática", "Organización y Gestión"]},
    "Derecho Tributario": {"anio": 2, "duracion": "2°C", "correlativas": ["Derecho Comercial"]},
    "Macroeconomía": {"anio": 2, "duracion": "2°C", "correlativas": ["Economía y Sociedad"]},

    # 3ER AÑO
    "Org. de la Producción y Tecnología": {"anio": 3, "duracion": "1°C", "correlativas": ["Costos Empresariales"]},
    "Derecho del Trabajo y Seg. Social": {"anio": 3, "duracion": "1°C", "correlativas": ["Derecho Tributario"]},
    "Comercialización": {"anio": 3, "duracion": "1°C", "correlativas": ["Costos Empresariales", "Macroeconomía"]},
    "Control de Gestión": {"anio": 3, "duracion": "1°C", "correlativas": ["Costos Empresariales"]},
    "Macroeconomía y Pol. Económica": {"anio": 3, "duracion": "1°C", "correlativas": ["Macroeconomía"]},
    "Comercio Exterior y Ec. Int.": {"anio": 3, "duracion": "1°C", "correlativas": ["Macroeconomía y Pol. Económica"]},
    "Plan de Negocios": {"anio": 3, "duracion": "1°C", "correlativas": ["Control de Gestión", "Comercialización"]},
    "Financiamiento": {"anio": 3, "duracion": "2°C", "correlativas": ["Comercialización"]},
    "Taller de Integración I": {"anio": 3, "duracion": "2°C", "correlativas": ["Comercialización"]},

    # 4TO AÑO
    "Formulación y Ev. de Proyectos": {"anio": 4, "duracion": "ANUAL", "correlativas": ["Comercio Exterior y Ec. Int.", "Plan de Negocios", "Taller de Integración I"]},
    "Sistemas de Organización": {"anio": 4, "duracion": "1°C", "correlativas": ["Plan de Negocios"]},
    "Economía Industrial": {"anio": 4, "duracion": "1°C", "correlativas": ["Macroeconomía y Pol. Económica", "Economía Bancaria y Financiera"]},
    "Economía Bancaria y Financiera": {"anio": 4, "duracion": "1°C", "correlativas": ["Financiamiento"]},
    "Gestión Ambiental y Empresa": {"anio": 4, "duracion": "1°C", "correlativas": ["Org. de la Producción y Tecnología", "Organización y Gestión"]},
    "Admin. de Recursos Humanos": {"anio": 4, "duracion": "2°C", "correlativas": ["Gestión Ambiental y Empresa"]},
    "Taller de Integración II": {"anio": 4, "duracion": "2°C", "correlativas": ["Sistemas de Organización", "Economía Bancaria y Financiera"]},

    # 5TO AÑO
    "Mediación y Negociación": {"anio": 5, "duracion": "1°C", "correlativas": ["Admin. de Recursos Humanos"]},
    "Problemas Actuales de la Econ. Arg.": {"anio": 5, "duracion": "1°C", "correlativas": ["Taller de Integración II"]},
    "Seminario: Resp. Social Empresaria": {"anio": 5, "duracion": "2°C", "correlativas": ["Ética y Empresa"]},
    "Seminario: Economía Social": {"anio": 5, "duracion": "2°C", "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Práctica Pre-Profesional": {"anio": 5, "duracion": "2°C", "correlativas": ["Taller de Integración II"]},
    "Taller de Trabajo Final Integrador": {"anio": 5, "duracion": "ANUAL", "correlativas": ["Taller de Integración II", "Taller de Integración I"]},
    "Ética y Empresa": {"anio": 5, "duracion": "2°C", "correlativas": ["Admin. de Recursos Humanos"]},
    "Planeamiento Estratégico": {"anio": 5, "duracion": "2°C", "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Políticas y Estrategias Des. Reg.": {"anio": 5, "duracion": "2°C", "correlativas": ["Taller de Integración II"]},
    
    # EXTRAS
    "Nivel 1 - Inglés": {"anio": 4, "duracion": "Extra", "correlativas": []},
    "Nivel 2 - Inglés": {"anio": 5, "duracion": "Extra", "correlativas": ["Nivel 1 - Inglés"]}
}

# --- CONEXIÓN A GOOGLE SHEETS ---
def obtener_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        return df, conn
    except Exception as e:
        st.error("Error de conexión. Verificá los Secrets.")
        return pd.DataFrame(columns=["Nombre", "Materia", "Estado"]), None

def guardar_registro(conn, df_nuevo):
    try:
        conn.update(worksheet=0, data=df_nuevo)
        st.cache_data.clear()
        st.toast("¡Cambios guardados!", icon="💾")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- APP PRINCIPAL ---
def main():
    st.title("🔴 Planificador Círculo Rojo")
    
    # --- SISTEMA DE ALERTAS (POPUP SUPERIOR) ---
    hoy = datetime.now().date()
    # Margen de aviso (días antes)
    dias_aviso = 7 
    
    for evento in CALENDARIO:
        fecha_evento = datetime.strptime(evento["fecha"], "%Y-%m-%d").date()
        dias_restantes = (fecha_evento - hoy).days
        
        # 1. Alerta de "ABIERTO HOY"
        if dias_restantes == 0:
            st.success(f"🚨 **¡HOY!** {evento['evento']}. ¡No te olvides de anotarte!")
            st.toast(f"¡Hoy es {evento['evento']}!", icon="🔔")
        
        # 2. Alerta de "PRÓXIMAMENTE" (dentro de 7 días)
        elif 0 < dias_restantes <= dias_aviso:
            st.warning(f"⚠️ **Atención:** En {dias_restantes} días comienza: **{evento['evento']}** ({fecha_evento.strftime('%d/%m')})")

    st.markdown("---")
    
    df, conn = obtener_datos()
    
    # --- BARRA LATERAL ---
    st.sidebar.header("👤 Identificación")
    usuario = st.sidebar.text_input("Tu Nombre:", placeholder="Ej: Enrique").strip().title()

    # --- SECCIÓN LINKS IMPORTANTES ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔗 Accesos Rápidos")
    st.sidebar.link_button("🎓 SIU Guaraní", "https://estudiantes.unla.edu.ar/")
    st.sidebar.link_button("🏫 Campus Virtual", "https://campus.unla.edu.ar/aulas/login/index.php")
    st.sidebar.link_button("🏛️ Web UNLa", "https://www.unla.edu.ar/")

    # --- SECCIÓN PRÓXIMAS FECHAS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Próximas Fechas")
    
    # Filtrar eventos futuros y mostrar los próximos 3
    eventos_futuros = [e for e in CALENDARIO if datetime.strptime(e["fecha"], "%Y-%m-%d").date() >= hoy]
    if eventos_futuros:
        for e in eventos_futuros[:3]: # Solo los 3 primeros
            f_obj = datetime.strptime(e["fecha"], "%Y-%m-%d")
            f_str = f_obj.strftime("%d/%m")
            st.sidebar.write(f"• **{f_str}**: {e['evento']}")
    else:
        st.sidebar.caption("No hay fechas próximas cargadas.")


    # Si NO hay usuario, mostramos el resumen
    if not usuario:
        st.info("👈 Escribí tu nombre a la izquierda para comenzar.")
        
        if not df.empty:
            st.subheader("📊 Estado del Grupo")
            cursada = df[df["Estado"] == "Cursando"]
            if not cursada.empty:
                resumen = cursada.groupby("Materia")["Nombre"].unique().reset_index()
                resumen["Estudiantes"] = resumen["Nombre"].apply(lambda x: ", ".join(x))
                resumen["Inscriptos"] = resumen["Nombre"].apply(len)
                
                st.dataframe(
                    resumen[["Materia", "Inscriptos", "Estudiantes"]].sort_values(by="Inscriptos", ascending=False),
                    hide_index=True,
                    use_container_width=True
                )
        return

    # --- CARGAR DATOS DEL USUARIO ---
    mis_datos = df[df["Nombre"] == usuario]
    mis_aprobadas = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    mis_cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()

    # --- BARRA DE PROGRESO ---
    total_materias = len(PLAN_ESTUDIOS)
    aprobadas_count = len(mis_aprobadas)
    progreso = aprobadas_count / total_materias if total_materias > 0 else 0
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"🎓 **Progreso de Carrera:** {int(progreso * 100)}%")
    st.sidebar.progress(progreso)
    
    if progreso == 1.0:
        st.sidebar.balloons()
        st.sidebar.success("¡FELICITACIONES! 🎓🎉")

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Historial", "📅 Inscripción", "📊 Estado del Grupo", "🎒 Mis Materias"])

    # 1. HISTORIAL (APROBADAS)
    with tab1:
        st.subheader("Marcá tus materias aprobadas")
        st.caption("Esto es necesario para que el sistema sepa qué correlativas tenés.")
        
        nuevas_aprobadas = mis_aprobadas.copy()
        
        # Mostrar materias por año
        for anio in range(1, 6):
            with st.expander(f"Materias de {anio}° Año"):
                cols = st.columns(2)
                materias_anio = [m for m, d in PLAN_ESTUDIOS.items() if d['anio'] == anio]
                
                for i, materia in enumerate(materias_anio):
                    checked = cols[i % 2].checkbox(materia, value=(materia in mis_aprobadas), key=f"chk_{materia}")
                    if checked and materia not in nuevas_aprobadas:
                        nuevas_aprobadas.append(materia)
                    elif not checked and materia in nuevas_aprobadas:
                        nuevas_aprobadas.remove(materia)
        
        if st.button("💾 Guardar Historial"):
            df = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            nuevos_registros = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada"} for m in nuevas_aprobadas]
            df = pd.concat([df, pd.DataFrame(nuevos_registros)], ignore_index=True)
            guardar_registro(conn, df)

    # 2. INSCRIPCIÓN (CURSADA)
    with tab2:
        st.subheader("Inscripción 2025")
        
        disponibles = []
        
        for materia, data in PLAN_ESTUDIOS.items():
            if materia in mis_aprobadas: continue
            if materia in mis_cursando: continue
            
            # Chequear correlativas
            faltan = [c for c in data['correlativas'] if c not in mis_aprobadas]
            
            if not faltan:
                disponibles.append(materia)
        
        if disponibles:
            with st.form("form_inscripcion"):
                st.write("##### Materias habilitadas para vos:")
                
                # Formato de visualización
                def formato(m):
                    info = PLAN_ESTUDIOS[m]
                    return f"{m}  [{info['duracion']}]"

                seleccion = st.multiselect("Seleccioná:", disponibles, format_func=formato)
                
                if st.form_submit_button("Confirmar Inscripción"):
                    nuevos = [{"Nombre": usuario, "Materia": m, "Estado": "Cursando"} for m in seleccion]
                    df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
                    guardar_registro(conn, df)
        else:
            st.success("¡Estás al día! No tenés materias pendientes habilitadas.")

    # 3. ESTADO DEL GRUPO (Tabla Completa + Buscador)
    with tab3:
        st.subheader("📊 Estado General del Grupo")
        
        if not df.empty:
            cursada_general = df[df["Estado"] == "Cursando"]
            if not cursada_general.empty:
                resumen = cursada_general.groupby("Materia")["Nombre"].unique().reset_index()
                resumen["Estudiantes"] = resumen["Nombre"].apply(lambda x: ", ".join(x))
                resumen["Inscriptos"] = resumen["Nombre"].apply(len)
                
                st.dataframe(
                    resumen[["Materia", "Inscriptos", "Estudiantes"]].sort_values(by="Inscriptos", ascending=False),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Aún no hay inscripciones en el grupo.")
        
        st.divider()
        st.write("🔍 **Buscar materia específica:**")
        materia_busqueda = st.selectbox("Elegí una materia:", list(PLAN_ESTUDIOS.keys()))
        
        alumnos = df[(df["Materia"] == materia_busqueda) & (df["Estado"] == "Cursando")]["Nombre"].unique()
        
        if len(alumnos) > 0:
            st.success(f"Estudiantes inscriptos en {materia_busqueda} ({len(alumnos)}):")
            st.markdown(f"### 🧑‍🎓 {', '.join(alumnos)}")
        else:
            st.warning("Nadie se anotó en esta materia todavía.")

    # 4. MIS INSCRIPCIONES
    with tab4:
        st.subheader(f"Inscripciones de {usuario}")
        
        if mis_cursando:
            datos_tabla = []
            for m in mis_cursando:
                info = PLAN_ESTUDIOS.get(m, {})
                datos_tabla.append({
                    "Materia": m,
                    "Año": f"{info.get('anio', '-')}°",
                    "Duración": info.get("duracion", "-")
                })
            
            st.dataframe(pd.DataFrame(datos_tabla), use_container_width=True, hide_index=True)
            
            st.divider()
            st.write("🛑 **Dar de baja materias:**")
            a_borrar = st.multiselect("Elegí la materia que querés borrar:", mis_cursando)
            
            if st.button("Eliminar Seleccionadas"):
                if a_borrar:
                    df = df[~((df["Nombre"] == usuario) & (df["Materia"].isin(a_borrar)) & (df["Estado"] == "Cursando"))]
                    guardar_registro(conn, df)
        else:
            st.info("No te anotaste en ninguna materia por ahora.")

if __name__ == "__main__":
    main()
