#!/usr/bin/env python3
# benchmark.py
# Performance benchmarking para módulos principales
# Ayuda a detectar regresiones de rendimiento

import time
import random
import statistics
from typing import Dict, List, Callable, Any
import sys
import json

# Imports de módulos a testear
sys.path.insert(0, 'engine')
from mcl_chess import run_game, compute_holistic_metrics
from demo import build_graph, compute_metrics
from chess_demo import run_game_stepwise
import chess


class Benchmark:
    """Clase para ejecutar y reportar benchmarks."""
    
    def __init__(self, name: str, warmup: int = 2, iterations: int = 10):
        """
        Args:
            name: Nombre del benchmark
            warmup: Número de iteraciones de calentamiento
            iterations: Número de iteraciones para medir
        """
        self.name = name
        self.warmup = warmup
        self.iterations = iterations
        self.results: List[float] = []
    
    def run(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta el benchmark y retorna estadísticas.
        
        Returns:
            Dict con mean, median, min, max, stddev en segundos
        """
        print(f"\n🔬 Benchmark: {self.name}")
        print(f"   Warmup: {self.warmup} iterations")
        print(f"   Measuring: {self.iterations} iterations")
        
        # Warmup
        for _ in range(self.warmup):
            func(*args, **kwargs)
        
        # Mediciones reales
        self.results = []
        for i in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            self.results.append(elapsed)
            print(f"   Iteration {i+1}/{self.iterations}: {elapsed:.4f}s")
        
        # Calcular estadísticas
        stats = {
            'name': self.name,
            'mean': statistics.mean(self.results),
            'median': statistics.median(self.results),
            'min': min(self.results),
            'max': max(self.results),
            'stddev': statistics.stdev(self.results) if len(self.results) > 1 else 0.0,
            'iterations': self.iterations
        }
        
        print(f"\n   📊 Results:")
        print(f"      Mean:   {stats['mean']:.4f}s")
        print(f"      Median: {stats['median']:.4f}s")
        print(f"      Min:    {stats['min']:.4f}s")
        print(f"      Max:    {stats['max']:.4f}s")
        print(f"      StdDev: {stats['stddev']:.4f}s")
        
        return stats


def benchmark_mcl_chess_small():
    """Benchmark: mcl_chess.run_game() con 10 movimientos."""
    rng = random.Random(42)
    run_game(max_moves=10, rng=rng)


def benchmark_mcl_chess_medium():
    """Benchmark: mcl_chess.run_game() con 50 movimientos."""
    rng = random.Random(42)
    run_game(max_moves=50, rng=rng)


def benchmark_mcl_chess_large():
    """Benchmark: mcl_chess.run_game() con 100 movimientos."""
    rng = random.Random(42)
    run_game(max_moves=100, rng=rng)


def benchmark_compute_holistic_metrics():
    """Benchmark: mcl_chess.compute_holistic_metrics()."""
    board = chess.Board()
    # Hacer algunos movimientos
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    compute_holistic_metrics(board)


def benchmark_demo_build_graph_small():
    """Benchmark: demo.build_graph() con 6 nodos."""
    rng = random.Random(42)
    build_graph(n=6, rng=rng)


def benchmark_demo_build_graph_large():
    """Benchmark: demo.build_graph() con 20 nodos."""
    rng = random.Random(42)
    build_graph(n=20, rng=rng)


def benchmark_demo_compute_metrics():
    """Benchmark: demo.compute_metrics()."""
    rng = random.Random(42)
    G, nodes = build_graph(n=10, rng=rng)
    compute_metrics(G, nodes)


def benchmark_chess_demo_small():
    """Benchmark: chess_demo.run_game_stepwise() con 5 movimientos."""
    rng = random.Random(42)
    run_game_stepwise(max_moves=5, rng=rng)


def benchmark_chess_demo_medium():
    """Benchmark: chess_demo.run_game_stepwise() con 20 movimientos."""
    rng = random.Random(42)
    run_game_stepwise(max_moves=20, rng=rng)


# Configuración de benchmarks
BENCHMARKS = [
    ("mcl_chess.compute_holistic_metrics()", benchmark_compute_holistic_metrics, 3, 20),
    ("mcl_chess.run_game(max_moves=10)", benchmark_mcl_chess_small, 2, 10),
    ("mcl_chess.run_game(max_moves=50)", benchmark_mcl_chess_medium, 1, 5),
    ("mcl_chess.run_game(max_moves=100)", benchmark_mcl_chess_large, 1, 3),
    ("demo.build_graph(n=6)", benchmark_demo_build_graph_small, 3, 15),
    ("demo.build_graph(n=20)", benchmark_demo_build_graph_large, 2, 10),
    ("demo.compute_metrics()", benchmark_demo_compute_metrics, 3, 20),
    ("chess_demo.run_game_stepwise(max_moves=5)", benchmark_chess_demo_small, 2, 10),
    ("chess_demo.run_game_stepwise(max_moves=20)", benchmark_chess_demo_medium, 1, 5),
]


def main():
    """Ejecuta todos los benchmarks y genera reporte."""
    print("=" * 80)
    print("🚀 SHE Core - Performance Benchmarks")
    print("=" * 80)
    
    all_results = []
    
    for name, func, warmup, iterations in BENCHMARKS:
        bench = Benchmark(name, warmup=warmup, iterations=iterations)
        try:
            stats = bench.run(func)
            all_results.append(stats)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_results.append({
                'name': name,
                'error': str(e)
            })
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📈 Summary")
    print("=" * 80)
    
    for result in all_results:
        if 'error' in result:
            print(f"❌ {result['name']}: ERROR")
        else:
            print(f"✅ {result['name']}: {result['mean']:.4f}s ± {result['stddev']:.4f}s")
    
    # Generar JSON para CI/CD
    output_file = "benchmark-results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'benchmarks': all_results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("\n✅ Benchmarks completed successfully")


if __name__ == "__main__":
    main()
