# compare_v42.py
# Structural Health Engine - Comparador Estructural v4.2
# NOTA: Este es un motor de comparación simplificado para demos públicos.
# Los criterios de clasificación son configurables y observables.

from typing import List, Dict, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -----------------------------
# Validación
# -----------------------------
def validate_positive_float(
    value: float,
    name: str,
    max_val: Optional[float] = None,
    allow_zero: bool = True
) -> float:
    """Valida que un valor sea numérico y positivo (estricto u opcionalmente no-negativo)."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} debe ser numérico, recibido {type(value).__name__}")
    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} no puede ser negativo: {value}")
    else:
        if value <= 0:
            raise ValueError(f"{name} debe ser > 0: {value}")
    if max_val is not None and value > max_val:
        raise ValueError(f"{name} excede máximo permitido {max_val}: {value}")
    return float(value)


def validate_steps(steps: int) -> int:
    """Valida número de pasos de simulación."""
    if not isinstance(steps, int):
        raise ValueError(f"steps debe ser int, recibido {type(steps).__name__}")
    if not 1 <= steps <= 1000:
        raise ValueError(f"steps fuera de rango [1, 1000]: {steps}")
    return steps


def validate_thresholds(thresholds: Dict[str, float]) -> Dict[str, float]:
    """Valida objeto de umbrales para clasificación estructural."""
    if not isinstance(thresholds, dict):
        raise ValueError(f"thresholds debe ser dict, recibido {type(thresholds).__name__}")

    required_keys = {"alpha_h_min", "alpha_decay_max", "beta_h_min"}
    missing = required_keys - set(thresholds.keys())
    if missing:
        raise ValueError(f"thresholds incompleto. Faltan claves: {sorted(missing)}")

    alpha_h_min = validate_positive_float(thresholds["alpha_h_min"], "alpha_h_min")
    alpha_decay_max = validate_positive_float(thresholds["alpha_decay_max"], "alpha_decay_max")
    beta_h_min = validate_positive_float(thresholds["beta_h_min"], "beta_h_min")

    if alpha_h_min <= beta_h_min:
        raise ValueError("alpha_h_min debe ser mayor que beta_h_min")

    return {
        "alpha_h_min": alpha_h_min,
        "alpha_decay_max": alpha_decay_max,
        "beta_h_min": beta_h_min,
    }


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
        try:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Name debe ser string no vacío")
            
            self.name = name.strip()
            self.H_eff_init = validate_positive_float(
                H_eff_init,
                "H_eff_init",
                max_val=10000,
                allow_zero=False
            )
            self.decay = validate_positive_float(
                decay,
                "decay",
                max_val=10000,
                allow_zero=False
            )
            
            logger.debug(f"Scenario creado: {name}, H_eff={H_eff_init}, decay={decay}")
            
        except (TypeError, ValueError) as e:
            logger.error(f"Error creando Scenario: {e}")
            raise

    def simulate(self, steps: int = 10) -> List[float]:
        """
        Simula evolución temporal de H_eff mediante modelo lineal simple.
        
        Args:
            steps: Número de pasos de simulación (1-1000)
            
        Returns:
            Lista de valores H_eff a lo largo del tiempo
            
        Raises:
            TypeError: Si steps no es int
            ValueError: Si steps fuera de rango
        
        NOTA: Este es un modelo demostrativo simplificado.
        El motor productivo usa modelos de degradación más complejos.
        """
        try:
            steps = validate_steps(steps)
            logger.debug(f"Simulando {self.name} por {steps} pasos")
            
            values = []
            H = self.H_eff_init
            for _ in range(steps):
                values.append(H)
                H = max(H - self.decay, 0)
            
            logger.debug(f"Simulación completa: {len(values)} valores")
            return values
            
        except ValueError as e:
            logger.error(f"Error en simulate para {self.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en simulate: {e}", exc_info=True)
            raise RuntimeError(f"Fallo en simulación: {e}") from e


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
    
    Args:
        H_eff: Holgura efectiva actual
        dH: Tasa de degradación
        alpha_h_min: Umbral mínimo para Alpha
        alpha_decay_max: Máxima degradación permitida para Alpha
        beta_h_min: Umbral mínimo para Beta
        
    Returns:
        Clasificación: "Alpha", "Beta" o "Gamma"
        
    Raises:
        TypeError: Si los parámetros no son numéricos
        ValueError: Si los parámetros son negativos
    
    Criterios observables:
    - Alpha: alta holgura efectiva y degradación lenta
    - Beta: holgura moderada
    - Gamma: holgura baja o degradación rápida
    
    Los umbrales son configurables y dependen del contexto del sistema.
    """
    try:
        H_eff = validate_positive_float(H_eff, "H_eff")
        dH = validate_positive_float(dH, "dH")
        alpha_h_min = validate_positive_float(alpha_h_min, "alpha_h_min")
        alpha_decay_max = validate_positive_float(alpha_decay_max, "alpha_decay_max")
        beta_h_min = validate_positive_float(beta_h_min, "beta_h_min")
        
        if H_eff > alpha_h_min and dH < alpha_decay_max:
            result = "Alpha"
        elif H_eff > beta_h_min:
            result = "Beta"
        else:
            result = "Gamma"
        
        logger.debug(f"Clasificación: H_eff={H_eff:.1f}, dH={dH:.2f} → {result}")
        return result
        
    except ValueError as e:
        logger.error(f"Error en classify: {e}")
        raise


# -----------------------------
# Comparación
# -----------------------------
def compare(
    scenarios: List[Scenario],
    alpha_h_min: float = ALPHA_H_EFF_MIN,
    alpha_decay_max: float = ALPHA_DECAY_MAX,
    beta_h_min: float = BETA_H_EFF_MIN,
    steps: int = 1
) -> List[Dict]:
    """
    Compara múltiples escenarios y genera un ranking estructural.
    
    Args:
        scenarios: Lista de escenarios a comparar
        alpha_h_min: Umbral Alpha para H_eff
        alpha_decay_max: Umbral Alpha para decay
        beta_h_min: Umbral Beta para H_eff
        steps: Pasos de simulación (1-1000)
        
    Returns:
        Lista ordenada de diccionarios con métricas y clasificación
        
    Raises:
        TypeError: Si scenarios no es lista
        ValueError: Si scenarios está vacía
    
    El ranking se ordena por:
    1. Mayor H_eff inicial
    2. Menor |dH_eff/dt|
    
    Retorna lista ordenada de resultados con métricas y clasificación.
    """
    try:
        if not isinstance(scenarios, list):
            raise ValueError(f"scenarios debe ser lista, recibido {type(scenarios).__name__}")
        if len(scenarios) == 0:
            logger.warning("compare llamado con lista vacía")
            return []

        steps = validate_steps(steps)
        alpha_h_min = validate_positive_float(alpha_h_min, "alpha_h_min")
        alpha_decay_max = validate_positive_float(alpha_decay_max, "alpha_decay_max")
        beta_h_min = validate_positive_float(beta_h_min, "beta_h_min")
        
        logger.info(f"Comparando {len(scenarios)} escenarios")
        results = []

        for s in scenarios:
            if not isinstance(s, Scenario):
                raise ValueError(f"Elemento debe ser Scenario, recibido {type(s).__name__}")
            
            try:
                series = s.simulate(steps=steps)
                current_h_eff = series[-1] if steps > 1 else s.H_eff_init
                dH = s.decay
                cls = classify(current_h_eff, dH, alpha_h_min, alpha_decay_max, beta_h_min)

                results.append({
                    "name": s.name,
                    "H_eff": current_h_eff,
                    "dH_eff_dt": dH,
                    "class": cls
                })
            except Exception as e:
                logger.error(f"Error procesando escenario {s.name}: {e}")
                # Continuar con otros escenarios
                continue

        # Ranking estructural: mayor H_eff, menor degradación
        results.sort(
            key=lambda x: (-x["H_eff"], x["dH_eff_dt"])
        )
        
        logger.info(f"Comparación completa: {len(results)} resultados")
        return results
        
    except ValueError as e:
        logger.error(f"Error en compare: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en compare: {e}", exc_info=True)
        raise RuntimeError(f"Fallo en comparación: {e}") from e


def compare_with_thresholds(
    scenarios: List[Scenario],
    thresholds: Dict[str, float],
    steps: int
) -> List[Dict]:
    """
    API explícita para comparar escenarios usando objeto `thresholds` + `steps`.
    """
    validated = validate_thresholds(thresholds)
    return compare(
        scenarios=scenarios,
        alpha_h_min=validated["alpha_h_min"],
        alpha_decay_max=validated["alpha_decay_max"],
        beta_h_min=validated["beta_h_min"],
        steps=steps,
    )


# -----------------------------
# Ejecución directa
# -----------------------------
if __name__ == "__main__":
    try:
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
    except Exception as e:
        logger.critical(f"Error crítico en ejecución: {e}", exc_info=True)
        print(f"\n⚠️ ERROR: {e}")
        raise
