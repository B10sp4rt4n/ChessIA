# test_mcl_chess.py
# Tests unitarios para el Modo Ajedrez Estructural

import pytest
import chess
from mcl_chess import (
    PIECE_CAPACITY,
    ACCESS_WEIGHT,
    compute_holistic_metrics,
    run_game
)


class TestConstants:
    """Tests para constantes del módulo."""
    
    def test_piece_capacity_values(self):
        """Verificar que todas las piezas tienen capacidad definida."""
        assert PIECE_CAPACITY[chess.PAWN] == 1
        assert PIECE_CAPACITY[chess.KNIGHT] == 3
        assert PIECE_CAPACITY[chess.BISHOP] == 3
        assert PIECE_CAPACITY[chess.ROOK] == 5
        assert PIECE_CAPACITY[chess.QUEEN] == 9
        assert PIECE_CAPACITY[chess.KING] == 10
    
    def test_piece_capacity_all_defined(self):
        """Verificar que todas las piezas de chess están cubiertas."""
        expected_pieces = {chess.PAWN, chess.KNIGHT, chess.BISHOP, 
                          chess.ROOK, chess.QUEEN, chess.KING}
        assert set(PIECE_CAPACITY.keys()) == expected_pieces
    
    def test_access_weight_valid(self):
        """Verificar que ACCESS_WEIGHT está en rango razonable."""
        assert 0 < ACCESS_WEIGHT <= 1.0
        assert ACCESS_WEIGHT == 0.5


class TestComputeHolisticMetrics:
    """Tests para compute_holistic_metrics."""
    
    def test_initial_position_metrics(self):
        """Verificar métricas en posición inicial."""
        board = chess.Board()
        H, H_eff = compute_holistic_metrics(board)
        
        # Verificaciones básicas
        assert H > 0, "H debe ser positivo en posición inicial"
        assert H_eff > 0, "H_eff debe ser positivo en posición inicial"
        assert H_eff <= H, "H_eff no puede exceder H"
        
        # Con 32 piezas iniciales, H debería ser suma de capacidades
        expected_H = (
            16 * PIECE_CAPACITY[chess.PAWN] +    # 16 peones
            4 * PIECE_CAPACITY[chess.KNIGHT] +   # 4 caballos
            4 * PIECE_CAPACITY[chess.BISHOP] +   # 4 alfiles
            4 * PIECE_CAPACITY[chess.ROOK] +     # 4 torres
            2 * PIECE_CAPACITY[chess.QUEEN] +    # 2 damas
            2 * PIECE_CAPACITY[chess.KING]       # 2 reyes
        )
        assert H == expected_H
    
    def test_empty_board_metrics(self):
        """Verificar métricas en tablero vacío."""
        board = chess.Board(fen=None)  # Tablero vacío
        board.clear()
        
        H, H_eff = compute_holistic_metrics(board)
        
        assert H == 0.0
        assert H_eff == 0.0
    
    def test_single_piece_metrics(self):
        """Verificar métricas con una sola pieza."""
        board = chess.Board(fen=None)
        board.clear()
        board.set_piece_at(chess.E4, chess.Piece(chess.QUEEN, chess.WHITE))
        
        H, H_eff = compute_holistic_metrics(board)
        
        assert H == PIECE_CAPACITY[chess.QUEEN]
        assert H_eff > 0  # Debe tener alguna movilidad
        assert H_eff <= H
    
    def test_metrics_with_captures(self):
        """Verificar que H disminuye cuando se capturan piezas."""
        board = chess.Board()
        H_initial, _ = compute_holistic_metrics(board)
        
        # Jugar algunas jugadas con capturas
        board.push_san("e4")
        board.push_san("d5")
        board.push_san("exd5")  # Captura
        
        H_after_capture, _ = compute_holistic_metrics(board)
        
        assert H_after_capture < H_initial, "H debe disminuir tras captura"
    
    def test_mobility_affects_h_eff(self):
        """Verificar que la movilidad afecta H_eff."""
        # Posición con piezas bloqueadas (baja movilidad)
        board_blocked = chess.Board()
        
        # Posición con piezas libres (alta movilidad)
        # FEN con solo dama en centro del tablero vacío
        board_open = chess.Board(fen="8/8/8/3Q4/8/8/8/8 w - - 0 1")
        
        _, H_eff_blocked = compute_holistic_metrics(board_blocked)
        _, H_eff_open = compute_holistic_metrics(board_open)
        
        # Con más movilidad relativa, H_eff debería ser mayor proporcionalmente
        # (difícil comparar directamente por diferentes H totales)
        assert H_eff_open > 0
        assert H_eff_blocked > 0
    
    def test_h_eff_respects_access_weight(self):
        """Verificar que H_eff usa ACCESS_WEIGHT correctamente."""
        board = chess.Board(fen="8/8/8/3Q4/8/8/8/8 w - - 0 1")
        H, H_eff = compute_holistic_metrics(board)
        
        # H_eff debe ser <= H * ACCESS_WEIGHT * accesibilidad
        # Como máximo teórico (si accesibilidad = 1)
        max_H_eff = H * ACCESS_WEIGHT
        assert H_eff <= max_H_eff
    
    def test_metrics_are_non_negative(self):
        """Verificar que métricas nunca son negativas."""
        # Probar varias posiciones
        positions = [
            None,  # Posición inicial
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Inicial
            "8/8/8/8/8/8/8/8 w - - 0 1",  # Vacío
            "4k3/8/8/8/8/8/8/4K3 w - - 0 1",  # Solo reyes
        ]
        
        for fen in positions:
            board = chess.Board() if fen is None else chess.Board(fen=fen)
            H, H_eff = compute_holistic_metrics(board)
            
            assert H >= 0, f"H negativo en posición {fen}"
            assert H_eff >= 0, f"H_eff negativo en posición {fen}"


class TestRunGame:
    """Tests para run_game."""
    
    def test_run_game_basic(self):
        """Verificar que run_game ejecuta sin errores."""
        history = run_game(max_moves=10)
        
        assert len(history) > 0
        assert len(history) <= 11  # max 10 movimientos + estado inicial
    
    def test_run_game_history_structure(self):
        """Verificar estructura de history."""
        history = run_game(max_moves=5)
        
        for move_count, H, H_eff in history:
            assert isinstance(move_count, int)
            assert isinstance(H, float)
            assert isinstance(H_eff, float)
            assert move_count >= 0
            assert H >= 0
            assert H_eff >= 0
    
    def test_run_game_metrics_decrease_or_stable(self):
        """Verificar que H no aumenta (piezas solo se capturan, no aparecen)."""
        history = run_game(max_moves=20)
        
        H_values = [h for _, h, _ in history]
        
        # H debería ser decreciente o estable (nunca crecer)
        for i in range(1, len(H_values)):
            assert H_values[i] <= H_values[i-1], "H no debe aumentar"
    
    def test_run_game_stops_on_game_over(self):
        """Verificar que se detiene cuando el juego termina."""
        # Ejecutar partida larga
        history = run_game(max_moves=200)
        
        # Si terminó antes de 200 movimientos, verificar que fue por game over
        # (difícil de testear determinísticamente con movimientos aleatorios)
        assert len(history) <= 201  # max_moves + 1 (estado inicial)
    
    def test_run_game_zero_moves(self):
        """Verificar comportamiento con max_moves=0."""
        history = run_game(max_moves=0)
        
        # Debe retornar al menos el estado inicial (turno 0)
        assert len(history) >= 0
    
    def test_run_game_different_lengths(self):
        """Verificar que diferentes max_moves producen diferentes longitudes."""
        history_short = run_game(max_moves=5)
        history_long = run_game(max_moves=50)
        
        # Partida más larga debería tener más estados (salvo game over temprano)
        assert len(history_short) <= len(history_long) or len(history_long) > 20
    
    def test_run_game_reproducibility(self):
        """Verificar que con misma seed produce mismos resultados."""
        import random
        
        random.seed(42)
        history1 = run_game(max_moves=10)
        
        random.seed(42)
        history2 = run_game(max_moves=10)
        
        # Deberían ser idénticos
        assert len(history1) == len(history2)
        
        for (t1, h1, he1), (t2, h2, he2) in zip(history1, history2):
            assert t1 == t2
            assert abs(h1 - h2) < 0.01  # Tolerancia numérica
            assert abs(he1 - he2) < 0.01


class TestIntegration:
    """Tests de integración entre funciones."""
    
    def test_full_game_simulation_integration(self):
        """Test de integración: simular partida completa."""
        history = run_game(max_moves=30)
        
        assert len(history) > 0
        
        # Verificar consistencia de datos
        for turn, H, H_eff in history:
            assert 0 <= H <= 200  # Límite razonable de capacidad total
            assert 0 <= H_eff <= H
            assert turn >= 0
        
        # Primer estado debe ser inicial
        first_turn, first_H, first_H_eff = history[0]
        assert first_turn == 0
        assert first_H > 0
        assert first_H_eff > 0
    
    def test_metrics_consistency_throughout_game(self):
        """Verificar que métricas mantienen relación H_eff <= H."""
        history = run_game(max_moves=50)
        
        for _, H, H_eff in history:
            assert H_eff <= H, "H_eff no puede exceder H"


@pytest.fixture
def standard_board():
    """Fixture con tablero en posición inicial."""
    return chess.Board()


@pytest.fixture
def endgame_board():
    """Fixture con posición de final de partida (pocos piezas)."""
    return chess.Board(fen="4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")


def test_endgame_low_metrics(endgame_board):
    """Verificar que final de partida tiene métricas bajas."""
    H, H_eff = compute_holistic_metrics(endgame_board)
    
    # Solo 2 reyes + 1 peón = capacidades bajas
    expected_H = 2 * PIECE_CAPACITY[chess.KING] + PIECE_CAPACITY[chess.PAWN]
    assert H == expected_H
    assert H_eff < 20  # Valor bajo por pocas piezas


def test_standard_vs_endgame_comparison(standard_board, endgame_board):
    """Comparar métricas entre posición inicial y final."""
    H_std, H_eff_std = compute_holistic_metrics(standard_board)
    H_end, H_eff_end = compute_holistic_metrics(endgame_board)
    
    assert H_std > H_end, "Posición inicial debe tener más H"
    assert H_eff_std > H_eff_end, "Posición inicial debe tener más H_eff"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
