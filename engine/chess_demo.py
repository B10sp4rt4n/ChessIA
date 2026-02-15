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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RNG aislado para demo (no usar random.seed() global)
_demo_rng = random.Random(42)


# Nota: El código de UI standalone ha sido removido.
# Para ejecutar el demo de ajedrez, usa: streamlit run engine/app.py
# y selecciona "🎮 Chess Demo" en el sidebar.


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


# ============================================================================
# NOTA: Este archivo define funciones para ser usadas por app.py
# Para la UI completa de Chess Demo, ejecutar: streamlit run engine/app.py
# ============================================================================

