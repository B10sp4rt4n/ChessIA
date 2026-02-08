# compare_v42.py
# Structural Health Engine - Comparador Estructural v4.2
# NOTA: Este es un motor de comparación simplificado para demos públicos.
# Los criterios de clasificación son configurables y observables.

from typing import List, Dict

# -----------------------------
# Configuración de clasificación
# -----------------------------
# Umbrales estructurales (configurables)
ALPHA_H_EFF_MIN = 60.0
ALPHA_DECAY_MAX = 1.0
BETA_H_EFF_MIN = 30.0


# -----------------------------
# Escenario estructural
# -----------------------------
class Scenario:
    """
    Representa un escenario estructural con holgura efectiva inicial
    y velocidad de degradación (decay).
    """
    
    def __init__(self, name: str, H_eff_init: float, decay: float):
        self.name = name
        self.H_eff_init = H_eff_init
        self.decay = decay

    def simulate(self, steps: int = 10) -> List[float]:
        """
        Simula evolución temporal de H_eff mediante modelo lineal simple.
        
        NOTA: Este es un modelo demostrativo simplificado.
        El motor productivo usa modelos de degradación más complejos.
        """
        values = []
        H = self.H_eff_init
        for _ in range(steps):
            values.append(H)
            H = max(H - self.decay, 0)
        return values


# -----------------------------
# Clasificación v4.2
# -----------------------------
def classify(
    H_eff: float, 
    dH: float,
    alpha_h_min: float = ALPHA_H_EFF_MIN,
    alpha_decay_max: float = ALPHA_DECAY_MAX,
    beta_h_min: float = BETA_H_EFF_MIN
) -> str:
    """
    Clasifica un escenario en Alpha, Beta o Gamma según métricas estructurales.
    
    Criterios observables:
    - Alpha: alta holgura efectiva y degradación lenta
    - Beta: holgura moderada
    - Gamma: holgura baja o degradación rápida
    
    Los umbrales son configurables y dependen del contexto del sistema.
    """
    if H_eff > alpha_h_min and dH < alpha_decay_max:
        return "Alpha"
    if H_eff > beta_h_min:
        return "Beta"
    return "Gamma"


# -----------------------------
# Comparación
# -----------------------------
def compare(
    scenarios: List[Scenario],
    alpha_h_min: float = ALPHA_H_EFF_MIN,
    alpha_decay_max: float = ALPHA_DECAY_MAX,
    beta_h_min: float = BETA_H_EFF_MIN
) -> List[Dict]:
    """
    Compara múltiples escenarios y genera un ranking estructural.
    
    El ranking se ordena por:
    1. Mayor H_eff inicial
    2. Menor |dH_eff/dt|
    
    Retorna lista ordenada de resultados con métricas y clasificación.
    """
    results = []

    for s in scenarios:
        series = s.simulate()
        dH = abs(series[1] - series[0]) if len(series) > 1 else 0
        cls = classify(series[0], dH, alpha_h_min, alpha_decay_max, beta_h_min)

        results.append({
            "name": s.name,
            "H_eff": series[0],
            "dH_eff_dt": dH,
            "class": cls
        })

    # Ranking estructural: mayor H_eff, menor degradación
    results.sort(
        key=lambda x: (-x["H_eff"], x["dH_eff_dt"])
    )
    return results


# -----------------------------
# Ejecución directa
# -----------------------------
if __name__ == "__main__":
    # Escenarios de ejemplo
    scenarios = [
        Scenario("Escenario A", 72.4, 0.8),
        Scenario("Escenario B", 51.6, 2.1),
        Scenario("Escenario C", 28.9, 4.5),
    ]

    ranking = compare(scenarios)

    print("Comparador Estructural v4.2")
    print("=" * 60)
    print(f"Escenarios evaluados: {len(scenarios)}")
    print(f"Umbrales: Alpha H_eff >{ALPHA_H_EFF_MIN}, decay <{ALPHA_DECAY_MAX}")
    print(f"          Beta H_eff >{BETA_H_EFF_MIN}")
    print("\nRanking estructural:")
    print("-" * 60)
    for i, r in enumerate(ranking, 1):
        print(
            f'{i}. {r["name"]}: '
            f'H_eff={r["H_eff"]:.1f}, '
            f'dH/dt={r["dH_eff_dt"]:.2f}, '
            f'Clase={r["class"]}'
        )
