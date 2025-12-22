import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="UNLa 2025", page_icon="🦅", layout="wide")

# --- PLAN DE ESTUDIOS OFICIAL (SIU 2025) ---
PLAN_ESTUDIOS = {
    "Taller de Producción de Textos": {"anio": 1, "cuatrimestre": "1°C", "correlativas": []},
    "Introducción a la Matemática": {"anio": 1, "cuatrimestre": "1°C", "correlativas": []},
    "Contabilidad": {"anio": 1, "cuatrimestre": "1°C", "correlativas": []},
    "Historia Económica Contemporánea": {"anio": 1, "cuatrimestre": "1°C", "correlativas": []},
    "Elementos de Matemática": {"anio": 1, "cuatrimestre": "2°C", "correlativas": ["Introducción a la Matemática"]},
    "Organización y Gestión": {"anio": 1, "cuatrimestre": "2°C", "correlativas": []},
    "Economía y Sociedad": {"anio": 1, "cuatrimestre": "2°C", "correlativas": ["Historia Económica Contemporánea"]},
    "Microeconomía": {"anio": 2, "cuatrimestre": "Anual", "correlativas": ["Historia Económica Contemporánea", "Introducción a la Matemática"]},
    "Derecho Comercial": {"anio": 2, "cuatrimestre": "1°C", "correlativas": ["Organización y Gestión"]},
    "Cálculo Financiero y Est. Aplicado": {"anio": 2, "cuatrimestre": "Anual", "correlativas": ["Elementos de Matemática"]},
    "Costos Empresariales": {"anio": 2, "cuatrimestre": "2°C", "correlativas": ["Elementos de Matemática", "Organización y Gestión"]},
    "Derecho Tributario": {"anio": 2, "cuatrimestre": "2°C", "correlativas": ["Derecho Comercial"]},
    "Macroeconomía": {"anio": 2, "cuatrimestre": "2°C", "correlativas": ["Economía y Sociedad"]},
    "Org. de la Producción y Tecnología": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Costos Empresariales"]},
    "Derecho del Trabajo y Seg. Social": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Derecho Tributario"]},
    "Comercialización": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Costos Empresariales", "Macroeconomía"]},
    "Control de Gestión": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Costos Empresariales"]},
    "Macroeconomía y Pol. Económica": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Macroeconomía"]},
    "Comercio Exterior y Ec. Int.": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Macroeconomía y Pol. Económica"]},
    "Plan de Negocios": {"anio": 3, "cuatrimestre": "1°C", "correlativas": ["Control de Gestión", "Comercialización"]},
    "Financiamiento": {"anio": 3, "cuatrimestre": "2°C", "correlativas": ["Comercialización"]},
    "Taller de Integración I": {"anio": 3, "cuatrimestre": "2°C", "correlativas": ["Comercialización"]},
    "Formulación y Ev. de Proyectos": {"anio": 4, "cuatrimestre": "Anual", "correlativas": ["Comercio Exterior y Ec. Int.", "Plan de Negocios", "Taller de Integración I"]},
    "Sistemas de Organización": {"anio": 4, "cuatrimestre": "1°C", "correlativas": ["Plan de Negocios"]},
    "Economía Industrial": {"anio": 4, "cuatrimestre": "1°C", "correlativas": ["Macroeconomía y Pol. Económica", "Economía Bancaria y Financiera"]},
    "Economía Bancaria y Financiera": {"anio": 4, "cuatrimestre": "1°C", "correlativas": ["Financiamiento"]},
    "Gestión Ambiental y Empresa": {"anio": 4, "cuatrimestre": "1°C", "correlativas": ["Org. de la Producción y Tecnología", "Organización y Gestión"]},
    "Admin. de Recursos Humanos": {"anio": 4, "cuatrimestre": "2°C", "correlativas": ["Gestión Ambiental y Empresa"]},
    "Taller de Integración II": {"anio": 4, "cuatrimestre": "2°C", "correlativas": ["Sistemas de Organización", "Economía Bancaria y Financiera"]},
    "Mediación y Negociación": {"anio": 5, "cuatrimestre": "1°C", "correlativas": ["Admin. de Recursos Humanos"]},
    "Problemas Actuales de la Econ. Arg.": {"anio": 5, "cuatrimestre": "1°C", "correlativas": ["Taller de Integración II"]},
    "Seminario: Resp. Social Empresaria": {"anio": 5, "cuatrimestre": "2°C", "correlativas": ["Ética y Empresa"]},
    "Seminario: Economía Social": {"anio": 5, "cuatrimestre": "2°C", "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Práctica Pre-Profesional": {"anio": 5, "cuatrimestre": "2°C", "correlativas": ["Taller de Integración II"]},
    "Taller de Trabajo Final Integrador": {"anio": 5, "cuatrimestre": "Anual", "correlativas": ["Taller de Integración II", "Taller de Integración I"]},
    "Ética y Empresa": {"anio": 5, "cuatrimestre": "2°C", "correlativas": ["Admin. de Recursos Humanos"]},
    "Planeamiento Estratégico": {"anio": 5, "cuatrimestre": "2°C", "correlativas": ["Políticas y Estrategias Des. Reg."]},
    "Políticas y Estrategias Des. Reg.": {"anio": 5, "cuatrimestre": "2°C", "correlativas": ["Taller de Integración II"]},
    "Nivel 1 - Inglés": {"anio": 4, "cuatrimestre": "Extra", "correlativas": []},
    "Nivel 2 - Inglés": {"anio": 5, "cuatrimestre": "Extra", "correlativas": ["Nivel 1 - Inglés"]}
}

ARCHIVO_DATOS = 'datos_grupo_unla.json'

# --- FUNCIONES DE CARGA Y GUARDADO LOCAL ---
def cargar_datos():
    if not os.path.exists(ARCHIVO_DATOS):
        return [] # Retorna lista vacía si no existe
    with open(ARCHIVO_DATOS, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_datos(lista_datos):
    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as f:
        json.dump(lista_datos, f, indent=4, ensure_ascii=False)

# --- INTERFAZ PRINCIPAL ---
def main():
    st.title("🦅 Planificador UNLa 2025 (Local)")
    st.markdown("Base de datos: **Archivo Local en PC**")

    # 1. Cargar Datos Locales
    datos_lista = cargar_datos()
    # Convertir a DataFrame para facilitar el manejo
    if datos_lista:
        df = pd.DataFrame(datos_lista)
    else:
        df = pd.DataFrame(columns=["Nombre", "Materia", "Estado"])
    
    # Sidebar: Identificación
    st.sidebar.header("👤 Tu Usuario")
    usuario = st.sidebar.text_input("Escribí tu Nombre:", placeholder="Ej: Enrique").strip().title()

    if not usuario:
        st.info("👈 Ingresá tu nombre en el menú izquierdo para empezar.")
        
        # MOSTRAR TABLERO GENERAL SI NO HAY USUARIO
        st.divider()
        st.subheader("📊 Estado del Grupo")
        if not df.empty:
            cursada = df[df["Estado"] == "Cursando"]
            if not cursada.empty:
                resumen = cursada.groupby("Materia")["Nombre"].unique().reset_index()
                # Formatear lista de nombres
                resumen["Alumnos"] = resumen["Nombre"].apply(lambda x: ", ".join(x))
                resumen["Cantidad"] = resumen["Nombre"].apply(len)
                
                # Ordenar por cantidad
                resumen = resumen.sort_values(by="Cantidad", ascending=False)
                
                st.dataframe(
                    resumen[["Materia", "Cantidad", "Alumnos"]], 
                    hide_index=True, 
                    use_container_width=True
                )
            else:
                st.info("Nadie se anotó a cursar nada todavía.")
        return

    # Filtrar datos del usuario actual
    mis_datos = df[df["Nombre"] == usuario]
    mis_aprobadas = []
    mis_cursando = []
    
    if not mis_datos.empty:
        mis_aprobadas = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
        mis_cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()

    tab1, tab2, tab3 = st.tabs(["✅ Cargar Aprobadas", "📅 Inscribirse 2025", "👥 Ver Grupo"])

    # --- TAB 1: APROBADAS ---
    with tab1:
        st.write(f"Hola **{usuario}**, marcá lo que ya aprobaste para desbloquear correlativas.")
        
        col1, col2 = st.columns(2)
        todas_materias = list(PLAN_ESTUDIOS.keys())
        mitad = len(todas_materias) // 2
        
        nuevas_aprobadas_temp = mis_aprobadas.copy()
        
        with st.form("form_aprobadas"):
            c1, c2 = st.columns(2)
            for i, mat in enumerate(todas_materias):
                col = c1 if i < mitad else c2
                # Checkbox
                checked = col.checkbox(mat, value=(mat in mis_aprobadas), key=f"ap_{mat}")
                
                if checked and mat not in nuevas_aprobadas_temp:
                    nuevas_aprobadas_temp.append(mat)
                elif not checked and mat in nuevas_aprobadas_temp:
                    nuevas_aprobadas_temp.remove(mat)
            
            if st.form_submit_button("Guardar Historial"):
                # 1. Eliminar registros viejos de "Aprobada" de este usuario
                df = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
                
                # 2. Agregar los nuevos
                nuevos_registros = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada"} for m in nuevas_aprobadas_temp]
                if nuevos_registros:
                    df = pd.concat([df, pd.DataFrame(nuevos_registros)], ignore_index=True)
                
                # 3. Guardar en JSON
                guardar_datos(df.to_dict('records'))
                st.success("¡Historial actualizado correctamente!")
                st.rerun()

    # --- TAB 2: INSCRIPCIÓN ---
    with tab2:
        st.subheader("Inscripción Próximo Cuatrimestre")
        
        materias_disponibles = []
        for materia, data in PLAN_ESTUDIOS.items():
            if materia in mis_aprobadas: continue # Ya aprobada
            if materia in mis_cursando: continue # Ya anotado
            
            # Verificar Correlativas
            faltan = [c for c in data['correlativas'] if c not in mis_aprobadas]
            if not faltan:
                materias_disponibles.append(materia)
        
        if materias_disponibles:
            with st.form("form_inscripcion"):
                seleccion = st.multiselect("Materias disponibles para vos:", materias_disponibles)
                if st.form_submit_button("¡Anotarme!"):
                    # Agregar nuevos cursantes
                    nuevos_registros = [{"Nombre": usuario, "Materia": m, "Estado": "Cursando"} for m in seleccion]
                    if nuevos_registros:
                        df = pd.concat([df, pd.DataFrame(nuevos_registros)], ignore_index=True)
                        guardar_datos(df.to_dict('records'))
                        st.balloons()
                        st.success("¡Inscripción guardada!")
                        st.rerun()
        else:
            st.success("¡Estás al día! No tenés materias pendientes habilitadas.")

        # Mostrar lo que ya está cursando
        if mis_cursando:
            st.info(f"Ya te anotaste en: {', '.join(mis_cursando)}")
            if st.button("Borrar mis inscripciones (Empezar de cero)"):
                # Borrar SOLO las inscripciones (cursando) de este usuario
                df = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Cursando"))]
                guardar_datos(df.to_dict('records'))
                st.warning("Inscripciones borradas.")
                st.rerun()

    # --- TAB 3: SOCIAL ---
    with tab3:
        st.header("¿Quién cursa conmigo?")
        materia_ver = st.selectbox("Elegí materia:", list(PLAN_ESTUDIOS.keys()))
        
        if not df.empty:
            gente = df[(df["Materia"] == materia_ver) & (df["Estado"] == "Cursando")]["Nombre"].unique()
            if len(gente) > 0:
                st.success(f"Son {len(gente)}: {', '.join(gente)}")
            else:
                st.warning("Nadie anotado aún.")
        else:
             st.warning("Base de datos vacía.")

if __name__ == "__main__":
    main()