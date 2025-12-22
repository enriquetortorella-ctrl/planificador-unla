import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="UNLa 2025", page_icon="🦅", layout="wide")

# --- PLAN DE ESTUDIOS ---
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
    "Nivel 1 - Inglés": {"anio": 4, "correlativas": []},
    "Nivel 2 - Inglés": {"anio": 5, "correlativas": ["Nivel 1 - Inglés"]}
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
    st.title("🦅 Planificador UNLa")
    df, conn = obtener_datos()
    
    # --- SIDEBAR ---
    st.sidebar.header("👤 Usuario")
    usuario = st.sidebar.text_input("Tu Nombre:", placeholder="Ej: Enrique").strip().title()

    if not usuario:
        st.info("👈 Escribí tu nombre a la izquierda para entrar.")
        if not df.empty:
            st.divider()
            st.write("📊 **Estado General del Grupo**")
            cursada = df[df["Estado"] == "Cursando"]
            if not cursada.empty:
                resumen = cursada.groupby("Materia")["Nombre"].unique().reset_index()
                resumen["Estudiantes"] = resumen["Nombre"].apply(lambda x: ", ".join(x))
                resumen["Total"] = resumen["Nombre"].apply(len)
                st.dataframe(resumen[["Materia", "Total", "Estudiantes"]], hide_index=True, use_container_width=True)
        return

    # Filtrar mis datos
    mis_datos = df[df["Nombre"] == usuario]
    mis_aprobadas = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    mis_cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()

    # --- PESTAÑAS (Ahora son 4) ---
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Aprobadas", "📅 Inscribirse", "👥 Ver Grupo", "🎒 Mis Inscripciones"])

    # 1. APROBADAS
    with tab1:
        st.write("Marcá lo que ya aprobaste (para desbloquear las siguientes):")
        nuevas = mis_aprobadas.copy()
        with st.expander("Ver lista de materias"):
            for mat in PLAN_ESTUDIOS:
                if st.checkbox(mat, value=(mat in mis_aprobadas), key=f"chk_{mat}"):
                    if mat not in nuevas: nuevas.append(mat)
                elif mat in nuevas: nuevas.remove(mat)
        
        if st.button("Guardar Historial"):
            df = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            nuevos = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada"} for m in nuevas]
            df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
            guardar_registro(conn, df)

    # 2. INSCRIBIRSE
    with tab2:
        disponibles = [m for m, d in PLAN_ESTUDIOS.items() 
                       if m not in mis_aprobadas and m not in mis_cursando 
                       and all(c in mis_aprobadas for c in d['correlativas'])]
        
        if disponibles:
            with st.form("inscripcion"):
                seleccion = st.multiselect("Materias disponibles:", disponibles)
                if st.form_submit_button("¡Anotarme!"):
                    nuevos = [{"Nombre": usuario, "Materia": m, "Estado": "Cursando"} for m in seleccion]
                    df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
                    guardar_registro(conn, df)
        else:
            st.success("No tenés materias pendientes para cursar.")

    # 3. VER GRUPO
    with tab3:
        materia = st.selectbox("Ver quién cursa:", list(PLAN_ESTUDIOS.keys()))
        gente = df[(df["Materia"] == materia) & (df["Estado"] == "Cursando")]["Nombre"].unique()
        if len(gente) > 0:
            st.success(f"Estudiantes ({len(gente)}): {', '.join(gente)}")
        else:
            st.warning("Nadie anotado acá.")

    # 4. MIS INSCRIPCIONES (NUEVA PESTAÑA)
    with tab4:
        st.subheader(f"Materias de {usuario}")
        
        if mis_cursando:
            # Mostrar tabla linda con el año
            datos_tabla = []
            for m in mis_cursando:
                anio = PLAN_ESTUDIOS.get(m, {}).get("anio", "-")
                datos_tabla.append({"Materia": m, "Año": f"{anio}° Año"})
            
            st.table(pd.DataFrame(datos_tabla))
            
            # Opción para borrar
            st.divider()
            st.write("🗑️ **¿Te equivocaste? Date de baja acá:**")
            a_borrar = st.multiselect("Seleccioná la materia para borrar:", mis_cursando)
            
            if st.button("Confirmar Baja"):
                if a_borrar:
                    # Filtramos el DF para sacar esas filas
                    df = df[~((df["Nombre"] == usuario) & (df["Materia"].isin(a_borrar)) & (df["Estado"] == "Cursando"))]
                    guardar_registro(conn, df)
                else:
                    st.warning("Seleccioná al menos una materia para borrar.")
        else:
            st.info("Todavía no te anotaste en ninguna materia para este cuatrimestre.")

if __name__ == "__main__":
    main()
