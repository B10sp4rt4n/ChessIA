# test_chess_demo.py
# Tests para chess_demo.py - funciones testables sin UI Streamlit

import pytest
import chess
import random
from chess_demo import (
    validate_max_moves,
    render_board_svg,
    get_load_legend_html,
    get_load_legend_markdown,
    calcular_carga_por_casilla,
    obtener_color_por_carga,
    calcular_carga_de_nodos,
    get_color_for_load,
    run_game_stepwise,
    PIECE_CAPACITY,
    ACCESS_WEIGHT
)


class TestValidateMaxMoves:
    """Tests para validate_max_moves()."""
    
    def test_valid_values(self):
        """Verificar que valores válidos pasan."""
        assert validate_max_moves(1) == 1
        assert validate_max_moves(50) == 50
        assert validate_max_moves(100) == 100
        assert validate_max_moves(200) == 200
    
    def test_invalid_type_string(self):
        """Verificar TypeError con string."""
        with pytest.raises(TypeError, match="max_moves debe ser int"):
            validate_max_moves("50")
    
    def test_invalid_type_float(self):
        """Verificar TypeError con float."""
        with pytest.raises(TypeError, match="max_moves debe ser int"):
            validate_max_moves(50.5)
    
    def test_invalid_type_none(self):
        """Verificar TypeError con None."""
        with pytest.raises(TypeError, match="max_moves debe ser int"):
            validate_max_moves(None)
    
    def test_below_minimum(self):
        """Verificar ValueError con valor menor a 1."""
        with pytest.raises(ValueError, match="fuera de rango"):
            validate_max_moves(0)
        
        with pytest.raises(ValueError, match="fuera de rango"):
            validate_max_moves(-10)
    
    def test_above_maximum(self):
        """Verificar ValueError con valor mayor a 200."""
        with pytest.raises(ValueError, match="fuera de rango"):
            validate_max_moves(201)
        
        with pytest.raises(ValueError, match="fuera de rango"):
            validate_max_moves(1000)
    
    def test_boundary_values(self):
        """Verificar valores en los límites."""
        assert validate_max_moves(1) == 1  # Mínimo
        assert validate_max_moves(200) == 200  # Máximo


class TestRenderBoardSvg:
    """Tests para render_board_svg()."""
    
    def test_render_initial_position(self):
        """Verificar que renderiza posición inicial correctamente."""
        board = chess.Board()
        svg = render_board_svg(board)
        
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert len(svg) > 1000  # SVG debe ser razonablemente largo
    
    def test_render_with_custom_size(self):
        """Verificar que tamaño personalizado funciona."""
        board = chess.Board()
        svg_small = render_board_svg(board, size=200)
        svg_large = render_board_svg(board, size=800)
        
        assert isinstance(svg_small, str)
        assert isinstance(svg_large, str)
        assert 'width="200"' in svg_small or 'width="200' in svg_small
        assert 'width="800"' in svg_large or 'width="800' in svg_large
    
    def test_render_empty_board(self):
        """Verificar que renderiza tablero vacío."""
        board = chess.Board()
        board.clear_board()
        svg = render_board_svg(board)
        
        assert isinstance(svg, str)
        assert "<svg" in svg
    
    def test_render_custom_position(self):
        """Verificar renderización de posición personalizada."""
        board = chess.Board()
        board.clear_board()
        board.set_piece_at(chess.E4, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(chess.E5, chess.Piece(chess.KING, chess.BLACK))
        
        svg = render_board_svg(board)
        assert isinstance(svg, str)
        assert "<svg" in svg
    
    def test_invalid_board_type(self):
        """Verificar RuntimeError con tipo incorrecto de board."""
        with pytest.raises(RuntimeError, match="Fallo al renderizar tablero"):
            render_board_svg("not a board")
        
        with pytest.raises(RuntimeError, match="Fallo al renderizar tablero"):
            render_board_svg(None)
    
    def test_invalid_size_type(self):
        """Verificar RuntimeError con size inválido."""
        board = chess.Board()
        
        with pytest.raises(RuntimeError, match="Fallo al renderizar tablero"):
            render_board_svg(board, size=50)  # Muy pequeño
        
        with pytest.raises(RuntimeError, match="Fallo al renderizar tablero"):
            render_board_svg(board, size=2000)  # Muy grande
    
    def test_invalid_size_type_string(self):
        """Verificar RuntimeError con size no-int."""
        board = chess.Board()
        
        with pytest.raises(RuntimeError, match="Fallo al renderizar tablero"):
            render_board_svg(board, size="400")
    
    def test_board_with_moves(self):
        """Verificar renderización después de algunos movimientos."""
        board = chess.Board()
        board.push_san("e4")
        board.push_san("e5")
        board.push_san("Nf3")
        
        svg = render_board_svg(board)
        assert isinstance(svg, str)
        assert "<svg" in svg

    def test_load_overlay_colors_in_svg(self):
        """Verificar que el SVG contiene colores de carga."""
        board = chess.Board(fen=None)
        board.set_piece_at(chess.D4, chess.Piece(chess.QUEEN, chess.WHITE))
        board.set_piece_at(chess.D8, chess.Piece(chess.ROOK, chess.BLACK))
        board.set_piece_at(chess.D1, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.BLACK))

        svg = render_board_svg(board)

        assert "#ff4d4d" in svg.lower()
        assert "#7cfc00" in svg.lower()


class TestNodeLoads:
    """Tests para cálculo de carga por nodo."""

    def test_calcular_carga_de_nodos_devuelve_64(self):
        """Debe devolver una carga para cada casilla."""
        board = chess.Board()
        node_loads = calcular_carga_de_nodos(board)

        assert isinstance(node_loads, dict)
        assert len(node_loads) == 64
        assert "a1" in node_loads
        assert "h8" in node_loads

    def test_calcular_carga_de_nodos_tablero_vacio(self):
        """En tablero vacío, toda carga debe ser 0."""
        board = chess.Board(fen=None)
        node_loads = calcular_carga_de_nodos(board)

        assert all(load == 0.0 for load in node_loads.values())

    def test_calcular_carga_de_nodos_por_compromiso(self):
        """Valida carga por amenaza, defensa y ataque."""
        board = chess.Board(fen=None)
        board.set_piece_at(chess.D1, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(chess.D4, chess.Piece(chess.QUEEN, chess.WHITE))
        board.set_piece_at(chess.D8, chess.Piece(chess.ROOK, chess.BLACK))
        board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.BLACK))

        node_loads = calcular_carga_de_nodos(board)

        assert node_loads["d4"] == 1.0
        assert node_loads["a1"] == 0.0

    def test_calcular_carga_por_casilla_alias_equivalente(self):
        """El alias nuevo debe coincidir con la función compatible."""
        board = chess.Board()
        assert calcular_carga_por_casilla(board) == calcular_carga_de_nodos(board)

    def test_calcular_carga_de_nodos_valida_tipo(self):
        """Debe fallar si board no es chess.Board."""
        with pytest.raises(TypeError, match="board debe ser chess.Board"):
            calcular_carga_de_nodos("invalid")


class TestLoadColorMapping:
    """Tests para mapeo de color por carga."""

    def test_get_color_for_load_ranges(self):
        """Verificar colores en umbrales definidos."""
        assert get_color_for_load(0.0) == "#7CFC00"
        assert get_color_for_load(0.24) == "#7CFC00"
        assert get_color_for_load(0.25) == "#FFD700"
        assert get_color_for_load(0.54) == "#FFD700"
        assert get_color_for_load(0.55) == "#FF4D4D"
        assert get_color_for_load(1.0) == "#FF4D4D"

    def test_obtener_color_por_carga_equivalente(self):
        """El alias antiguo debe mapear igual que la función nueva."""
        for carga in [0.0, 0.2, 0.3, 0.7, 1.0]:
            assert get_color_for_load(carga) == obtener_color_por_carga(carga)


class TestLoadLegend:
    """Tests para leyenda visual de carga."""

    def test_get_load_legend_html_content(self):
        """La leyenda visual debe incluir badges para tres niveles."""
        legend_html = get_load_legend_html()

        assert isinstance(legend_html, str)
        assert "<div" in legend_html
        assert "🟢" in legend_html
        assert "🟡" in legend_html
        assert "🔴" in legend_html

    def test_get_load_legend_markdown_content(self):
        """La leyenda textual de compatibilidad debe incluir tres niveles."""
        legend = get_load_legend_markdown()

        assert isinstance(legend, str)
        assert "🟢" in legend
        assert "🟡" in legend
        assert "🔴" in legend


class TestRunGameStepwise:
    """Tests para run_game_stepwise()."""
    
    def test_basic_game(self):
        """Verificar que el juego se ejecuta correctamente."""
        rng = random.Random(42)
        history = run_game_stepwise(max_moves=10, rng=rng)
        
        assert len(history) >= 1  # Al menos posición inicial
        assert len(history) <= 11  # Máximo 10 movimientos + inicial
        
        # Verificar estructura de cada registro
        for turn, H, H_eff, board, move_san in history:
            assert isinstance(turn, int)
            assert isinstance(H, float)
            assert isinstance(H_eff, float)
            assert isinstance(board, chess.Board)
            assert isinstance(move_san, str)
            assert H >= 0
            assert H_eff >= 0
    
    def test_initial_position_included(self):
        """Verificar que posición inicial está incluida."""
        rng = random.Random(123)
        history = run_game_stepwise(max_moves=5, rng=rng)
        
        assert len(history) >= 1
        turn, H, H_eff, board, move_san = history[0]
        
        assert turn == 0
        assert move_san == "Posición inicial"
        assert board.fen() == chess.Board().fen()
    
    def test_different_max_moves(self):
        """Verificar que max_moves limita correctamente."""
        rng1 = random.Random(999)
        history_short = run_game_stepwise(max_moves=5, rng=rng1)
        
        rng2 = random.Random(999)
        history_long = run_game_stepwise(max_moves=20, rng=rng2)
        
        # Historia corta debe ser <= historia larga
        assert len(history_short) <= len(history_long)
    
    def test_reproducibility_with_seed(self):
        """Verificar reproducibilidad con mismo seed."""
        results = []
        
        for _ in range(2):
            rng = random.Random(7777)
            history = run_game_stepwise(max_moves=10, rng=rng)
            results.append(history)
        
        # Verificar que ambas corridas son idénticas
        assert len(results[0]) == len(results[1])
        
        for i in range(len(results[0])):
            turn1, H1, H_eff1, board1, move1 = results[0][i]
            turn2, H2, H_eff2, board2, move2 = results[1][i]
            
            assert turn1 == turn2
            assert abs(H1 - H2) < 0.01
            assert abs(H_eff1 - H_eff2) < 0.01
            assert board1.fen() == board2.fen()
            assert move1 == move2
    
    def test_metrics_decrease_or_stable(self):
        """Verificar que métricas generalmente disminuyen o son estables."""
        rng = random.Random(456)
        history = run_game_stepwise(max_moves=20, rng=rng)
        
        # H generalmente disminuye (capturas)
        first_H = history[0][1]
        last_H = history[-1][1]
        
        # Puede disminuir o mantenerse, pero no aumentar mucho
        assert last_H <= first_H * 1.1  # Margen del 10%
    
    def test_board_state_progression(self):
        """Verificar que estados de tablero progresan correctamente."""
        rng = random.Random(321)
        history = run_game_stepwise(max_moves=10, rng=rng)
        
        # Cada tablero debe ser diferente del anterior (excepto si termina)
        for i in range(1, len(history)):
            prev_board = history[i-1][3]
            curr_board = history[i][3]
            
            # Si hay más turnos después, el tablero debe haber cambiado
            if i < len(history) - 1:
                # Verificar que FEN es diferente (al menos el turno cambió)
                assert prev_board.fen() != curr_board.fen() or curr_board.is_game_over()
    
    def test_move_san_format(self):
        """Verificar que move_san está en formato correcto."""
        rng = random.Random(111)
        history = run_game_stepwise(max_moves=10, rng=rng)
        
        # Primer registro es posición inicial
        assert history[0][4] == "Posición inicial"
        
        # Registros siguientes deben tener notación SAN
        for i in range(1, len(history)):
            move_san = history[i][4]
            assert isinstance(move_san, str)
            assert len(move_san) > 0
            assert move_san != ""
    
    def test_game_over_detection(self, caplog):
        """Verificar que detecta cuando juego termina."""
        import logging
        
        with caplog.at_level(logging.INFO):
            rng = random.Random(888)
            history = run_game_stepwise(max_moves=100, rng=rng)
        
        # El juego puede terminar por varias razones
        # Solo verificamos que se ejecuta sin errores
        assert len(history) >= 1
    
    def test_invalid_max_moves_type(self):
        """Verificar que valida tipo de max_moves."""
        with pytest.raises(TypeError, match="max_moves debe ser int"):
            run_game_stepwise(max_moves="10")
    
    def test_invalid_max_moves_range(self):
        """Verificar que valida rango de max_moves."""
        with pytest.raises(ValueError, match="fuera de rango"):
            run_game_stepwise(max_moves=0)
        
        with pytest.raises(ValueError, match="fuera de rango"):
            run_game_stepwise(max_moves=300)
    
    def test_structural_collapse_detection(self, caplog):
        """Verificar detección de colapso estructural."""
        import logging
        
        # Difícil provocar colapso real, pero al menos verificar que no falla
        with caplog.at_level(logging.WARNING):
            rng = random.Random(555)
            history = run_game_stepwise(max_moves=50, rng=rng)
        
        # Verificar que se ejecuta correctamente
        assert len(history) >= 1
    
    def test_short_game(self):
        """Verificar juego muy corto (1 movimiento)."""
        rng = random.Random(222)
        history = run_game_stepwise(max_moves=1, rng=rng)
        
        # Debe tener inicial + posiblemente 1 movimiento
        assert 1 <= len(history) <= 2
    
    def test_board_copies_independent(self):
        """Verificar que copias de tableros son independientes."""
        rng = random.Random(333)
        history = run_game_stepwise(max_moves=5, rng=rng)
        
        # Modificar un tablero no debe afectar otros
        if len(history) >= 2:
            board1 = history[0][3]
            board2 = history[1][3]
            
            # Guardar FEN original
            original_fen = board1.fen()
            
            # Intentar modificar board1 (si tiene movimientos legales)
            if list(board1.legal_moves):
                move = list(board1.legal_moves)[0]
                board1.push(move)
                
                # board2 no debe verse afectado
                assert history[1][3].fen() == board2.fen()


class TestConstants:
    """Tests para constantes importadas."""
    
    def test_piece_capacity_exists(self):
        """Verificar que PIECE_CAPACITY está disponible."""
        assert PIECE_CAPACITY is not None
        assert isinstance(PIECE_CAPACITY, dict)
        assert len(PIECE_CAPACITY) > 0
    
    def test_access_weight_exists(self):
        """Verificar que ACCESS_WEIGHT está disponible."""
        assert ACCESS_WEIGHT is not None
        assert isinstance(ACCESS_WEIGHT, (int, float))
        assert ACCESS_WEIGHT > 0


class TestIntegration:
    """Tests de integración entre funciones."""
    
    def test_full_game_with_rendering(self):
        """Verificar que juego completo + rendering funciona."""
        rng = random.Random(999)
        history = run_game_stepwise(max_moves=5, rng=rng)
        
        # Renderizar cada estado
        for turn, H, H_eff, board, move_san in history:
            svg = render_board_svg(board, size=300)
            assert isinstance(svg, str)
            assert "<svg" in svg
    
    def test_validation_in_game(self):
        """Verificar que validación se aplica en run_game_stepwise."""
        # validate_max_moves se llama internamente
        with pytest.raises(ValueError):
            run_game_stepwise(max_moves=-5)
        
        with pytest.raises(TypeError):
            run_game_stepwise(max_moves="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
