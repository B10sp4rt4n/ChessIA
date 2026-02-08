# mcl_chess.py
# Structural Health Engine - Modo Ajedrez Estructural
# Laboratorio experimental
# NOTA: Este módulo es EXPERIMENTAL. Usa ajedrez como entorno controlado
# para explorar comportamiento estructural, no como engine de ajedrez real.

from typing import Tuple, List, Optional
import chess
import random
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RNG aislado para chess (no usar random.seed() global)
_chess_rng = random.Random(42)

# -----------------------------
# Validación
# -----------------------------
def validate_max_moves(max_moves: int) -> int:
    """Valida número máximo de movimientos."""
    if not isinstance(max_moves, int):
        raise TypeError(f"max_moves debe ser int, recibido {type(max_moves).__name__}")
    if not 1 <= max_moves <= 500:
        raise ValueError(f"max_moves fuera de rango [1, 500]: {max_moves}")
    return max_moves


# -----------------------------
# Parámetros estructurales
# -----------------------------
PIECE_CAPACITY = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 10,
}

# Factor de accesibilidad estructural (simplificado para demo)
ACCESS_WEIGHT = 0.5


# -----------------------------
# Métricas estructurales
# -----------------------------
def compute_holistic_metrics(board: chess.Board) -> Tuple[float, float]:
    """
    Calcula métricas estructurales holísticas del tablero.
    
    Args:
        board: Tablero de ajedrez en estado actual
        
    Returns:
        Tuple de (H, H_eff):
        - H: holgura total (capacidad base - presión)
        - H_eff: holgura efectiva (holgura ponderada por movilidad/accesibilidad)
        
    Raises:
        TypeError: Si board no es chess.Board
        ValueError: Si el tablero es inválido
    
    CONCEPTO EXPERIMENTAL:
    - Capacidad = valor estructural base de la pieza
    - Movilidad = número de movimientos legales (proxy de accesibilidad)
    - Slack = capacidad remanente
    - H_eff pondera slack por movilidad (más movilidad → más accesible)
    
    NOTA: Esta es una instanciación simple. El motor productivo usa
    criterios más complejos de interdependencia estructural.
    """
    try:
        if not isinstance(board, chess.Board):
            raise TypeError(f"board debe ser chess.Board, recibido {type(board).__name__}")
        
        logger.debug(f"Calculando métricas para board: {board.fen()[:20]}...")
        
        H = 0.0
        H_eff = 0.0
        piece_count = 0

        for square, piece in board.piece_map().items():
            if piece is None:
                continue
                
            capacity = PIECE_CAPACITY.get(piece.piece_type, 0)
            if capacity == 0:
                logger.warning(f"Pieza desconocida: {piece.piece_type}")
                continue
            
            # Movilidad = movimientos legales desde esta casilla
            # (proxy observable de accesibilidad estructural)
            mobility = len(list(board.attacks(square)))
            
            # Slack base: capacidad no comprometida
            # Simplificación: asumimos que cada pieza tiene su capacidad plena
            slack = capacity
            
            # H total: suma de todas las capacidades
            H += slack
            piece_count += 1
            
            # H_eff: ponderar por accesibilidad (movilidad)
            # Mayor movilidad → mayor accesibilidad → mayor H_eff
            if mobility > 0:
                accessibility = min(mobility / 8.0, 1.0)  # Normalizar (8 = alta movilidad típica)
                H_eff += slack * accessibility * ACCESS_WEIGHT
            # Si mobility == 0, esta pieza no contribuye a H_eff (inaccesible)
        
        logger.debug(f"Métricas calculadas: H={H:.2f}, H_eff={H_eff:.2f} ({piece_count} piezas)")
        return H, H_eff
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error validando inputs: {e}")
        raise
    except Exception as e:
        logger.error(f"Error calculando métricas: {e}", exc_info=True)
        raise RuntimeError(f"Fallo al calcular métricas: {e}") from e


# -----------------------------
# Simulación
# -----------------------------
def run_game(max_moves: int = 200, rng: Optional[random.Random] = None) -> List[Tuple[int, float, float]]:
    """
    Ejecuta una partida de ajedrez monitoreando métricas estructurales.
    
    Args:
        max_moves: Número máximo de movimientos (1-500)
        rng: Generador random aislado (opcional)
        
    Returns:
        Lista de tuplas (move_count, H, H_eff)
        
    Raises:
        TypeError: Si max_moves no es int
        ValueError: Si max_moves fuera de rango
    
    NOTA: Los movimientos son aleatorios simples, no hay IA.
    El propósito es observar evolución estructural, no jugar correctamente.
    """
    try:
        max_moves = validate_max_moves(max_moves)
        if rng is None:
            rng = _chess_rng
        
        logger.info(f"Iniciando simulación de partida (max_moves={max_moves})")
        board = chess.Board()
        history = []

        for move_count in range(max_moves):
            if board.is_game_over():
                logger.info(f"Juego terminado en turno {move_count}")
                break

            H, H_eff = compute_holistic_metrics(board)
            history.append((move_count, H, H_eff))

            # Detección de colapso estructural experimental
            if H_eff <= 0.1:  # Umbral bajo (permite observar degradación)
                logger.warning(f"Colapso estructural aproximado en turno {move_count}")
                break

            # Movimiento aleatorio (no determinista, no IA)
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                logger.info(f"Sin movimientos legales en turno {move_count}")
                break
            
            try:
                move = rng.choice(legal_moves)
                board.push(move)
            except Exception as e:
                logger.error(f"Error aplicando movimiento en turno {move_count}: {e}")
                break
        
        logger.info(f"Simulación completa: {len(history)} turnos")
        return history
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error validando parámetros: {e}")
        raise
    except Exception as e:
        logger.error(f"Error en simulación: {e}", exc_info=True)
        raise RuntimeError(f"Fallo en simulación: {e}") from e


# -----------------------------
# Ejecución directa
# -----------------------------
if __name__ == "__main__":
    try:
        print("SHE - Modo Ajedrez Estructural (Laboratorio Experimental)")
        print("=" * 60)
        data = run_game()
        print(f"\nTurnos simulados: {len(data)}")
        
        if not data:
            print("\n⚠️ No se generaron datos")
        else:
            print("\nPrimeros 10 turnos:")
            print("Turno | H      | H_eff")
            print("-" * 30)
            for t, h, he in data[:10]:
                print(f"{t:5d} | {h:6.2f} | {he:6.2f}")
            
            final_t, final_h, final_he = data[-1]
            print(f"\nEstado final (turno {final_t}):")
            print(f"  H     = {final_h:.2f}")
            print(f"  H_eff = {final_he:.2f}")
    except Exception as e:
        logger.critical(f"Error crítico en ejecución: {e}", exc_info=True)
        print(f"\n⚠️ ERROR: {e}")
        raise
