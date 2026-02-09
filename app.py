import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN Y ESTÉTICA 8-BIT ---
st.set_page_config(page_title="Círculo Rojo RPG", page_icon="⚔️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

    /* Contenedor del Personaje */
    .pixel-box {
        background: #1e1e26;
        border: 4px solid #ffffff;
        box-shadow: 6px 6px 0px #800000;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .pixel-img {
        width: 150px;
        image-rendering: pixelated;
        margin: 10px;
    }

    /* Estilo de Ítems Desbloqueados */
    .item-card {
        background: #2d2d3a;
        border: 2px solid #555;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        font-size: 0.9em;
    }

    /* Títulos estilo Retro */
    .retro-title {
        font-family: 'Press Start 2P', cursive;
        color: #ff4b4b;
        font-size: 18px;
        text-shadow: 2px 2px #000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DICCIONARIO DE LOS 42 DESBLOQUEOS ---
RECOMPENSAS = {
    1: "☕ Café Frío", 2: "📒 Cuaderno de Notas", 3: "🖊️ Resaltador Gastado", 
    4: "🍕 Sobra de Pizza", 5: "🎒 Mochila Pesada", 6: "🔋 Batería Portátil",
    7: "📑 Fotocopias PDF", 8: "👓 Anteojos de Descanso", 9: "🍎 Manzana de Recreo",
    10: "🎧 Playlist de Lo-Fi", 11: "💾 Pendrive Perdido", 12: "🥤 Energizante",
    13: "🚌 Abono de Colectivo", 14: "📅 Calendario Tachado", 15: "🛡️ Escudo de Correlativas",
    16: "💻 Laptop con Stickers", 17: "🐁 Mouse Inalámbrico", 18: "📚 Libro de 800 págs",
    19: "🥪 Sándwich de Comedor", 20: "🔥 Aura de Segundo Año", 21: "🏹 Flecha de Parciales",
    22: "🧮 Calculadora Científica", 23: "🖋️ Pluma de Oro", 24: "🕵️ Capa de Invisible",
    25: "👟 Zapatillas Cómodas", 26: "🕰️ Reloj de 25 Horas", 27: "🧠 Memoria Expandida",
    28: "🌩️ Rayo de Ideas", 29: "🗺️ Mapa de la UNLa", 30: "🪄 Varita de Aprobación",
    31: "💎 Gema del Conocimiento", 32: "🧪 Poción de Energía", 33: "📜 Pergamino de Leyes",
    34: "🔑 Llave del Éxito", 35: "🧥 Túnica de Magíster", 36: "🦾 Brazo de Hierro",
    37: "🐉 Montura de Dragón", 38: "⚔️ Espada Legendaria", 39: "🪐 Anillo del Saber",
    40: "🦅 Alas de Libertad", 41: "🌌 Capa Cósmica", 42: "👑 CORONA DEL GRADUADO"
}

# --- 3. LÓGICA DE AVATARES (DiceBear API) ---
def get_avatar_url(seed, level):
    if level < 10:
        style = "pixel-art"      # Estilo inicial simple
    elif level < 25:
        style = "miniavs"        # Estilo caricatura
    elif level < 42:
        style = "bottts-neutral" # Estilo robots avanzados
    else:
        style = "adventurer"     # Estilo épico final
    
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"

# --- 4. FUNCIÓN PRINCIPAL ---
def main():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=0, ttl=0)
    except:
        st.error("Error al conectar con el servidor de datos.")
        return

    with st.sidebar:
        st.markdown("<p class='retro-title'>RED CIRCLE RPG</p>", unsafe_allow_html=True)
        usuario = st.selectbox("👤 SELECT PLAYER", ["Seleccionar..."] + list(df["Nombre"].unique()), key="rpg_user")
        
        st.markdown("---")
        if "menu" not in st.session_state: st.session_state.menu = "Dashboard"
        if st.button("🏠 Status"): st.session_state.menu = "Dashboard"
        if st.button("🎒 Inventario"): st.session_state.menu = "Inventario"

    if usuario == "Seleccionar...":
        st.info("Elegí tu personaje para iniciar la partida.")
        return

    # Datos del Usuario
    aprobadas = len(df[(df["Nombre"] == usuario) & (df["Estado"] == "Aprobada")])
    
    if st.session_state.menu == "Dashboard":
        col_char, col_stats = st.columns([1, 1.5])
        
        with col_char:
            st.markdown("<div class='pixel-box'>", unsafe_allow_html=True)
            avatar_url = get_avatar_url(usuario, aprobadas)
            st.image(avatar_url, use_container_width=True)
            st.markdown(f"**LVL: {aprobadas}**")
            
            # Título honorífico según nivel
            if aprobadas < 14: rango = "Ingresante"
            elif aprobadas < 28: rango = "Sobreviviente"
            elif aprobadas < 42: rango = "Casi Licenciado"
            else: rango = "LEYENDA VIVIENTE"
            st.success(rango)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_stats:
            st.subheader("Estadísticas de Poder")
            st.write(f"Materias conquistadas: {aprobadas} / 42")
            st.progress(aprobadas / 42)
            
            # Próximo desbloqueo
            next_lvl = aprobadas + 1
            if next_lvl <= 42:
                st.warning(f"Siguiente ítem: **{RECOMPENSAS[next_lvl]}**")
                st.caption(f"Falta {1} materia para subir de nivel.")

    elif st.session_state.menu == "Inventario":
        st.subheader("Tu Mochila de Objetos")
        mis_items = [v for k, v in RECOMPENSAS.items() if aprobadas >= k]
        
        if not mis_items:
            st.info("Tu mochila está vacía. ¡Aprobá tu primera materia!")
        else:
            cols = st.columns(3)
            for i, item in enumerate(mis_items):
                with cols[i % 3]:
                    st.markdown(f"<div class='item-card'>{item}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

