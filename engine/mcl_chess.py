# mcl_chess.py
# Structural Health Engine - Modo Ajedrez Estructural
# Laboratorio experimental
# NOTA: Este módulo es EXPERIMENTAL. Usa ajedrez como entorno controlado
# para explorar comportamiento estructural, no como engine de ajedrez real.

from typing import Tuple, List
import chess
import random

# Reproducibilidad inicial
random.seed(42)

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
    
    H: holgura total (capacidad base - presión)
    H_eff: holgura efectiva (holgura ponderada por movilidad/accesibilidad)
    
    CONCEPTO EXPERIMENTAL:
    - Capacidad = valor estructural base de la pieza
    - Movilidad = número de movimientos legales (proxy de accesibilidad)
    - Slack = capacidad remanente
    - H_eff pondera slack por movilidad (más movilidad → más accesible)
    
    NOTA: Esta es una instanciación simple. El motor productivo usa
    criterios más complejos de interdependencia estructural.
    """
    H = 0.0
    H_eff = 0.0

    for square, piece in board.piece_map().items():
        capacity = PIECE_CAPACITY[piece.piece_type]
        
        # Movilidad = movimientos legales desde esta casilla
        # (proxy observable de accesibilidad estructural)
        mobility = len(list(board.attacks(square)))
        
        # Slack base: capacidad no comprometida
        # Simplificación: asumimos que cada pieza tiene su capacidad plena
        slack = capacity
        
        # H total: suma de todas las capacidades
        H += slack
        
        # H_eff: ponderar por accesibilidad (movilidad)
        # Mayor movilidad → mayor accesibilidad → mayor H_eff
        if mobility > 0:
            accessibility = min(mobility / 8.0, 1.0)  # Normalizar (8 = alta movilidad típica)
            H_eff += slack * accessibility * ACCESS_WEIGHT
        # Si mobility == 0, esta pieza no contribuye a H_eff (inaccesible)

    return H, H_eff


# -----------------------------
# Simulación
# -----------------------------
def run_game(max_moves: int = 200) -> List[Tuple[int, float, float]]:
    """
    Ejecuta una partida de ajedrez monitoreando métricas estructurales.
    
    NOTA: Los movimientos son aleatorios simples, no hay IA.
    El propósito es observar evolución estructural, no jugar correctamente.
    """
    board = chess.Board()
    history = []

    for move_count in range(max_moves):
        if board.is_game_over():
            break

        H, H_eff = compute_holistic_metrics(board)
        history.append((move_count, H, H_eff))

        # Detección de colapso estructural experimental
        if H_eff <= 0.1:  # Umbral bajo (permite observar degradación)
            print(f"⚠ Colapso estructural aproximado en turno {move_count}")
            break

        # Movimiento aleatorio (no determinista, no IA)
        legal_moves = list(board.legal_moves)
        if legal_moves:
            board.push(random.choice(legal_moves))
        else:
            break

    return history


# -----------------------------
# Ejecución directa
# -----------------------------
if __name__ == "__main__":
    print("SHE - Modo Ajedrez Estructural (Laboratorio Experimental)")
    print("=" * 60)
    data = run_game()
    print(f"\nTurnos simulados: {len(data)}")
    print("\nPrimeros 10 turnos:")
    print("Turno | H      | H_eff")
    print("-" * 30)
    for t, h, he in data[:10]:
        print(f"{t:5d} | {h:6.2f} | {he:6.2f}")
    
    if data:
        final_t, final_h, final_he = data[-1]
        print(f"\nEstado final (turno {final_t}):")
        print(f"  H     = {final_h:.2f}")
        print(f"  H_eff = {final_he:.2f}")
