import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="UNLa 2025", page_icon="🦅", layout="wide")

# --- PLAN DE ESTUDIOS 2025 (Datos Oficiales) ---
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
    st.title("🦅 Planificador UNLa 2025")
    st.markdown("---")
    
    df, conn = obtener_datos()
    
    # --- BARRA LATERAL (Usuario) ---
    st.sidebar.header("👤 Identificación")
    usuario = st.sidebar.text_input("Tu Nombre:", placeholder="Ej: Enrique").strip().title()

    # Si NO hay usuario, mostramos el resumen y cortamos la ejecución
    if not usuario:
        st.info("👈 Por favor, escribí tu nombre en el menú de la izquierda para comenzar.")
        
        if not df.empty:
            st.subheader("📊 Estado del Grupo")
            cursada = df[df["Estado"] == "Cursando"]
            if not cursada.empty:
                resumen = cursada.groupby("Materia")["Nombre"].unique().reset_index()
                resumen["Estudiantes"] = resumen["Nombre"].apply(lambda x: ", ".join(x))
                resumen["Inscriptos"] = resumen["Nombre"].apply(len)
                
                # Tabla resumen
                st.dataframe(
                    resumen[["Materia", "Inscriptos", "Estudiantes"]].sort_values(by="Inscriptos", ascending=False),
                    hide_index=True,
                    use_container_width=True
                )
        return  # <--- Frena acá si no hay nombre

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
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Historial", "📅 Inscripción", "👥 Grupo", "🎒 Mis Materias"])

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

    # 3. VER GRUPO
    with tab3:
        st.subheader("Buscador de Compañeros")
        materia_busqueda = st.selectbox("Elegí una materia:", list(PLAN_ESTUDIOS.keys()))
        
        alumnos = df[(df["Materia"] == materia_busqueda) & (df["Estado"] == "Cursando")]["Nombre"].unique()
        
        if len(alumnos) > 0:
            st.success(f"Estudiantes inscriptos ({len(alumnos)}):")
            st.markdown(f"### 🧑‍🎓 {', '.join(alumnos)}")
        else:
            st.warning("Nadie se anotó en esta materia todavía.")

    # 4. MIS INSCRIPCIONES (Resumen)
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
