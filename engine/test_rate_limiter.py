# test_rate_limiter.py
# Tests para verificar rate limiting en demos

import pytest
import time
from rate_limiter import (
    timeout,
    TimeoutError,
    SimpleRateLimiter,
    validate_computational_cost,
    rate_limited
)


class TestTimeoutDecorator:
    """Tests para el decorator @timeout."""
    
    def test_fast_function_completes(self):
        """Verificar que funciones rápidas completan sin problema."""
        @timeout(2)
        def fast_func():
            time.sleep(0.1)
            return "completed"
        
        result = fast_func()
        assert result == "completed"
    
    def test_slow_function_times_out(self):
        """Verificar que funciones lentas lanzan TimeoutError."""
        @timeout(1)
        def slow_func():
            time.sleep(5)
            return "never reached"
        
        with pytest.raises(TimeoutError):
            slow_func()
    
    def test_timeout_with_parameters(self):
        """Verificar que decorator funciona con parámetros."""
        @timeout(2)
        def func_with_args(a, b, c=10):
            time.sleep(0.1)
            return a + b + c
        
        result = func_with_args(1, 2, c=3)
        assert result == 6


class TestSimpleRateLimiter:
    """Tests para SimpleRateLimiter."""
    
    def test_allows_up_to_max_calls(self):
        """Verificar que permite hasta max_calls llamadas."""
        limiter = SimpleRateLimiter(max_calls=3, time_window=10.0)
        
        assert limiter.is_allowed()  # 1
        assert limiter.is_allowed()  # 2
        assert limiter.is_allowed()  # 3
        assert not limiter.is_allowed()  # 4 - bloqueada
    
    def test_resets_after_time_window(self):
        """Verificar que se resetea después de la ventana de tiempo."""
        limiter = SimpleRateLimiter(max_calls=2, time_window=1.0)
        
        assert limiter.is_allowed()  # 1
        assert limiter.is_allowed()  # 2
        assert not limiter.is_allowed()  # 3 - bloqueada
        
        # Esperar a que expire la ventana
        time.sleep(1.1)
        
        assert limiter.is_allowed()  # 4 - permitida después de reset
    
    def test_time_until_next_allowed(self):
        """Verificar cálculo de tiempo hasta próxima llamada."""
        limiter = SimpleRateLimiter(max_calls=2, time_window=5.0)
        
        limiter.is_allowed()
        limiter.is_allowed()
        
        # Ya alcanzamos el límite
        wait_time = limiter.time_until_next_allowed()
        assert 0 < wait_time <= 5.0


class TestValidateComputationalCost:
    """Tests para validate_computational_cost."""
    
    def test_low_cost_allowed(self):
        """Verificar que operaciones de bajo costo se permiten."""
        result = validate_computational_cost(max_moves=50)
        
        assert result['allowed'] is True
        assert result['warning'] is None
        assert result['cost'] < 0.7
    
    def test_high_cost_warning(self):
        """Verificar advertencia para operaciones costosas."""
        result = validate_computational_cost(max_moves=400)
        
        assert result['allowed'] is True
        assert result['warning'] is not None
        assert "⚠️" in result['warning']
        assert result['cost'] > 0.7
    
    def test_over_limit_blocked(self):
        """Verificar que operaciones sobre el límite se bloquean."""
        result = validate_computational_cost(max_moves=600)
        
        assert result['allowed'] is False
        assert result['warning'] is not None
        assert "⛔" in result['warning']
        assert result['cost'] > 1.0
    
    def test_with_nodes(self):
        """Verificar validación con número de nodos."""
        result = validate_computational_cost(max_moves=100, max_nodes=500)
        
        assert result['allowed'] is True
        assert result['cost'] > 0
    
    def test_nodes_over_limit(self):
        """Verificar bloqueo cuando nodos exceden límite."""
        result = validate_computational_cost(max_moves=100, max_nodes=1500)
        
        assert result['allowed'] is False
        assert result['warning'] is not None


class TestRateLimitedDecorator:
    """Tests para el decorator @rate_limited."""
    
    def test_allows_within_limit(self):
        """Verificar que permite llamadas dentro del límite."""
        @rate_limited(max_calls=3, time_window=10.0)
        def limited_func(x):
            return x * 2
        
        assert limited_func(1) == 2
        assert limited_func(2) == 4
        assert limited_func(3) == 6
    
    def test_blocks_over_limit(self):
        """Verificar que bloquea llamadas sobre el límite."""
        @rate_limited(max_calls=2, time_window=10.0)
        def limited_func():
            return "ok"
        
        limited_func()  # 1
        limited_func()  # 2
        
        with pytest.raises(RuntimeError, match="Rate limit excedido"):
            limited_func()  # 3 - bloqueada


class TestIntegrationWithDemos:
    """Tests de integración con funciones de demos."""
    
    def test_chess_demo_with_timeout(self):
        """Verificar que chess_demo funciona con timeout."""
        from chess_demo import run_game_stepwise
        import random
        
        # Debe completar sin timeout
        rng = random.Random(42)
        history = run_game_stepwise(max_moves=5, rng=rng)
        
        assert len(history) >= 1
        assert len(history) <= 6
    
    def test_demo_build_graph_with_timeout(self):
        """Verificar que demo.py build_graph funciona con timeout."""
        from demo import build_graph
        import random
        
        # Debe completar sin timeout
        rng = random.Random(123)
        G, nodes = build_graph(n=5, rng=rng)
        
        assert G is not None
        assert len(nodes) == 5
    
    def test_computational_cost_validation_chess(self):
        """Verificar validación de costo para chess demo."""
        # Valores seguros
        result = validate_computational_cost(max_moves=50)
        assert result['allowed']
        
        # Valores altos pero permitidos
        result = validate_computational_cost(max_moves=150)
        assert result['allowed']
        
        # Valores excesivos
        result = validate_computational_cost(max_moves=600)
        assert not result['allowed']
    
    def test_computational_cost_validation_graph(self):
        """Verificar validación de costo para demo de grafos."""
        # Valores seguros
        result = validate_computational_cost(max_moves=100, max_nodes=10)
        assert result['allowed']
        
        # Nodos altos
        result = validate_computational_cost(max_moves=100, max_nodes=800)
        assert result['allowed']
        assert result['warning'] is not None
        
        # Nodos excesivos
        result = validate_computational_cost(max_moves=100, max_nodes=1500)
        assert not result['allowed']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
