import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
import os
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────
# 1. CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(page_title="Círculo Rojo - SQUAD", page_icon="🔫", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

    .stApp { background-color: #0b0d11; color: #e0e0e0; }

    .retro-font {
        font-family: 'Press Start 2P', cursive;
        color: #f1c40f;
        text-shadow: 2px 2px #000;
    }
    .hp-bar-text {
        font-family: 'Press Start 2P', cursive;
        font-size: 10px;
        color: #ff4b4b;
        margin-top: 5px;
    }
    .hp-bar-text-blue {
        font-family: 'Press Start 2P', cursive;
        font-size: 10px;
        color: #3498db;
        margin-top: 5px;
    }
    .cuatri-header {
        font-family: 'Press Start 2P', cursive;
        color: #3498db;
        font-size: 16px;
        margin-top: 30px;
        padding: 10px;
        border-bottom: 2px solid #3498db;
    }
    .materia-card {
        background-color: #1a1c23;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #f1c40f;
    }
    .warning-card {
        background-color: #1a1200;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #ff4b4b;
    }
    .exam-card {
        background-color: #0d1a2e;
        border-radius: 5px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #3498db;
    }
    .exam-urgent {
        border-left: 4px solid #ff4b4b !important;
        background-color: #1a0d0d !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Press Start 2P', cursive;
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 2. PLAN DE ESTUDIOS CON CRÉDITOS
# ─────────────────────────────────────────────
PLAN_ESTUDIOS = {
    "Introducción a Economía Empresarial":               {"periodo": "1° Cuat.", "puntos": 4,  "correlativas": []},
    "Historia Económica Contemporánea":                  {"periodo": "1° Cuat.", "puntos": 5,  "correlativas": []},
    "Contabilidad":                                      {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": []},
    "Matemática I":                                      {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": []},
    "Taller de Comunicación y Producción de Textos":     {"periodo": "1° Cuat.", "puntos": 5,  "correlativas": []},
    "Empresa, Economía y Sociedad":                      {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Historia Económica Contemporánea"]},
    "Organización y Gestión":                            {"periodo": "2° Cuat.", "puntos": 7,  "correlativas": []},
    "Matemática II":                                     {"periodo": "2° Cuat.", "puntos": 8,  "correlativas": ["Matemática I"]},
    "Derecho Comercial":                                 {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Organización y Gestión"]},
    "Seminario de Justicia y Derechos Humanos":          {"periodo": "2° Cuat.", "puntos": 3,  "correlativas": []},
    "Microeconomía I":                                   {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Empresa, Economía y Sociedad", "Matemática I"]},
    "Cálculo Financiero":                                {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Matemática II"]},
    "Comercialización":                                  {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Organización y Gestión"]},
    "Costos Empresariales":                              {"periodo": "1° Cuat.", "puntos": 8,  "correlativas": ["Contabilidad", "Matemática II"]},
    "Seminario de Pensamiento Nacional Latinoamericano": {"periodo": "1° Cuat.", "puntos": 3,  "correlativas": []},
    "Macroeconomía":                                     {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Microeconomía I"]},
    "Estadística":                                       {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Matemática II"]},
    "Sistemas de Información":                           {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Contabilidad"]},
    "Administración Financiera":                         {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Cálculo Financiero"]},
    "Derecho del Trabajo y la Seguridad Social":         {"periodo": "2° Cuat.", "puntos": 6,  "correlativas": ["Derecho Comercial"]},
    "Microeconomía II":                                  {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Microeconomía I"]},
    "Investigación de Operaciones":                      {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Estadística"]},
    "Principios de Tributación":                         {"periodo": "1° Cuat.", "puntos": 6,  "correlativas": ["Derecho Comercial", "Costos Empresariales"]},
    "Seminario de Integración I":                        {"periodo": "Anual",    "puntos": 8,  "correlativas": ["Comercialización", "Administración Financiera"]},
    "Taller de Práctica Preprofesional":                 {"periodo": "2° Cuat.", "puntos": 5,  "correlativas": ["Seminario de Integración I"]},
}

# Áreas para radar chart
AREAS = {
    "Matemática":     ["Matemática I", "Matemática II", "Cálculo Financiero", "Estadística", "Investigación de Operaciones"],
    "Económica":      ["Introducción a Economía Empresarial", "Historia Económica Contemporánea",
                       "Empresa, Economía y Sociedad", "Microeconomía I", "Microeconomía II", "Macroeconomía"],
    "Administración": ["Organización y Gestión", "Comercialización", "Costos Empresariales",
                       "Administración Financiera", "Sistemas de Información", "Seminario de Integración I",
                       "Taller de Práctica Preprofesional", "Seminario de Pensamiento Nacional Latinoamericano",
                       "Seminario de Justicia y Derechos Humanos"],
    "Jurídica":       ["Derecho Comercial", "Derecho del Trabajo y la Seguridad Social", "Principios de Tributación"],
    "Comunicación":   ["Taller de Comunicación y Producción de Textos", "Contabilidad"],
}

CREDITOS_TOTAL_TECNICATURA  = 120
CREDITOS_TOTAL_LICENCIATURA = 240
TOTAL_MATERIAS = len(PLAN_ESTUDIOS)

SQUAD_MAP = {
    "Facu": "Allen", "Ivan": "Trevor", "Maca": "Alisa",
    "Juli": "Nadia", "Kike": "Marco", "Cristian": "Tarma",
}


# ─────────────────────────────────────────────
# 3. HELPERS
# ─────────────────────────────────────────────
def get_avatar_path(usuario: str, n_aprobadas: int) -> str:
    char  = SQUAD_MAP.get(usuario, "Marco")
    nivel = 1 if n_aprobadas <= 10 else 2 if n_aprobadas <= 20 else 3 if n_aprobadas <= 30 else 4
    return os.path.join("assets", f"{char}_{nivel}.gif")


def normalizar_estado(df: pd.DataFrame) -> pd.DataFrame:
    df["Estado"] = df["Estado"].astype(str).str.strip().str.capitalize()
    return df


def calcular_promedio_ponderado(aprobadas_df: pd.DataFrame) -> float:
    total_pts = total_pond = 0
    for _, row in aprobadas_df.iterrows():
        nota = pd.to_numeric(row.get("Nota", ""), errors="coerce")
        pts  = PLAN_ESTUDIOS.get(row["Materia"], {}).get("puntos", 0)
        if pd.notna(nota) and pts > 0:
            total_pond += nota * pts
            total_pts  += pts
    return (total_pond / total_pts) if total_pts > 0 else 0.0


def asignar_periodo_real(materia: str, cursada: str) -> str:
    teorico = PLAN_ESTUDIOS.get(materia, {}).get("periodo", "1° Cuat.")
    if cursada == "Contracursada":
        return "2° Cuatrimestre" if teorico == "1° Cuat." else "1° Cuatrimestre"
    return "1° Cuatrimestre" if teorico in ("1° Cuat.", "Anual") else "2° Cuatrimestre"


def guardar_df(conn, df: pd.DataFrame):
    conn.update(worksheet=0, data=df)


def asegurar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "Nota": "", "Cursada": "Regular", "Estado": "Cursando",
        "Nota_parcial1": "", "Nota_parcial2": "",
        "Fecha_aprobacion": "", "Fecha_examen": "",
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
    return df


def dias_restantes(fecha_str: str):
    try:
        fecha = datetime.strptime(str(fecha_str).strip(), "%Y-%m-%d").date()
        return (fecha - date.today()).days
    except Exception:
        return None


def estimar_egreso(aprobadas_df: pd.DataFrame):
    if "Fecha_aprobacion" not in aprobadas_df.columns:
        return None
    fechas = pd.to_datetime(aprobadas_df["Fecha_aprobacion"], errors="coerce").dropna()
    if len(fechas) < 2:
        return None
    fechas_sorted = fechas.sort_values()
    delta_dias    = (fechas_sorted.iloc[-1] - fechas_sorted.iloc[0]).days
    if delta_dias <= 0:
        return None
    ritmo         = len(aprobadas_df) / delta_dias
    materias_rest = TOTAL_MATERIAS - len(aprobadas_df)
    dias_rest     = materias_rest / ritmo
    fecha_est     = date.today() + timedelta(days=dias_rest)
    return fecha_est.strftime("%B %Y")


def confetti_html() -> str:
    return """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
    (function() {
        var duration = 3000;
        var animationEnd = Date.now() + duration;
        var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };
        function randomInRange(min, max) { return Math.random() * (max - min) + min; }
        var interval = setInterval(function() {
            var timeLeft = animationEnd - Date.now();
            if (timeLeft <= 0) return clearInterval(interval);
            var particleCount = 50 * (timeLeft / duration);
            confetti(Object.assign({}, defaults, {
                particleCount,
                origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
                colors: ['#f1c40f','#ff4b4b','#3498db','#2ecc71']
            }));
            confetti(Object.assign({}, defaults, {
                particleCount,
                origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
                colors: ['#f1c40f','#ff4b4b','#3498db','#2ecc71']
            }));
        }, 250);
    })();
    </script>
    """


def _get_examenes_proximos(mis_datos: pd.DataFrame) -> list:
    resultado = []
    for _, row in mis_datos[mis_datos["Estado"].isin(["Cursando", "Aprobada"])].iterrows():
        fecha_str = str(row.get("Fecha_examen", "")).strip()
        if not fecha_str or fecha_str in ("", "nan", "NaT", "None"):
            continue
        dias = dias_restantes(fecha_str)
        resultado.append({"materia": row["Materia"], "fecha_str": fecha_str, "dias": dias})
    resultado.sort(key=lambda x: (x["dias"] is None, x["dias"] or 9999))
    return resultado


# ─────────────────────────────────────────────
# 4. GRÁFICOS
# ─────────────────────────────────────────────
def grafico_arbol_correlativas(aprobadas: list, cursando: list) -> go.Figure:
    materias = list(PLAN_ESTUDIOS.keys())

    def get_capa(m, visitados=None):
        if visitados is None:
            visitados = set()
        if m in visitados:
            return 0
        visitados.add(m)
        deps = PLAN_ESTUDIOS[m]["correlativas"]
        if not deps:
            return 0
        return 1 + max(get_capa(d, visitados.copy()) for d in deps)

    capas = {m: get_capa(m) for m in materias}

    capa_grupos = {}
    for m, c in capas.items():
        capa_grupos.setdefault(c, []).append(m)

    pos = {}
    for capa, mats in capa_grupos.items():
        for j, m in enumerate(mats):
            pos[m] = (capa * 3.0, j * 2.0 - len(mats) * 1.0)

    edge_x, edge_y = [], []
    for m, info in PLAN_ESTUDIOS.items():
        for cor in info["correlativas"]:
            x0, y0 = pos[cor]
            x1, y1 = pos[m]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    colores, simbolos, textos_hover = [], [], []
    for m in materias:
        if m in aprobadas:
            colores.append("#2ecc71")
            simbolos.append("circle")
        elif m in cursando:
            colores.append("#f1c40f")
            simbolos.append("diamond")
        elif all(c in aprobadas for c in PLAN_ESTUDIOS[m]["correlativas"]):
            colores.append("#3498db")
            simbolos.append("circle")
        else:
            colores.append("#555")
            simbolos.append("circle")
        pts  = PLAN_ESTUDIOS[m]["puntos"]
        cors = ", ".join(PLAN_ESTUDIOS[m]["correlativas"]) or "Ninguna"
        textos_hover.append(f"<b>{m}</b><br>Créditos: {pts}<br>Correlativas: {cors}")

    node_x = [pos[m][0] for m in materias]
    node_y = [pos[m][1] for m in materias]

    labels = []
    for m in materias:
        palabras = m.split()
        labels.append(" ".join(palabras[:2]) + ("…" if len(palabras) > 2 else ""))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="#444", width=1.5),
        hoverinfo="none", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=22, color=colores, symbol=simbolos,
                    line=dict(color="#0b0d11", width=2)),
        text=labels,
        textposition="top center",
        textfont=dict(size=9, color="#e0e0e0"),
        hovertext=textos_hover,
        hoverinfo="text",
        showlegend=False,
    ))
    fig.update_layout(
        paper_bgcolor="#0b0d11", plot_bgcolor="#0b0d11",
        font=dict(color="#e0e0e0"),
        height=700,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


def grafico_radar(aprobadas_df: pd.DataFrame) -> go.Figure:
    categorias = list(AREAS.keys())
    valores = []
    for area, mats in AREAS.items():
        aprobadas_area = sum(1 for m in mats if m in aprobadas_df["Materia"].values)
        valores.append(round(aprobadas_area / len(mats) * 100, 1) if mats else 0)

    fig = go.Figure(go.Scatterpolar(
        r=valores + [valores[0]],
        theta=categorias + [categorias[0]],
        fill="toself",
        fillcolor="rgba(52, 152, 219, 0.25)",
        line=dict(color="#3498db", width=2),
        marker=dict(color="#f1c40f", size=8),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1c23",
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color="#aaa", size=9),
                            gridcolor="#333", linecolor="#333"),
            angularaxis=dict(tickfont=dict(color="#e0e0e0", size=11),
                             gridcolor="#333", linecolor="#333"),
        ),
        paper_bgcolor="#0b0d11",
        font=dict(color="#e0e0e0"),
        height=380,
        margin=dict(l=60, r=60, t=20, b=20),
        showlegend=False,
    )
    return fig


def grafico_progreso_tiempo(aprobadas_df: pd.DataFrame):
    if "Fecha_aprobacion" not in aprobadas_df.columns:
        return None
    df_f = aprobadas_df.copy()
    df_f["Fecha_aprobacion"] = pd.to_datetime(df_f["Fecha_aprobacion"], errors="coerce")
    df_f = df_f.dropna(subset=["Fecha_aprobacion"]).sort_values("Fecha_aprobacion")
    if df_f.empty:
        return None
    df_f["Acumuladas"] = range(1, len(df_f) + 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f["Fecha_aprobacion"], y=df_f["Acumuladas"],
        mode="lines+markers",
        line=dict(color="#f1c40f", width=3),
        marker=dict(color="#ff4b4b", size=8),
        hovertemplate="%{x|%d/%m/%Y}<br>Materias aprobadas: %{y}<extra></extra>",
    ))
    fig.add_hline(y=TOTAL_MATERIAS, line_dash="dot", line_color="#2ecc71",
                  annotation_text="Meta total", annotation_font_color="#2ecc71")
    fig.update_layout(
        paper_bgcolor="#0b0d11", plot_bgcolor="#0b0d11",
        font=dict(color="#e0e0e0"),
        xaxis=dict(title="Fecha", gridcolor="#222", linecolor="#444"),
        yaxis=dict(title="Materias aprobadas", gridcolor="#222", linecolor="#444"),
        height=320,
        margin=dict(l=20, r=20, t=10, b=20),
    )
    return fig


# ─────────────────────────────────────────────
# 5. VISTAS
# ─────────────────────────────────────────────

def vista_inicio(conn, df, usuario, mis_datos, aprobadas_df, cursando_df,
                 puntos_logrados, promedio_simple, promedio_pond):

    col_av, col_cur = st.columns([1, 2])

    with col_av:
        img_path = get_avatar_path(usuario, len(aprobadas_df))
        if os.path.exists(img_path):
            st.image(img_path, width=150)
        else:
            st.markdown("🎮")

        st.metric("PUNTOS",   puntos_logrados)
        st.metric("PROMEDIO", f"{promedio_simple:.2f}")
        st.metric("POND.",    f"{promedio_pond:.2f}",
                  help="Promedio ponderado por créditos de cada materia")

        egreso = estimar_egreso(aprobadas_df)
        if egreso:
            st.markdown(
                f"<p style='font-size:11px; color:#aaa;'>🎓 Estimado egreso: "
                f"<strong style='color:#2ecc71'>{egreso}</strong></p>",
                unsafe_allow_html=True,
            )

        st.link_button("📂 DRIVE SQUAD",  "https://drive.google.com/drive/folders/1C7LQskupjeW2sO2wnD_upyYnuxip4oqs", use_container_width=True)
        st.link_button("🏛️ SIU GUARANÍ", "https://estudiantes.unla.edu.ar/autogestion3w/acceso",                     use_container_width=True)
        st.link_button("💻 CAMPUS UNLA", "https://campus.unla.edu.ar/aulas/login/index.php",                          use_container_width=True)

    with col_cur:
        st.markdown("#### 🏆 PROGRESO POR CRÉDITOS:")
        prog_tec = min(puntos_logrados / CREDITOS_TOTAL_TECNICATURA, 1.0)
        st.progress(prog_tec)
        st.markdown(
            f"<p class='hp-bar-text-blue'>TECNICATURA: {puntos_logrados}/{CREDITOS_TOTAL_TECNICATURA} pts ({int(prog_tec*100)}%)</p>",
            unsafe_allow_html=True,
        )
        prog_lic = min(puntos_logrados / CREDITOS_TOTAL_LICENCIATURA, 1.0)
        st.progress(prog_lic)
        st.markdown(
            f"<p class='hp-bar-text'>LICENCIATURA: {puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA} pts ({int(prog_lic*100)}%)</p>",
            unsafe_allow_html=True,
        )

        # Próximos exámenes en inicio (máx. 3)
        examenes = _get_examenes_proximos(mis_datos)
        if examenes:
            st.markdown("---")
            st.markdown("#### 📅 PRÓXIMOS EXÁMENES:")
            for ex in examenes[:3]:
                dias    = ex["dias"]
                urgente = dias is not None and dias <= 7
                badge   = f"⚠️ {dias}d" if urgente else (f"📅 {dias}d" if dias is not None else "")
                clase   = "exam-card exam-urgent" if urgente else "exam-card"
                st.markdown(
                    f"<div class='{clase}'><strong>{ex['materia']}</strong> {badge}<br>"
                    f"<span style='color:#aaa; font-size:12px;'>{ex['fecha_str']}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("#### ⚔️ MATERIAS EN CURSO:")

        if cursando_df.empty:
            st.info("No estás cursando ninguna materia. ¡Inscribite en PRÓX.!")
        else:
            for i, row in cursando_df.iterrows():
                materia  = row["Materia"]
                tipo_c   = row["Cursada"]
                key_flag = f"aprobar_{i}_{materia}"
                key_edit = f"editar_{i}_{materia}"

                c_btn_m, c_btn_edit, c_btn_del = st.columns([3, 1, 1])

                if c_btn_m.button(f"✅ {materia} [{tipo_c}]", key=f"mision_{i}"):
                    st.session_state[key_flag] = not st.session_state.get(key_flag, False)
                    st.session_state[key_edit] = False

                if c_btn_edit.button("✏️", key=f"edit_{i}", help="Editar parciales / fecha examen"):
                    st.session_state[key_edit] = not st.session_state.get(key_edit, False)
                    st.session_state[key_flag] = False

                if c_btn_del.button("❌", key=f"del_{i}"):
                    idx_drop = df[(df["Nombre"] == usuario) & (df["Materia"] == materia)].index
                    guardar_df(conn, df.drop(idx_drop).reset_index(drop=True))
                    st.rerun()

                # Formulario: registrar aprobación
                if st.session_state.get(key_flag, False):
                    with st.form(key=f"form_{i}"):
                        nota_input  = st.number_input("Nota final (4-10):", min_value=4, max_value=10, value=7)
                        fecha_ap    = st.date_input("Fecha de aprobación:", value=date.today())
                        if st.form_submit_button("🎖️ REGISTRAR VICTORIA"):
                            df.loc[
                                (df["Nombre"] == usuario) & (df["Materia"] == materia),
                                ["Estado", "Nota", "Fecha_aprobacion"]
                            ] = ["Aprobada", nota_input, str(fecha_ap)]
                            guardar_df(conn, df)
                            st.session_state[key_flag]        = False
                            st.session_state["show_confetti"] = True
                            st.rerun()

                # Formulario: editar parciales / fecha examen / tipo cursada
                if st.session_state.get(key_edit, False):
                    with st.form(key=f"editform_{i}"):
                        st.markdown(f"**Editar: {materia}**")
                        p1_act = pd.to_numeric(row.get("Nota_parcial1", ""), errors="coerce")
                        p2_act = pd.to_numeric(row.get("Nota_parcial2", ""), errors="coerce")
                        p1 = st.number_input("Nota parcial 1 (0 = sin nota):", 0, 10,
                                             int(p1_act) if pd.notna(p1_act) else 0)
                        p2 = st.number_input("Nota parcial 2 (0 = sin nota):", 0, 10,
                                             int(p2_act) if pd.notna(p2_act) else 0)
                        fecha_ex_act = str(row.get("Fecha_examen", "")).strip()
                        try:
                            fecha_ex_val = datetime.strptime(fecha_ex_act, "%Y-%m-%d").date()
                        except Exception:
                            fecha_ex_val = date.today()
                        fecha_ex   = st.date_input("Fecha de examen final:", value=fecha_ex_val)
                        nuevo_tipo = st.selectbox(
                            "Tipo de cursada:",
                            ["Regular", "Contracursada"],
                            index=["Regular", "Contracursada"].index(tipo_c)
                                  if tipo_c in ["Regular", "Contracursada"] else 0,
                        )
                        if st.form_submit_button("💾 GUARDAR"):
                            mask = (df["Nombre"] == usuario) & (df["Materia"] == materia)
                            df.loc[mask, "Nota_parcial1"] = p1 if p1 > 0 else ""
                            df.loc[mask, "Nota_parcial2"] = p2 if p2 > 0 else ""
                            df.loc[mask, "Fecha_examen"]  = str(fecha_ex)
                            df.loc[mask, "Cursada"]       = nuevo_tipo
                            guardar_df(conn, df)
                            st.session_state[key_edit] = False
                            st.rerun()

                # Mostrar parciales si los hay
                p1v = pd.to_numeric(row.get("Nota_parcial1", ""), errors="coerce")
                p2v = pd.to_numeric(row.get("Nota_parcial2", ""), errors="coerce")
                if pd.notna(p1v) or pd.notna(p2v):
                    p1_str = f"P1: {int(p1v)}" if pd.notna(p1v) else "P1: -"
                    p2_str = f"P2: {int(p2v)}" if pd.notna(p2v) else "P2: -"
                    st.caption(f"   {p1_str} | {p2_str}")


def vista_grupo(df):
    st.header("👥 DESPLIEGUE POR CUATRIMESTRE REAL")
    en_curso = df[df["Estado"] == "Cursando"].copy()

    if not en_curso.empty:
        en_curso["PeriodoReal"] = en_curso.apply(
            lambda r: asignar_periodo_real(r["Materia"], r["Cursada"]), axis=1
        )
        for periodo in ["1° Cuatrimestre", "2° Cuatrimestre"]:
            st.markdown(f"<div class='cuatri-header'>{periodo}</div>", unsafe_allow_html=True)
            bloque = en_curso[en_curso["PeriodoReal"] == periodo]
            if bloque.empty:
                st.info("Sin actividad en este periodo.")
                continue
            for mat in bloque["Materia"].unique():
                soldados_data = bloque[bloque["Materia"] == mat]
                lista_nombres = [f"{r['Nombre']} ({r['Cursada']})" for _, r in soldados_data.iterrows()]
                puntos_mat    = PLAN_ESTUDIOS.get(mat, {}).get("puntos", 0)
                st.markdown(
                    f"<div class='materia-card'><strong>{mat}</strong> ({puntos_mat} pts)<br>"
                    f"<span style='color:#aaa;'>🎖️ Soldados: {', '.join(lista_nombres)}</span></div>",
                    unsafe_allow_html=True,
                )
    else:
        st.warning("No hay soldados cursando actualmente.")

    st.markdown("---")
    st.markdown("#### 🏅 MATERIAS APROBADAS POR EL SQUAD")
    aprobadas_grupo = df[df["Estado"] == "Aprobada"][["Nombre", "Materia", "Nota"]].copy()
    if not aprobadas_grupo.empty:
        st.dataframe(aprobadas_grupo.sort_values(["Materia", "Nombre"]), use_container_width=True, hide_index=True)
    else:
        st.info("Nadie ha aprobado materias aún.")


def vista_proximas(conn, df, usuario, mis_datos, aprobadas_df):
    st.header("📝 PRÓXIMOS OBJETIVOS")
    ya_registradas = mis_datos["Materia"].tolist()
    aprobadas      = aprobadas_df["Materia"].tolist()

    disponibles = [m for m, info in PLAN_ESTUDIOS.items()
                   if m not in ya_registradas and all(c in aprobadas for c in info["correlativas"])]
    bloqueadas  = [m for m, info in PLAN_ESTUDIOS.items()
                   if m not in ya_registradas and not all(c in aprobadas for c in info["correlativas"])]

    if disponibles:
        st.markdown("##### 🔓 Disponibles para cursar:")
        for d in disponibles:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.success(f"**{d}** ({PLAN_ESTUDIOS[d]['puntos']} pts) — {PLAN_ESTUDIOS[d]['periodo']}")
            tipo_key = f"tipo_{d}"
            if tipo_key not in st.session_state:
                st.session_state[tipo_key] = "Regular"
            st.session_state[tipo_key] = c2.selectbox(
                "Modalidad:", ["Regular", "Contracursada"], key=f"sel_{d}",
                index=["Regular", "Contracursada"].index(st.session_state[tipo_key]),
            )
            if c3.button("⚔️ CURSAR", key=f"in_{d}"):
                nueva = pd.DataFrame([{
                    "Nombre": usuario, "Materia": d, "Estado": "Cursando",
                    "Cursada": st.session_state[tipo_key],
                    "Nota": "", "Nota_parcial1": "", "Nota_parcial2": "",
                    "Fecha_aprobacion": "", "Fecha_examen": "",
                }])
                guardar_df(conn, pd.concat([df, nueva], ignore_index=True))
                st.rerun()

    if bloqueadas:
        st.markdown("---")
        st.markdown("##### 🔒 Bloqueadas (faltan correlativas):")
        for b in bloqueadas:
            faltan = [c for c in PLAN_ESTUDIOS[b]["correlativas"] if c not in aprobadas]
            st.markdown(
                f"<div class='warning-card'><strong>{b}</strong> — falta: {', '.join(faltan)}</div>",
                unsafe_allow_html=True,
            )


def vista_historial(conn, df, usuario, mis_datos):
    st.header("✅ REGISTRO DE COMBATE")
    cols_mostrar = [c for c in ["Materia", "Estado", "Nota", "Nota_parcial1", "Nota_parcial2",
                                 "Cursada", "Fecha_aprobacion", "Fecha_examen"] if c in mis_datos.columns]
    st.dataframe(mis_datos[cols_mostrar].sort_values("Estado"), use_container_width=True, hide_index=True)

    # Editar materia aprobada
    aprobadas_list = mis_datos[mis_datos["Estado"] == "Aprobada"]["Materia"].tolist()
    if aprobadas_list:
        st.markdown("---")
        st.markdown("#### ✏️ CORREGIR MATERIA APROBADA")
        with st.form("editar_aprobada"):
            mat_sel     = st.selectbox("Materia:", aprobadas_list)
            nueva_nota  = st.number_input("Nueva nota (4-10):", min_value=4, max_value=10, value=7)
            nueva_fecha = st.date_input("Fecha de aprobación:", value=date.today())
            if st.form_submit_button("💾 ACTUALIZAR"):
                mask = (df["Nombre"] == usuario) & (df["Materia"] == mat_sel)
                df.loc[mask, "Nota"]             = nueva_nota
                df.loc[mask, "Fecha_aprobacion"] = str(nueva_fecha)
                guardar_df(conn, df)
                st.success(f"✅ {mat_sel} actualizada.")
                st.rerun()


def vista_estadisticas(df, usuario, mis_datos, aprobadas_df, cursando_df,
                        puntos_logrados, promedio_simple, promedio_pond):
    st.header("📊 ANÁLISIS DE CAMPAÑA")

    # Métricas resumen
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aprobadas",  len(aprobadas_df))
    c2.metric("Cursando",   len(cursando_df))
    c3.metric("Pendientes", TOTAL_MATERIAS - len(aprobadas_df) - len(cursando_df))
    c4.metric("Créditos",   f"{puntos_logrados}/{CREDITOS_TOTAL_LICENCIATURA}")

    egreso = estimar_egreso(aprobadas_df)
    if egreso:
        st.info(f"🎓 A tu ritmo actual, terminarías la carrera aproximadamente en **{egreso}**.")
    else:
        st.info("💡 Registrá fechas de aprobación en INICIO para estimar cuándo terminás la carrera.")

    st.markdown("---")

    # Progreso en el tiempo
    st.markdown("#### 📈 PROGRESO EN EL TIEMPO")
    fig_tiempo = grafico_progreso_tiempo(aprobadas_df)
    if fig_tiempo:
        st.plotly_chart(fig_tiempo, use_container_width=True)
    else:
        st.info("💡 Registrá fechas de aprobación para ver tu curva de progreso.")

    st.markdown("---")

    # Radar chart
    st.markdown("#### 🕸️ FORTALEZA POR ÁREA")
    col_r, col_r2 = st.columns([2, 1])
    with col_r:
        st.plotly_chart(grafico_radar(aprobadas_df), use_container_width=True)
    with col_r2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        for area, mats in AREAS.items():
            aprobadas_area = sum(1 for m in mats if m in aprobadas_df["Materia"].values)
            pct = int(aprobadas_area / len(mats) * 100) if mats else 0
            st.markdown(f"**{area}**: {aprobadas_area}/{len(mats)} ({pct}%)")

    st.markdown("---")

    # Árbol de correlativas
    st.markdown("#### 🌐 ÁRBOL DE CORRELATIVAS")
    st.markdown(
        "<div style='display:flex; gap:20px; flex-wrap:wrap; margin-bottom:10px; font-size:13px;'>"
        "<span>🟢 Aprobada</span><span>🟡 Cursando</span>"
        "<span>🔵 Disponible</span><span>⚫ Bloqueada</span></div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        grafico_arbol_correlativas(
            aprobadas_df["Materia"].tolist(),
            cursando_df["Materia"].tolist(),
        ),
        use_container_width=True,
    )

    st.markdown("---")

    # Calendario de exámenes
    st.markdown("#### 📅 CALENDARIO DE EXÁMENES")
    examenes = _get_examenes_proximos(mis_datos)
    if examenes:
        for ex in examenes:
            dias = ex["dias"]
            if dias is None:
                badge = "📅 fecha inválida"
            elif dias < 0:
                badge = f"⏰ hace {abs(dias)}d"
            elif dias == 0:
                badge = "🚨 HOY"
            elif dias <= 7:
                badge = f"⚠️ en {dias}d"
            else:
                badge = f"📅 en {dias}d"
            urgente = dias is not None and dias <= 7
            clase   = "exam-card exam-urgent" if urgente else "exam-card"
            st.markdown(
                f"<div class='{clase}'>"
                f"<strong>{ex['materia']}</strong> — {ex['fecha_str']} {badge}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No tenés exámenes cargados. Editá una materia en INICIO (✏️) para agregar fechas.")


# ─────────────────────────────────────────────
# 6. CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def cargar_datos(conn):
    try:
        df = conn.read(worksheet=0, ttl=60)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        df = asegurar_columnas(df)
        df = normalizar_estado(df)
        return df
    except Exception as e:
        st.error("❌ ERROR CRÍTICO DE CONEXIÓN")
        st.warning(
            "Google Sheets no responde. "
            "Verificá que el archivo esté compartido con el Service Account como 'Editor'.\n\n"
            f"Detalle: `{e}`"
        )
        return None


# ─────────────────────────────────────────────
# 7. MAIN
# ─────────────────────────────────────────────
def main():
    if "menu" not in st.session_state:
        st.session_state.menu = "Inicio"
    if "show_confetti" not in st.session_state:
        st.session_state.show_confetti = False

    conn = get_connection()
    df   = cargar_datos(conn)
    if df is None:
        st.stop()

    # Confetti al registrar victoria
    if st.session_state.show_confetti:
        st.components.v1.html(confetti_html(), height=0)
        st.session_state.show_confetti = False

    # Header
    st.markdown(
        "<h1 class='retro-font' style='text-align:center; font-size:24px;'>SQUAD COMMAND 2026</h1>",
        unsafe_allow_html=True,
    )

    usuarios = sorted(df["Nombre"].dropna().unique().tolist())
    usuario  = st.selectbox("👤 SOLDADO:", ["Seleccionar..."] + usuarios, label_visibility="collapsed")
    if usuario == "Seleccionar...":
        return

    # Navegación — 5 secciones
    nav_cols = st.columns(5)
    menus = [
        ("🏠 INICIO",  "Inicio"),
        ("📝 PRÓX.",   "Proximas"),
        ("✅ HIST.",   "Historial"),
        ("👥 GRUPO",  "Grupo"),
        ("📊 STATS",  "Stats"),
    ]
    for col, (label, key) in zip(nav_cols, menus):
        if col.button(label, use_container_width=True):
            st.session_state.menu = key
            st.rerun()

    st.markdown("---")

    # Datos del usuario
    mis_datos    = df[df["Nombre"] == usuario].copy()
    aprobadas_df = mis_datos[mis_datos["Estado"] == "Aprobada"]
    cursando_df  = mis_datos[mis_datos["Estado"] == "Cursando"]

    puntos_logrados = sum(PLAN_ESTUDIOS.get(m, {}).get("puntos", 0) for m in aprobadas_df["Materia"])
    promedio_simple = (pd.to_numeric(aprobadas_df["Nota"], errors="coerce").dropna().mean()
                       if not aprobadas_df.empty else 0.0)
    promedio_pond   = calcular_promedio_ponderado(aprobadas_df)

    # Despacho de vistas
    menu = st.session_state.menu

    if menu == "Inicio":
        vista_inicio(conn, df, usuario, mis_datos, aprobadas_df, cursando_df,
                     puntos_logrados, promedio_simple, promedio_pond)
    elif menu == "Grupo":
        vista_grupo(df)
    elif menu == "Proximas":
        vista_proximas(conn, df, usuario, mis_datos, aprobadas_df)
    elif menu == "Historial":
        vista_historial(conn, df, usuario, mis_datos)
    elif menu == "Stats":
        vista_estadisticas(df, usuario, mis_datos, aprobadas_df, cursando_df,
                           puntos_logrados, promedio_simple, promedio_pond)


if __name__ == "__main__":
    main()
