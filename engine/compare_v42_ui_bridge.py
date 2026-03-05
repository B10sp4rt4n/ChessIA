"""Puente entre valores de UI y motor compare_v42.

Este módulo permite testear la integración de parámetros de interfaz
sin depender del runtime de Streamlit.
"""

from typing import Dict, List

from compare_v42 import Scenario, compare_with_thresholds


def build_thresholds(alpha_h: float, alpha_decay: float, beta_h: float) -> Dict[str, float]:
    """Construye objeto thresholds con formato esperado por el motor."""
    return {
        "alpha_h_min": alpha_h,
        "alpha_decay_max": alpha_decay,
        "beta_h_min": beta_h,
    }


def compare_from_ui(
    scenarios: List[Scenario],
    alpha_h: float,
    alpha_decay: float,
    beta_h: float,
    sim_steps: int,
):
    """Ejecuta comparación usando valores provenientes de controles UI."""
    thresholds = build_thresholds(alpha_h, alpha_decay, beta_h)
    return compare_with_thresholds(
        scenarios=scenarios,
        thresholds=thresholds,
        steps=sim_steps,
    )
