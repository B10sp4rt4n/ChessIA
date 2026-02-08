# chess_demo.py
# Structural Health Engine - Demo Ajedrez Estructural
# Visualización Streamlit para mcl_chess.py
# NOTA: Este es un DEMO EXPERIMENTAL para observar métricas estructurales en ajedrez.

from typing import List, Tuple, Optional
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import chess
import chess.svg
import random
import logging
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
        if not isinstance(board, chess.Board):
            raise TypeError(f"board debe ser chess.Board, recibido {type(board).__name__}")
        if not isinstance(size, int) or size < 100 or size > 1000:
            raise ValueError(f"size debe estar entre 100-1000: {size}")
        
        svg = chess.svg.board(
            board=board,
            size=size,
            coordinates=True,
            colors={
                "square light": "#f0d9b5",
                "square dark": "#b58863",
                "square light lastmove": "#cdd26a",
                "square dark lastmove": "#aaa23a"
            }
        )
        return svg
    except Exception as e:
        logger.error(f"Error renderizando tablero: {e}")
        raise RuntimeError(f"Fallo al renderizar tablero: {e}") from e


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

if max_turns <= 0:
    st.sidebar.error("El número de turnos debe ser mayor a 0")
    max_turns = 10

# Validar costo computacional
cost_validation = validate_computational_cost(max_moves=max_turns)
if cost_validation['warning']:
    if cost_validation['allowed']:
        st.sidebar.warning(cost_validation['warning'])
    else:
        st.sidebar.error(cost_validation['warning'])
        max_turns = 50  # Forzar valor seguro

if st.sidebar.button("🎲 Nueva partida"):
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

# Extraer datos para gráfico (optimizado)
turns, H_values, H_eff_values = [], [], []
for t, h, he, _, _ in game_history:
    turns.append(t)
    H_values.append(h)
    H_eff_values.append(he)

# Gráfico simple con Streamlit

df = pd.DataFrame({
    "Turno": turns,
    "H (Holgura total)": H_values,
    "H_eff (Holgura efectiva)": H_eff_values
})

st.line_chart(df.set_index("Turno"))

# -----------------------------
# Lista de movimientos
# -----------------------------
with st.expander("📋 Ver lista completa de movimientos"):
    moves_list = []
    move_number = 1
    white_move = None
    
    for idx, (t, _, _, _, move_san) in enumerate(game_history):
        if t == 0:
            continue  # Saltar posición inicial
        
        # Determinar si es movimiento de blancas o negras
        if (t - 1) % 2 == 0:  # Blancas
            white_move = move_san
        else:  # Negras
            moves_list.append(f"{move_number}. {white_move} {move_san}")
            move_number += 1
            white_move = None
    
    # Si quedó un movimiento de blancas sin pareja
    if white_move:
        moves_list.append(f"{move_number}. {white_move}")
    
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

