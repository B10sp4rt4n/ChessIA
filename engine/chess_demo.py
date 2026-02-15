# chess_demo.py
# Structural Health Engine - Demo Ajedrez Estructural
# Visualización Streamlit para mcl_chess.py
# NOTA: Este es un DEMO EXPERIMENTAL para observar métricas estructurales en ajedrez.

from typing import Dict, List, Tuple, Optional
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import chess
import chess.svg
import random
import logging
import os
from mcl_chess import (
    PIECE_CAPACITY,
    ACCESS_WEIGHT,
    compute_holistic_metrics
)
from rate_limiter import (
    timeout,
    TimeoutError,
    validate_computational_cost
)
from explanations import obtener_explicacion_con_fuente

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RNG aislado para demo (no usar random.seed() global)
_demo_rng = random.Random(42)

st.set_page_config(page_title="SHE Demo - Modo Ajedrez", layout="wide")

st.title("Structural Health Engine · Demo Ajedrez Estructural")
st.caption("Demo experimental — Laboratorio de métricas estructurales en ajedrez")

st.warning(
    """
    ⚠️ **Laboratorio Experimental**: Este modo usa ajedrez como entorno controlado 
    para observar comportamiento estructural. Los movimientos son aleatorios simples, 
    no hay motor de ajedrez real.
    """
)


# -----------------------------
# Validación
# -----------------------------
def validate_max_moves(max_moves: int) -> int:
    """Valida número máximo de movimientos."""
    if not isinstance(max_moves, int):
        raise TypeError(f"max_moves debe ser int, recibido {type(max_moves).__name__}")
    if not 1 <= max_moves <= 200:
        raise ValueError(f"max_moves fuera de rango [1, 200]: {max_moves}")
    return max_moves


def get_cached_cost_validation(
    cache_key: str,
    *,
    max_moves: int,
    max_nodes: Optional[int] = None,
    warn_threshold: float = 0.7,
    force_refresh: bool = False
) -> dict:
    """Obtiene validación de costo con caché en session_state."""
    cache = st.session_state.get(cache_key)
    cache_params = (max_moves, max_nodes, warn_threshold)

    if (
        force_refresh
        or cache is None
        or cache.get("params") != cache_params
    ):
        result = validate_computational_cost(
            max_moves=max_moves,
            max_nodes=max_nodes,
            warn_threshold=warn_threshold
        )
        st.session_state[cache_key] = {
            "params": cache_params,
            "result": result
        }
        return result

    return cache["result"]


def build_game_view_cache(game_history: List[Tuple[int, float, float, chess.Board, str]]) -> dict:
    """Construye datos derivados para visualización (gráfico y lista de movimientos)."""
    turns = [t for t, _, _, _, _ in game_history]
    H_values = [h for _, h, _, _, _ in game_history]
    H_eff_values = [he for _, _, he, _, _ in game_history]

    chart_df = pd.DataFrame({
        "Turno": turns,
        "H (Holgura total)": H_values,
        "H_eff (Holgura efectiva)": H_eff_values
    })

    moves_list = []
    move_number = 1
    white_move = None

    for t, _, _, _, move_san in game_history:
        if t == 0:
            continue
        if (t - 1) % 2 == 0:
            white_move = move_san
        else:
            moves_list.append(f"{move_number}. {white_move} {move_san}")
            move_number += 1
            white_move = None

    if white_move:
        moves_list.append(f"{move_number}. {white_move}")

    return {
        "game_ref": game_history,
        "chart_df": chart_df,
        "moves_list": moves_list
    }


# -----------------------------
# Funciones auxiliares
# -----------------------------
def render_board_svg(board: chess.Board, size: int = 400) -> str:
    """
    Renderiza el tablero en formato SVG gráfico usando python-chess.
    
    Args:
        board: Tablero de ajedrez
        size: Tamaño del tablero en pixels
        
    Returns:
        String SVG del tablero
        
    Raises:
        TypeError: Si board no es chess.Board
        ValueError: Si size es inválido
    """
    try:
        return renderizar_tablero_con_carga(board, size=size)
    except Exception as e:
        logger.error(f"Error renderizando tablero: {e}")
        raise RuntimeError(f"Fallo al renderizar tablero: {e}") from e


def obtener_color_por_carga(carga: float) -> str:
    """Asigna color de casilla basado en carga estructural."""
    if carga < 0.25:
        return "#7CFC00"  # Verde brillante (baja carga)
    if carga < 0.55:
        return "#FFD700"  # Amarillo (moderada carga)
    return "#FF4D4D"  # Rojo (alta carga)


def calcular_carga_por_casilla(board: chess.Board) -> Dict[str, float]:
    """Calcula carga estructural por casilla en rango [0, 1]."""
    if not isinstance(board, chess.Board):
        raise TypeError(f"board debe ser chess.Board, recibido {type(board).__name__}")

    node_loads: Dict[str, float] = {}

    for square in chess.SQUARES:
        square_name = chess.square_name(square)
        piece = board.piece_at(square)

        if piece is None:
            node_loads[square_name] = 0.0
            continue

        load = 0.0

        if board.is_attacked_by(not piece.color, square):
            load += 0.35

        if board.is_attacked_by(piece.color, square):
            load += 0.25

        attacking_enemy = False
        for target_square in board.attacks(square):
            target_piece = board.piece_at(target_square)
            if target_piece and target_piece.color != piece.color:
                attacking_enemy = True
                break
        if attacking_enemy:
            load += 0.25

        if piece.piece_type in (chess.KING, chess.QUEEN):
            load += 0.15

        node_loads[square_name] = min(1.0, load)

    return node_loads


def renderizar_tablero_con_carga(board: chess.Board, size: int = 400) -> str:
    """Renderiza tablero con colores por carga estructural de casillas."""
    if not isinstance(board, chess.Board):
        raise TypeError(f"board debe ser chess.Board, recibido {type(board).__name__}")
    if not isinstance(size, int) or size < 100 or size > 1000:
        raise ValueError(f"size debe estar entre 100-1000: {size}")

    node_loads = calcular_carga_por_casilla(board)
    fill_colors = {
        chess.parse_square(square_name): obtener_color_por_carga(carga)
        for square_name, carga in node_loads.items()
    }

    return chess.svg.board(
        board=board,
        size=size,
        coordinates=True,
        colors={
            "square light": "#f0d9b5",
            "square dark": "#b58863",
            "square light lastmove": "#cdd26a",
            "square dark lastmove": "#aaa23a"
        },
        fill=fill_colors
    )


def get_load_legend_html() -> str:
    """Leyenda visual tipo badge para carga estructural."""
    return """
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">
      <span style="background:#7CFC00;color:#111;padding:4px 10px;border-radius:999px;font-weight:600;">🟢 Baja (&lt;0.25)</span>
      <span style="background:#FFD700;color:#111;padding:4px 10px;border-radius:999px;font-weight:600;">🟡 Moderada (0.25–0.54)</span>
      <span style="background:#FF4D4D;color:#fff;padding:4px 10px;border-radius:999px;font-weight:600;">🔴 Alta (≥0.55)</span>
    </div>
    """


def get_load_legend_markdown() -> str:
    """Compatibilidad retroactiva: leyenda textual de carga estructural."""
    return "🟢 Baja (<0.25) · 🟡 Moderada (0.25–0.54) · 🔴 Alta (≥0.55)"


def get_color_for_load(load: float) -> str:
    """Compatibilidad retroactiva: alias de obtener_color_por_carga()."""
    return obtener_color_por_carga(load)


def generar_narrativa_posicion(
    board: chess.Board,
    H: float,
    H_eff: float,
    turn: int,
    oyente_type: str = "técnico"
) -> Tuple[str, str]:
    """
    Genera narrativa del estado estructural de la posición de ajedrez.
    
    Returns:
        Tuple[str, str]: (explicacion, fuente)
    """
    # Clasificar estado según H_eff
    if H_eff > 50:
        classification = "Alpha"
    elif H_eff > 20:
        classification = "Beta"
    else:
        classification = "Gamma"
    
    # Calcular decay simulado (asumiendo degradación lineal)
    decay_rate = (100 - H_eff) / max(turn, 1)
    
    # Contar piezas
    white_pieces = len([p for p in board.piece_map().values() if p.color == chess.WHITE])
    black_pieces = len([p for p in board.piece_map().values() if p.color == chess.BLACK])
    total_pieces = white_pieces + black_pieces
    
    # Crear escenario para explicación
    scenario = {
        "name": f"Turno {turn} ({total_pieces} piezas)",
        "H_eff": H_eff,
        "decay": decay_rate
    }
    
    try:
        explicacion, fuente = obtener_explicacion_con_fuente(
            scenario=scenario,
            classification=classification,
            oyente_type=oyente_type
        )
        return explicacion, fuente
    except Exception as e:
        logger.warning(f"Error generando narrativa: {e}")
        # Fallback básico
        return (
            f"📊 Turno {turn}\n"
            f"Holgura efectiva: {H_eff:.1f}\n"
            f"Estado: {classification}\n"
            f"El sistema tiene {total_pieces} piezas activas ({white_pieces} blancas, {black_pieces} negras)."
        ), "LOCAL_FALLBACK"


def calcular_carga_de_nodos(board: chess.Board) -> Dict[str, float]:
    """Compatibilidad retroactiva: alias de calcular_carga_por_casilla()."""
    return calcular_carga_por_casilla(board)


@timeout(seconds=60)
def run_game_stepwise(max_moves: int = 50, rng: Optional[random.Random] = None) -> List[Tuple[int, float, float, chess.Board, str]]:
    """
    Ejecuta una partida paso a paso, guardando estado del tablero y movimientos.
    
    Args:
        max_moves: Número máximo de movimientos (1-200)
        rng: Generador random aislado (opcional)
        
    Returns:
        Lista de tuplas (move_count, H, H_eff, board, move_san)
        
    Raises:
        TypeError: Si max_moves no es int
        ValueError: Si max_moves fuera de rango
        TimeoutError: Si la ejecución excede 60 segundos
    
    Movimientos aleatorios simples.
    """
    try:
        max_moves = validate_max_moves(max_moves)
        if rng is None:
            rng = _demo_rng
        
        logger.info(f"Iniciando partida (max_moves={max_moves})")
        board = chess.Board()
        history = []
        
        # Estado inicial (sin movimiento)
        H, H_eff = compute_holistic_metrics(board)
        history.append((0, H, H_eff, board.copy(), "Posición inicial"))
        
        for move_count in range(max_moves):
            if board.is_game_over():
                logger.info(f"Juego terminado en turno {move_count}")
                break
            
            # Movimiento aleatorio
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                logger.warning(f"Sin movimientos legales en turno {move_count}")
                break
            
            try:
                move = rng.choice(legal_moves)
                move_san = board.san(move)  # Notación algebraica estándar (e.g., "Nf3", "e4")
                board.push(move)
            except Exception as e:
                logger.error(f"Error aplicando movimiento en turno {move_count}: {e}")
                break
            
            # Calcular métricas después del movimiento
            try:
                H, H_eff = compute_holistic_metrics(board)
            except Exception as e:
                logger.error(f"Error calculando métricas en turno {move_count}: {e}")
                break
            
            # Guardar estado
            history.append((move_count + 1, H, H_eff, board.copy(), move_san))
            
            # Detección de colapso estructural
            if H_eff <= 0.1:
                logger.warning(f"Colapso estructural en turno {move_count + 1}")
                break
        
        logger.info(f"Partida completa: {len(history)} estados")
        return history
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error validando parámetros: {e}")
        raise
    except Exception as e:
        logger.error(f"Error en simulación: {e}", exc_info=True)
        raise RuntimeError(f"Fallo en simulación: {e}") from e


# -----------------------------
# UI Sidebar
# -----------------------------
st.sidebar.header("Parámetros")
max_turns = st.sidebar.slider("Máximo de turnos", 10, 100, 50, step=10)
new_game_clicked = st.sidebar.button("🎲 Nueva partida")
show_load_legend = st.sidebar.checkbox("Mostrar leyenda de carga", value=True)

if max_turns <= 0:
    st.sidebar.error("El número de turnos debe ser mayor a 0")
    max_turns = 10

# Validar costo computacional
cost_validation = get_cached_cost_validation(
    "chess_demo_cost_validation",
    max_moves=max_turns,
    force_refresh=new_game_clicked
)
if cost_validation['warning']:
    if cost_validation['allowed']:
        st.sidebar.warning(cost_validation['warning'])
    else:
        st.sidebar.error(cost_validation['warning'])
        max_turns = 50  # Forzar valor seguro

if new_game_clicked:
    try:
        # Crear nuevo RNG para cada partida manual
        new_rng = random.Random()
        st.session_state["game"] = run_game_stepwise(max_turns, rng=new_rng)
        st.session_state["current_turn"] = 0
        st.success(f"Nueva partida generada ({max_turns} turnos máx)")
    except TimeoutError:
        st.error("⏱️ Timeout: La generación de partida tomó demasiado tiempo (>60s). Reduce el número de turnos.")
        logger.error(f"Timeout en nueva partida con max_turns={max_turns}")
    except Exception as e:
        st.error(f"Error generando partida: {e}")
        logger.error(f"Error en nueva partida: {e}", exc_info=True)

if "game" not in st.session_state:
    st.session_state["game"] = run_game_stepwise(max_turns)
    st.session_state["current_turn"] = 0

game_history = st.session_state["game"]
view_cache = st.session_state.get("chess_demo_view_cache")
if view_cache is None or view_cache.get("game_ref") is not game_history:
    view_cache = build_game_view_cache(game_history)
    st.session_state["chess_demo_view_cache"] = view_cache

# -----------------------------
# Control de turnos
# -----------------------------
st.sidebar.subheader("Control de reproducción")

col_prev, col_next = st.sidebar.columns(2)

with col_prev:
    if st.button("⏮ Anterior"):
        if st.session_state["current_turn"] > 0:
            st.session_state["current_turn"] -= 1

with col_next:
    if st.button("Siguiente ⏭"):
        if st.session_state["current_turn"] < len(game_history) - 1:
            st.session_state["current_turn"] += 1

current_idx = st.session_state["current_turn"]
turn, H, H_eff, board, move_san = game_history[current_idx]

st.sidebar.metric("Turno actual", f"{turn} / {len(game_history) - 1}")

# Mostrar último movimiento
if turn > 0:
    st.sidebar.info(f"**Movimiento:** {move_san}")
else:
    st.sidebar.info("**Movimiento:** —")

# -----------------------------
# Métricas actuales
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Holgura total (H)", f"{H:.1f}")
col2.metric("Holgura efectiva (H_eff)", f"{H_eff:.1f}")

state = "VIVO" if H_eff > 0.1 else ("ZOMBI" if H > 0 else "COLAPSADO")
col3.metric("Estado estructural", state)

# -----------------------------
# Narrativa Inteligente de la Posición
# -----------------------------
st.divider()
with st.expander("🤖 Análisis Narrativo de la Posición", expanded=False):
    st.caption("Explicación automatizada del estado estructural actual")
    
    col_narrativa1, col_narrativa2 = st.columns([2, 1])
    
    with col_narrativa1:
        oyente_chess = st.radio(
            "Tipo de audiencia:",
            ["técnico", "no técnico", "gerencial", "usuario final"],
            horizontal=True,
            key="chess_oyente"
        )
    
    with col_narrativa2:
        # Mostrar fuente de explicación
        if st.session_state.get("openai_api_key") and st.session_state.openai_api_key != "sk-your-key-here":
            st.info("🤖 Fuente: **IA**")
        else:
            st.warning("🔄 Fuente: **Local**")
    
    # Generar key única para forzar regeneración cuando cambian las métricas
    h_key = int(H * 10)
    h_eff_key = int(H_eff * 10)
    narrative_key = f"chess_narrative_{turn}_{h_key}_{h_eff_key}_{oyente_chess.replace(' ', '_')}"
    
    try:
        with st.spinner("Generando análisis..."):
            narrativa, fuente = generar_narrativa_posicion(
                board=board,
                H=H,
                H_eff=H_eff,
                turn=turn,
                oyente_type=oyente_chess
            )
        
        # Badge de fuente
        if fuente == "IA":
            st.markdown("**📡 Análisis generado por IA (OpenAI GPT-4)**")
        else:
            st.markdown("**⚙️ Análisis generado por motor de reglas local**")
        
        # Mostrar narrativa
        st.text_area(
            "Análisis estructural de la posición:",
            value=narrativa,
            height=300,
            key=narrative_key,
            disabled=True
        )
    except Exception as e:
        st.error(f"❌ Error generando análisis: {e}")
        logger.error(f"Error en narrativa chess: {e}", exc_info=True)

st.divider()

# -----------------------------
# Tablero
# -----------------------------
col_title, col_move = st.columns([2, 1])
with col_title:
    st.subheader(f"Tablero — Turno {turn}")
with col_move:
    if turn > 0:
        # Determinar turno de blancas o negras
        color_emoji = "⚪" if (turn - 1) % 2 == 0 else "⚫"
        st.metric("Último movimiento", f"{color_emoji} {move_san}")

# Generar SVG del tablero
board_svg = render_board_svg(board, size=450)

# Renderizar SVG en Streamlit
components.html(
    f"""
    <div style="display: flex; justify-content: center; margin: 20px 0;">
        {board_svg}
    </div>
    """,
    height=500
)
if show_load_legend:
    st.markdown(get_load_legend_html(), unsafe_allow_html=True)

# Info del turno y estado del juego
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric("Piezas blancas", len([p for p in board.piece_map().values() if p.color == chess.WHITE]))
with col_info2:
    st.metric("Piezas negras", len([p for p in board.piece_map().values() if p.color == chess.BLACK]))
with col_info3:
    if turn == len(game_history) - 1 and board.is_game_over():
        if board.is_checkmate():
            winner = "⚫ Negras" if board.turn == chess.WHITE else "⚪ Blancas"
            st.success(f"Jaque mate: {winner}")
        elif board.is_stalemate():
            st.info("Tablas: Ahogado")
        elif board.is_insufficient_material():
            st.info("Tablas: Material insuficiente")
        else:
            st.info("Partida terminada")
    elif H_eff <= 0.1:
        st.warning("⚠ Colapso estructural")

# -----------------------------
# Evolución de métricas
# -----------------------------
st.subheader("Evolución estructural")
st.line_chart(view_cache["chart_df"].set_index("Turno"))

# -----------------------------
# Lista de movimientos
# -----------------------------
with st.expander("📋 Ver lista completa de movimientos"):
    moves_list = view_cache["moves_list"]
    
    # Mostrar en columnas para mejor legibilidad
    cols_per_row = 3
    for i in range(0, len(moves_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(moves_list):
                move_idx = i + j
                # Cada par tiene 2 turnos: blancas (turn_white) y negras (turn_black)
                turn_white = move_idx * 2 + 1
                turn_black = move_idx * 2 + 2
                # Resaltar si estamos en alguno de esos turnos
                if turn_white <= turn <= turn_black:
                    col.markdown(f"**➤ {moves_list[i + j]}**")
                else:
                    col.write(moves_list[i + j])

# -----------------------------
# Interpretación
# -----------------------------
with st.expander("📖 Interpretación de métricas"):
    st.markdown("""
    ### Métricas estructurales en ajedrez
    
    - **H (Holgura total)**: Capacidad estructural base de todas las piezas en el tablero.
      Disminuye cuando se capturan piezas.
    
    - **H_eff (Holgura efectiva)**: Holgura ponderada por la movilidad de cada pieza.
      Una pieza con más movimientos legales tiene mayor accesibilidad estructural.
    
    - **Estado**:
      - **VIVO**: H_eff > 0.1 — El sistema puede redistribuir presión
      - **ZOMBI**: H > 0 pero H_eff ≈ 0 — Hay capacidad pero inaccesible
      - **COLAPSADO**: No existe redistribución viable
    
    ### Limitaciones del demo
    
    - Los movimientos son aleatorios (no hay estrategia ni IA)
    - El propósito es observar métricas estructurales, no jugar correctamente
    - Este es un laboratorio conceptual, no un motor de ajedrez
    """)

# -----------------------------
# Detalles técnicos
# -----------------------------
with st.expander("⚙️ Detalles técnicos"):
    st.markdown(f"""
    ### Configuración estructural
    
    **Capacidad base por pieza:**
    - Peón: {PIECE_CAPACITY[chess.PAWN]}
    - Caballo: {PIECE_CAPACITY[chess.KNIGHT]}
    - Alfil: {PIECE_CAPACITY[chess.BISHOP]}
    - Torre: {PIECE_CAPACITY[chess.ROOK]}
    - Dama: {PIECE_CAPACITY[chess.QUEEN]}
    - Rey: {PIECE_CAPACITY[chess.KING]}
    
    **Factor de accesibilidad**: {ACCESS_WEIGHT}
    
    H_eff = Σ (slack × accesibilidad × factor)
    
    donde accesibilidad = min(movilidad / 8.0, 1.0)
    """)

st.sidebar.markdown("---")
st.sidebar.caption("Modo Ajedrez Estructural v1.0")

