# rate_limiter.py
# Utilidades de rate limiting y timeout para demos Streamlit
# Previene abuso de recursos computacionales en producción

import time
import signal
import functools
import logging
import threading
from typing import Callable, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# -----------------------------
# Timeout Decorator
# -----------------------------
class TimeoutError(Exception):
    """Excepción lanzada cuando una función excede el timeout."""
    pass


def timeout_handler(signum, frame):
    """Handler para señal de timeout."""
    raise TimeoutError("Operación excedió el tiempo límite")


def timeout(seconds: int = 30):
    """
    Decorator que limita el tiempo de ejecución de una función.
    
    NOTA: Solo funciona en el main thread. Si se usa en un thread secundario
    (como en Streamlit), ejecuta la función sin timeout.
    
    Args:
        seconds: Tiempo máximo en segundos (default: 30)
        
    Raises:
        TimeoutError: Si la función no termina a tiempo (solo main thread)
        
    Ejemplo:
        @timeout(10)
        def slow_function():
            time.sleep(20)  # Lanzará TimeoutError en main thread
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Verificar si estamos en el main thread
            is_main_thread = threading.current_thread() is threading.main_thread()
            
            if not is_main_thread:
                # En threads secundarios (Streamlit), ejecutar sin timeout
                logger.debug(f"{func.__name__}: Ejecutando en thread secundario, timeout desactivado")
                return func(*args, **kwargs)
            
            # En main thread, usar signal
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restaurar handler y cancelar alarma
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        return wrapper
    return decorator


# -----------------------------
# Rate Limiter Simple
# -----------------------------
class SimpleRateLimiter:
    """
    Rate limiter basado en ventana deslizante.
    Previene ejecutar una función más de N veces en T segundos.
    """
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Args:
            max_calls: Número máximo de llamadas permitidas
            time_window: Ventana de tiempo en segundos
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """
        Verifica si una nueva llamada está permitida.
        
        Returns:
            True si está permitida, False si excede el límite
        """
        now = time.time()
        
        # Remover llamadas fuera de la ventana
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        # Verificar si podemos hacer otra llamada
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def time_until_next_allowed(self) -> float:
        """
        Calcula tiempo en segundos hasta que se permita la siguiente llamada.
        
        Returns:
            Segundos hasta próxima llamada permitida (0 si ya está permitida)
        """
        if len(self.calls) < self.max_calls:
            return 0.0
        
        now = time.time()
        oldest_call = min(self.calls)
        time_until_expires = self.time_window - (now - oldest_call)
        
        return max(time_until_expires, 0.0)


# -----------------------------
# Context Manager de Timeout
# -----------------------------
@contextmanager
def time_limit(seconds: int):
    """
    Context manager para limitar tiempo de ejecución.
    
    Args:
        seconds: Tiempo máximo en segundos
        
    Raises:
        TimeoutError: Si el bloque excede el tiempo
        
    Ejemplo:
        with time_limit(5):
            slow_operation()  # Se interrumpe si tarda >5s
    """
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# -----------------------------
# Validación de Recursos
# -----------------------------
def validate_computational_cost(
    max_moves: int,
    max_nodes: int = None,
    warn_threshold: float = 0.7
) -> dict:
    """
    Valida el costo computacional estimado de una operación.
    
    Args:
        max_moves: Número de movimientos/iteraciones
        max_nodes: Número de nodos (opcional)
        warn_threshold: Umbral para advertencias (0-1)
        
    Returns:
        Dict con 'allowed' (bool), 'warning' (str opcional), 'cost' (float)
    """
    # Límites absolutos
    MAX_MOVES_HARD = 500
    MAX_NODES_HARD = 1000
    
    # Calcular costo estimado (normalizado 0-1)
    move_cost = max_moves / MAX_MOVES_HARD if max_moves else 0
    node_cost = max_nodes / MAX_NODES_HARD if max_nodes else 0
    total_cost = max(move_cost, node_cost)
    
    result = {
        'allowed': total_cost <= 1.0,
        'cost': total_cost,
        'warning': None
    }
    
    # Generar advertencias
    if total_cost > 1.0:
        result['warning'] = "⛔ Operación bloqueada: excede límites de recursos"
    elif total_cost > warn_threshold:
        result['warning'] = f"⚠️ Advertencia: operación costosa (costo: {total_cost:.0%})"
    
    return result


# -----------------------------
# Decorator de Rate Limiting
# -----------------------------
def rate_limited(max_calls: int, time_window: float):
    """
    Decorator que aplica rate limiting a una función.
    
    Args:
        max_calls: Máximo de llamadas permitidas
        time_window: Ventana de tiempo en segundos
        
    Raises:
        RuntimeError: Si se excede el límite de llamadas
    """
    limiter = SimpleRateLimiter(max_calls, time_window)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not limiter.is_allowed():
                wait_time = limiter.time_until_next_allowed()
                raise RuntimeError(
                    f"Rate limit excedido. Espera {wait_time:.1f}s antes de intentar nuevamente."
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# -----------------------------
# Tests unitarios
# -----------------------------
if __name__ == "__main__":
    import pytest
    
    # Test timeout decorator
    @timeout(2)
    def fast_function():
        time.sleep(0.5)
        return "completado"
    
    @timeout(1)
    def slow_function():
        time.sleep(3)
        return "nunca llega aquí"
    
    # Test básico
    assert fast_function() == "completado"
    
    try:
        slow_function()
        assert False, "Debería haber lanzado TimeoutError"
    except TimeoutError:
        logger.info("✓ Timeout funciona correctamente")
    
    # Test rate limiter
    limiter = SimpleRateLimiter(max_calls=3, time_window=2.0)
    
    assert limiter.is_allowed()  # 1
    assert limiter.is_allowed()  # 2
    assert limiter.is_allowed()  # 3
    assert not limiter.is_allowed()  # 4 - bloqueado
    
    logger.info("✓ Rate limiter funciona correctamente")
    
    # Test validación
    result = validate_computational_cost(max_moves=100)
    assert result['allowed']
    assert result['warning'] is None
    
    result = validate_computational_cost(max_moves=600)
    assert not result['allowed']
    assert result['warning'] is not None
    
    logger.info("✓ Validación de recursos funciona correctamente")
    
    print("\n✅ Todos los tests pasaron")
