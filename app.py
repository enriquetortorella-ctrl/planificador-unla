import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Círculo Rojo - UNLa", page_icon="🔴", layout="wide")

# --- CONTROL DE ESTADO ---
if "celebro_analista" not in st.session_state: st.session_state["celebro_analista"] = False
if "celebro_licenciado" not in st.session_state: st.session_state["celebro_licenciado"] = False
if "mensaje_aliento_pendiente" not in st.session_state: st.session_state["mensaje_aliento_pendiente"] = None

# --- BASE DE DATOS DE FECHAS ---
CALENDARIO = [
    {"fecha": "2025-02-24", "evento": "Inscripción Cursada 1° Cuatrimestre 2025"},
    {"fecha": "2025-04-22", "evento": "Inscripción Finales (Turno Mayo)"},
    {"fecha": "2025-05-05", "evento": "Inicio Finales (Turno Mayo)"},
    {"fecha": "2025-07-04", "evento": "Inscripción Finales (Turno Julio)"},
    {"fecha": "2025-07-28", "evento": "Inscripción Cursada 2° Cuatrimestre 2025"},
    {"fecha": "2025-09-20", "evento": "Inscripción Finales (Turno Septiembre)"},
    {"fecha": "2025-11-24", "evento": "Inscripción Finales (Turno Diciembre)"},
    {"fecha": "2025-11-27", "evento": "📝 Inscripción CURSOS DE VERANO 2026"},
    {"fecha": "2026-02-09", "evento": "Inscripción Finales (Turno Feb/Marzo 2026)"},
    {"fecha": "2026-03-17", "evento": "Inscripción Cursada 1° Cuatrimestre 2026"},
]

# --- PLAN DE ESTUDIOS ---
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
    "Nivel 1 - Inglés": {"anio": 99, "duracion": "Requisito", "correlativas": []},
    "Nivel 2 - Inglés": {"anio": 99, "duracion": "Requisito", "correlativas": ["Nivel 1 - Inglés"]},
    "Informática (Módulos)": {"anio": 99, "duracion": "Requisito", "correlativas": []}
}

# --- BIBLIOTECA DE LINKS (CARGADA AUTOMÁTICAMENTE) ---
BIBLIOTECA = {
    "GENERAL_UNLA": "https://drive.google.com/drive/u/0/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs",
    "Taller de Producción de Textos": "https://drive.google.com/drive/folders/1EhI-sOwxbQkkSMWbPT6yGCUQF6xCu7Mp",
    "Introducción a la Matemática": "https://drive.google.com/drive/folders/11ZpKeteyJULu0OoUItyCIvBjNp9PiiSW",
    "Contabilidad": "https://drive.google.com/drive/folders/17arr-tD35OF8hRANI9YhZ8P5BZSNvsCj",
    "Historia Económica Contemporánea": "https://drive.google.com/drive/folders/1dMC-mINSkPHNSTIPFKy5QRIzh8eksJqE",
    "Elementos de Matemática": "https://drive.google.com/drive/folders/1ljBGZrOWp86y39U8O1WSOx7RL41nYsnE",
    "Organización y Gestión": "https://drive.google.com/drive/folders/1T6XHag5mHY6e0ics9EaO-GpdUn05WYTg",
    "Economía y Sociedad": "https://drive.google.com/drive/folders/12Za-sst6bMwFLgOLNwUSc3FY0zpGtJ9p",
    "Microeconomía": "https://drive.google.com/drive/folders/1poMkppjaPtvf2ykpWL1QmqGU38_ojxNa",
    "Derecho Comercial": "https://drive.google.com/drive/folders/122j21UzCzQ8QjX_Dgcc9X5FJ4zMY-LR4",
    "Cálculo Financiero y Est. Aplicado": "https://drive.google.com/drive/folders/185uCtIb_bTE-rUqNgw-8StfgpTPHX3ph",
    "Costos Empresariales": "https://drive.google.com/drive/folders/1IInDSsAVrC7sbXWnwdbyYh4SsfyBNI17",
    "Derecho Tributario": "https://drive.google.com/drive/folders/1cEONRX1FT7uY4iBrew82Zb1mCAUWeCQ0",
    "Macroeconomía": "https://drive.google.com/drive/folders/1p4vcWSdUpGucf0OAnYyUzACeMxXickCg",
    "Org. de la Producción y Tecnología": "https://drive.google.com/drive/folders/1zhp69SR3HUJQ64D_9rO64U6HtmtmhDb1",
    "Derecho del Trabajo y Seg. Social": "https://drive.google.com/drive/folders/1cPRZ9D4dVbV3IN9lVrXK6H0gWgwO_aa4",
    "Comercialización": "https://drive.google.com/drive/folders/1bJVACDFXqEu08w9vdZC64a6fWxdmYuDy",
    "Control de Gestión": "https://drive.google.com/drive/folders/1dq-oqCiiCIeghp1Z6N7IG45o5SnGtWh5",
    "Macroeconomía y Pol. Económica": "https://drive.google.com/drive/folders/1_u9cFsBzTZ8zBAPySWg9j7V0LCoFm7BX",
    "Comercio Exterior y Ec. Int.": "https://drive.google.com/drive/folders/1Hldr_Ku-2hK6LgtW_8UXkDiBeLTd_WyP",
    "Plan de Negocios": "https://drive.google.com/drive/folders/11CMDAhVFoFJWrVxY6gQBuelL_UfMwnKh",
    "Financiamiento": "https://drive.google.com/drive/folders/1Kv4psPor6q4GNxiAzHQK0uAeZDeYEtfz",
    "Taller de Integración I": "https://drive.google.com/drive/folders/1v93Y01tmj82JIgKQfH5L7xc9U3dJ3RwY",
    "Formulación y Ev. de Proyectos": "https://drive.google.com/drive/folders/1Lhmb59meRqhCPyH804t4dcMQcFwGB7mi",
    "Sistemas de Organización": "https://drive.google.com/drive/folders/1wIxV86jdg_cZvtUO-PkOz2fCWCAHbiDU",
    "Economía Industrial": "https://drive.google.com/drive/folders/1uVcQF4MIJxXj-sFNxSq95bMpriDI4YxC",
    "Economía Bancaria y Financiera": "https://drive.google.com/drive/folders/1IuTCxCkmp_q5Ad_C0iR7oTxHH3mmjqzM",
    "Gestión Ambiental y Empresa": "https://drive.google.com/drive/folders/1pkQ8qS1wFvYN35xTlIVhh-exECwGlW1u",
    "Admin. de Recursos Humanos": "https://drive.google.com/drive/folders/1GA7q0li75JoqNZeWSRu1d1AXpFh11Buq",
    "Taller de Integración II": "https://drive.google.com/drive/folders/12yVr49-UE7YyYNLpd7IIQcHRuc536_Xx",
    "Mediación y Negociación": "https://drive.google.com/drive/folders/1NtU2eb3k_UoGTtXnJco2wTPXL8gPWs-A",
    "Problemas Actuales de la Econ. Arg.": "https://drive.google.com/drive/folders/1TqrMohDl2ZpvqSWKZ1ac7ZD1Wn1tpafT",
    "Seminario: Resp. Social Empresaria": "https://drive.google.com/drive/folders/1jx9ixhZkNEO-09qlUcZJhaZgvwmLpDdX",
    "Seminario: Economía Social": "https://drive.google.com/drive/folders/1hFE0dBjixaB2u3TdkgE02bw6iT3I_m4r",
    "Práctica Pre-Profesional": "https://drive.google.com/drive/folders/1fuPVnpuekoowF_hCDJcCCspPSiehhjrb",
    "Taller de Trabajo Final Integrador": "https://drive.google.com/drive/folders/1j7zadBn5vULDUh6HDIGJqR7JhYyKjWKv",
    "Ética y Empresa": "https://drive.google.com/drive/folders/1aVoy2KM614cbtPCnYqnFS1W4-BeeZV5R",
    "Planeamiento Estratégico": "https://drive.google.com/drive/folders/1KmmW8ogOdlND8uGEDeFFiW2S2no5Ff7r",
    "Políticas y Estrategias Des. Reg.": "https://drive.google.com/drive/folders/1Oamrg6k63IWcEoDJCi8EQYtg5cwgDGqa",
    "Nivel 1 - Inglés": "https://drive.google.com/drive/folders/1LYF4hQmvPErJwZCECTLzLCXa2GxQXyMC",
    "Nivel 2 - Inglés": "https://drive.google.com/drive/folders/18w2UQG4rT8SitkT4pJwLN9QDOsYO1_U1",
    "Informática (Módulos)": "https://drive.google.com/drive/folders/1A6kH91BrN3IY4Dt7vFIr8_5T7qM5vJrE",
}

MASCOTAS = {
    "Lagarto 🦎": ["🥚", "🦎", "🐊", "🦖", "👑🦖👑"],
    "Dragón 🐉": ["🥚", "🦎", "🐲", "🐉", "🔥🐲🔥"],
    "Robot 🤖": ["🔩", "🔋", "🦾", "🤖", "🚀🤖🚀"],
    "Planta 🌱": ["🌱", "🌿", "🌳", "🍎", "✨🌳✨"],
    "Mago 🧙": ["📚", "🔮", "🎩", "🧙", "⚡🧙⚡"],
    "Lobo 🐺": ["🦴", "🐕", "🐺", "🌕", "👑🐺👑"]
}

MENSAJES_ALIENTO = {
    "Elementos de Matemática": "¡Qué genio! Aprobaste Elementos, una de las más difíciles. 🚀",
    "Organización y Gestión": "¡Excelente! Superaste Gestión. ¡Un paso gigante! 👏",
    "Costos Empresariales": "¡Increíble! Aprobaste Costos. ¡Estás a otro nivel! 🔥",
    "Microeconomía": "¡Economista en potencia! Muy buena esa aprobada. 📈",
    "Cálculo Financiero y Est. Aplicado": "¡Cálculo adentro! Venís imparable. 💰"
}

# --- CONEXIÓN GOOGLE SHEETS ---
def obtener_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
        # Aseguramos compatibilidad con registros viejos
        if not df.empty and "Modalidad" not in df.columns:
            df["Modalidad"] = "Regular"
        return df, conn
    except Exception as e:
        return pd.DataFrame(columns=["Nombre", "Materia", "Estado", "Modalidad"]), None

def guardar_registro(conn, df_nuevo):
    if conn is None:
        st.error("⚠️ Conexión inestable: Recargá la página (F5).")
        return
    try:
        conn.update(worksheet=0, data=df_nuevo)
        st.cache_data.clear()
        st.toast("¡Cambios guardados!", icon="💾")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- FUNCIONES AUXILIARES ---
def mostrar_mensaje_aliento():
    if st.session_state["mensaje_aliento_pendiente"]:
        mensaje = st.session_state["mensaje_aliento_pendiente"]
        st.toast(mensaje, icon="🎉")
        st.balloons()
        st.session_state["mensaje_aliento_pendiente"] = None

def verificar_titulos(mis_aprobadas, usuario):
    materias_intermedio = [m for m, d in PLAN_ESTUDIOS.items() if d['anio'] in [1, 2, 3]]
    tiene_intermedio = set(materias_intermedio).issubset(set(mis_aprobadas))
    materias_final = list(PLAN_ESTUDIOS.keys())
    tiene_final = set(materias_final).issubset(set(mis_aprobadas))
    resultado = None

    if tiene_final:
        resultado = "Licenciado/a"
        st.markdown(f"""
        <div style="background-color:#d4edda;padding:20px;border-radius:10px;text-align:center;border:2px solid #28a745">
            <h1 style="color:#155724;margin:0;">🎓 ¡FELICITACIONES {usuario.upper()}! 🎓</h1>
            <h3 style="color:#155724;">Ya sos LICENCIADO/A EN ECONOMÍA EMPRESARIAL</h3>
            <p style="color:#155724;">¡Completaste todo el plan de estudios! 🍾</p>
        </div><br>""", unsafe_allow_html=True)
        if not st.session_state["celebro_licenciado"]:
            st.snow(); st.session_state["celebro_licenciado"] = True
    elif tiene_intermedio:
        resultado = "Analista"
        st.markdown(f"""
        <div style="background-color:#fff3cd;padding:20px;border-radius:10px;text-align:center;border:2px solid #ffc107">
            <h1 style="color:#856404;margin:0;">✨ ¡FELICITACIONES {usuario.upper()}! ✨</h1>
            <h3 style="color:#856404;">Título Intermedio: ANALISTA</h3>
            <p style="color:#856404;">¡Completaste 3 años! 🚀</p>
        </div><br>""", unsafe_allow_html=True)
        if not st.session_state["celebro_analista"]:
            st.balloons(); st.session_state["celebro_analista"] = True
    return resultado

# --- APP PRINCIPAL ---
def main():
    st.title("🔴 Planificador Círculo Rojo")
    
    # ALERTAS DE FECHAS
    hoy = datetime.now().date()
    dias_aviso = 10
    for evento in CALENDARIO:
        fecha_evento = datetime.strptime(evento["fecha"], "%Y-%m-%d").date()
        dias_restantes = (fecha_evento - hoy).days
        if dias_restantes == 0: st.success(f"🚨 **¡HOY!** {evento['evento']}")
        elif 0 < dias_restantes <= dias_aviso: st.warning(f"⚠️ **Pronto:** {evento['evento']} (en {dias_restantes} días)")

    st.markdown("---")
    df, conn = obtener_datos()
    
    # --- SIDEBAR ---
    st.sidebar.header("👤 Identificación")
    usuario = st.sidebar.text_input("Tu Nombre:", placeholder="Ej: Enrique").strip().title()
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔗 Accesos Rápidos")
    st.sidebar.link_button("🎓 SIU Guaraní", "https://estudiantes.unla.edu.ar/")
    st.sidebar.link_button("🏫 Campus Virtual", "https://campus.unla.edu.ar/aulas/login/index.php")
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Próximas Fechas")
    eventos_futuros = [e for e in CALENDARIO if datetime.strptime(e["fecha"], "%Y-%m-%d").date() >= hoy]
    if eventos_futuros:
        for e in eventos_futuros[:3]:
            f_str = datetime.strptime(e["fecha"], "%Y-%m-%d").strftime("%d/%m")
            st.sidebar.write(f"• **{f_str}**: {e['evento']}")
    else: st.sidebar.caption("Sin fechas próximas.")

    if not usuario:
        st.info("👈 Escribí tu nombre a la izquierda para comenzar.")
        if not df.empty:
            st.subheader("📊 Estado del Grupo")
            cursada = df[df["Estado"] == "Cursando"]
            if not cursada.empty:
                # --- VISUALIZACIÓN DIVIDIDA PARA NO USUARIOS ---
                resultados = []
                for mat in cursada["Materia"].unique():
                    sub = cursada[cursada["Materia"] == mat]
                    reg = sub[sub["Modalidad"] != "Contra Cursada"]["Nombre"].unique()
                    cc = sub[sub["Modalidad"] == "Contra Cursada"]["Nombre"].unique()
                    resultados.append({
                        "Materia": mat,
                        "Inscriptos": len(reg) + len(cc),
                        "📅 Regular": ", ".join(reg) if len(reg) > 0 else "-",
                        "🔄 Contra Cursada": ", ".join(cc) if len(cc) > 0 else "-"
                    })
                st.dataframe(pd.DataFrame(resultados).sort_values("Inscriptos", ascending=False), hide_index=True, use_container_width=True)
        return

    mis_datos = df[df["Nombre"] == usuario]
    mis_aprobadas = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    mis_cursando = mis_datos[mis_datos["Estado"] == "Cursando"]["Materia"].tolist()

    total = len(PLAN_ESTUDIOS)
    progreso = len(mis_aprobadas) / total if total > 0 else 0
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("👾 Tu Compañero")
    idx_defecto = list(MASCOTAS.keys()).index("Lagarto 🦎")
    tipo_mascota = st.sidebar.selectbox("Elegí tu avatar:", list(MASCOTAS.keys()), index=idx_defecto)
    fases = MASCOTAS[tipo_mascota]
    indice_fase = 0
    if progreso >= 1.0: indice_fase = 4
    elif progreso >= 0.75: indice_fase = 3
    elif progreso >= 0.50: indice_fase = 2
    elif progreso >= 0.25: indice_fase = 1
    avatar_actual = fases[indice_fase]
    st.sidebar.markdown(f"<h1 style='text-align: center; font-size: 60px;'>{avatar_actual}</h1>", unsafe_allow_html=True)
    st.sidebar.caption(f"Nivel {indice_fase + 1}/5")
    st.sidebar.write(f"🎓 **Progreso:** {int(progreso * 100)}%")
    st.sidebar.progress(progreso)

    mostrar_mensaje_aliento()
    titulo_obtenido = verificar_titulos(mis_aprobadas, usuario)
    if titulo_obtenido: st.sidebar.success(f"🏆 **Título:** {titulo_obtenido}")

    # --- PESTAÑAS (AHORA SON 5) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Historial", "📅 Inscripción", "📊 Estado del Grupo", "🎒 Mis Materias", "📚 Biblioteca"])

    with tab1:
        st.subheader("Marcá tus materias aprobadas")
        nuevas_aprobadas = mis_aprobadas.copy()
        for anio in range(1, 6):
            with st.expander(f"Materias de {anio}° Año"):
                cols = st.columns(2)
                materias_anio = [m for m, d in PLAN_ESTUDIOS.items() if d['anio'] == anio]
                for i, materia in enumerate(materias_anio):
                    checked = cols[i % 2].checkbox(materia, value=(materia in mis_aprobadas), key=f"chk_{materia}")
                    if checked and materia not in nuevas_aprobadas: nuevas_aprobadas.append(materia)
                    elif not checked and materia in nuevas_aprobadas: nuevas_aprobadas.remove(materia)
        with st.expander("🌍 Requisitos (Inglés / Informática)"):
            cols = st.columns(2)
            materias_extra = [m for m, d in PLAN_ESTUDIOS.items() if d['anio'] == 99]
            for i, materia in enumerate(materias_extra):
                 checked = cols[i % 2].checkbox(materia, value=(materia in mis_aprobadas), key=f"chk_{materia}")
                 if checked and materia not in nuevas_aprobadas: nuevas_aprobadas.append(materia)
                 elif not checked and materia in nuevas_aprobadas: nuevas_aprobadas.remove(materia)
        if st.button("💾 Guardar Historial"):
            materias_recien_aprobadas = [m for m in nuevas_aprobadas if m not in mis_aprobadas]
            for materia in materias_recien_aprobadas:
                if materia in MENSAJES_ALIENTO:
                    st.session_state["mensaje_aliento_pendiente"] = MENSAJES_ALIENTO[materia]
                    break
            df = df[~((df["Nombre"] == usuario) & (df["Estado"] == "Aprobada"))]
            nuevos = [{"Nombre": usuario, "Materia": m, "Estado": "Aprobada", "Modalidad": "Regular"} for m in nuevas_aprobadas]
            df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
            guardar_registro(conn, df)

    with tab2:
        st.subheader("Inscripción 2025")
        
        # --- SELECTOR DE MODALIDAD ---
        col_mod1, col_mod2 = st.columns(2)
        modalidad = col_mod1.radio("Tipo de Cursada:", ["📅 Cursada Regular (Según Plan)", "🔄 Contra Cursada (Fuera de término)"], horizontal=True)
        modalidad_texto = "Contra Cursada" if "Contra" in modalidad else "Regular"
        
        disponibles = []
        for materia, data in PLAN_ESTUDIOS.items():
            if materia in mis_aprobadas: continue
            if materia in mis_cursando: continue
            faltan = [c for c in data['correlativas'] if c not in mis_aprobadas]
            if not faltan: disponibles.append(materia)
        
        if disponibles:
            with st.form("form_inscripcion"):
                def formato(m):
                    info = PLAN_ESTUDIOS[m]
                    dur = info['duracion']
                    return f"{m}  [{dur}]" if dur != "Requisito" else f"⭐ {m} [REQUISITO]"
                seleccion = st.multiselect("Seleccioná:", disponibles, format_func=formato)
                if st.form_submit_button("Confirmar Inscripción"):
                    nuevos = [{"Nombre": usuario, "Materia": m, "Estado": "Cursando", "Modalidad": modalidad_texto} for m in seleccion]
                    df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
                    guardar_registro(conn, df)
        else: st.success("¡Estás al día!")

    with tab3:
        st.subheader("📊 Estado General del Grupo")
        if not df.empty:
            cursada_gral = df[df["Estado"] == "Cursando"]
            if not cursada_gral.empty:
                # --- VISUALIZACIÓN DIVIDIDA EN COLUMNAS ---
                resultados = []
                for mat in cursada_gral["Materia"].unique():
                    sub = cursada_gral[cursada_gral["Materia"] == mat]
                    # Filtramos por modalidad
                    reg = sub[sub["Modalidad"] != "Contra Cursada"]["Nombre"].unique()
                    cc = sub[sub["Modalidad"] == "Contra Cursada"]["Nombre"].unique()
                    
                    resultados.append({
                        "Materia": mat,
                        "Inscriptos": len(reg) + len(cc),
                        "📅 Regular": ", ".join(reg) if len(reg) > 0 else "-",
                        "🔄 Contra Cursada": ", ".join(cc) if len(cc) > 0 else "-"
                    })
                
                st.dataframe(pd.DataFrame(resultados).sort_values("Inscriptos", ascending=False), hide_index=True, use_container_width=True)
        
        st.divider()
        st.write("🔍 **Buscar materia:**")
        mat_busq = st.selectbox("Elegí materia:", list(PLAN_ESTUDIOS.keys()))
        
        cursando_mat = df[(df["Materia"] == mat_busq) & (df["Estado"] == "Cursando")]
        if not cursando_mat.empty:
            col_a, col_b = st.columns(2)
            
            # Lista Regular
            regulares = cursando_mat[cursando_mat["Modalidad"] != "Contra Cursada"]["Nombre"].unique()
            if len(regulares) > 0:
                col_a.success(f"📅 **Regular ({len(regulares)}):**\n\n" + "\n".join([f"- {n}" for n in regulares]))
            else:
                col_a.info("📅 Regular: Nadie")
                
            # Lista Contra Cursada
            contra = cursando_mat[cursando_mat["Modalidad"] == "Contra Cursada"]["Nombre"].unique()
            if len(contra) > 0:
                col_b.warning(f"🔄 **Contra Cursada ({len(contra)}):**\n\n" + "\n".join([f"- {n}" for n in contra]))
            else:
                col_b.info("🔄 Contra Cursada: Nadie")
                
        else: st.warning("Nadie anotado.")

    with tab4:
        st.subheader(f"Inscripciones de {usuario}")
        if mis_cursando:
            datos = []
            for m in mis_cursando:
                info = PLAN_ESTUDIOS.get(m, {})
                registro = mis_datos[(mis_datos["Materia"] == m) & (mis_datos["Estado"] == "Cursando")]
                mod = registro.iloc[0].get("Modalidad", "Regular") if not registro.empty else "Regular"
                datos.append({
                    "Materia": m, 
                    "Año": f"{info.get('anio', '-')}", 
                    "Modalidad": mod,
                    "Duración": info.get("duracion", "-")
                })
            st.dataframe(pd.DataFrame(datos), use_container_width=True, hide_index=True)
            st.divider()
            borrar = st.multiselect("Dar de baja:", mis_cursando)
            if st.button("Eliminar Seleccionadas"):
                if borrar:
                    df = df[~((df["Nombre"] == usuario) & (df["Materia"].isin(borrar)) & (df["Estado"] == "Cursando"))]
                    guardar_registro(conn, df)
        else: st.info("No te anotaste a nada.")

    with tab5:
        st.subheader("📚 Biblioteca de Apuntes (Drive)")
        st.caption("Elegí una materia para ir a la carpeta compartida.")
        st.link_button("📂 Ir a Carpeta General (UNLa)", BIBLIOTECA["GENERAL_UNLA"], type="primary")
        st.divider()
        opciones_con_link = [m for m in BIBLIOTECA.keys() if m != "GENERAL_UNLA"]
        col1, col2 = st.columns([3, 1])
        materia_elegida = col1.selectbox("Buscar materia específica:", opciones_con_link)
        if materia_elegida:
            link = BIBLIOTECA[materia_elegida]
            col2.link_button(f"📂 Abrir Carpeta", link, type="primary")
        st.info("💡 Consejo: Subí tus resúmenes para ayudar a los demás.")

if __name__ == "__main__":
    main()
