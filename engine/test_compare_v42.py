# test_compare_v42.py
# Tests unitarios para el Comparador Estructural v4.2

import pytest
from compare_v42 import (
    Scenario,
    classify,
    compare,
    ALPHA_H_EFF_MIN,
    ALPHA_DECAY_MAX,
    BETA_H_EFF_MIN
)


class TestScenario:
    """Tests para la clase Scenario."""
    
    def test_scenario_initialization(self):
        """Verificar que Scenario se inicializa correctamente."""
        s = Scenario("Test A", 75.0, 1.2)
        assert s.name == "Test A"
        assert s.H_eff_init == 75.0
        assert s.decay == 1.2
    
    def test_scenario_simulate_basic(self):
        """Verificar simulación básica con degradación lineal."""
        s = Scenario("Test", 10.0, 2.0)
        values = s.simulate(steps=5)
        
        assert len(values) == 5
        assert values[0] == 10.0
        assert values[1] == 8.0
        assert values[2] == 6.0
        assert values[3] == 4.0
        assert values[4] == 2.0
    
    def test_scenario_simulate_floor_at_zero(self):
        """Verificar que H_eff no se hace negativo."""
        s = Scenario("Test", 5.0, 3.0)
        values = s.simulate(steps=3)
        
        assert values[0] == 5.0
        assert values[1] == 2.0
        assert values[2] == 0.0  # No debe ser negativo
    
    def test_scenario_simulate_no_decay(self):
        """Verificar simulación sin degradación."""
        s = Scenario("Estable", 50.0, 0.0)
        values = s.simulate(steps=5)
        
        assert all(v == 50.0 for v in values)
    
    def test_scenario_simulate_default_steps(self):
        """Verificar que el default de steps=10 funciona."""
        s = Scenario("Test", 100.0, 5.0)
        values = s.simulate()
        
        assert len(values) == 10


class TestClassify:
    """Tests para la función classify."""
    
    def test_classify_alpha_high_h_low_decay(self):
        """Escenario Alpha: H_eff alto y decay bajo."""
        result = classify(H_eff=70.0, dH=0.5)
        assert result == "Alpha"
    
    def test_classify_alpha_boundary(self):
        """Verificar umbral exacto de Alpha."""
        # Justo en el límite (H_eff > 60 y dH < 1)
        result = classify(H_eff=60.1, dH=0.9)
        assert result == "Alpha"
    
    def test_classify_beta_moderate_h(self):
        """Escenario Beta: H_eff moderado."""
        result = classify(H_eff=45.0, dH=2.0)
        assert result == "Beta"
    
    def test_classify_beta_boundary(self):
        """Verificar umbral exacto de Beta."""
        result = classify(H_eff=30.1, dH=5.0)
        assert result == "Beta"
    
    def test_classify_gamma_low_h(self):
        """Escenario Gamma: H_eff bajo."""
        result = classify(H_eff=20.0, dH=3.0)
        assert result == "Gamma"
    
    def test_classify_gamma_high_decay(self):
        """Escenario Gamma: Decay alto aunque H_eff sea moderado."""
        # Si H_eff > 60 pero dH >= 1, no es Alpha (porque dH >= alpha_decay_max=1.0)
        result = classify(H_eff=65.0, dH=5.0)
        assert result == "Beta"  # dH alto descalifica de Alpha
        
        # Pero si H_eff es menor y decay es alto
        result = classify(H_eff=50.0, dH=5.0)
        assert result == "Beta"
    
    def test_classify_custom_thresholds(self):
        """Verificar que umbrales configurables funcionan."""
        result = classify(
            H_eff=50.0,
            dH=0.5,
            alpha_h_min=45.0,  # Umbral más bajo
            alpha_decay_max=1.0,
            beta_h_min=20.0
        )
        assert result == "Alpha"
    
    def test_classify_edge_cases(self):
        """Verificar casos extremos."""
        # H_eff = 0
        assert classify(H_eff=0.0, dH=0.0) == "Gamma"
        
        # H_eff muy alto
        assert classify(H_eff=1000.0, dH=0.1) == "Alpha"


class TestCompare:
    """Tests para la función compare."""
    
    def test_compare_basic_ranking(self):
        """Verificar ranking básico: mayor H_eff primero."""
        scenarios = [
            Scenario("C", 30.0, 2.0),
            Scenario("A", 70.0, 1.0),
            Scenario("B", 50.0, 1.5),
        ]
        
        ranking = compare(scenarios)
        
        assert len(ranking) == 3
        assert ranking[0]["name"] == "A"  # Mayor H_eff
        assert ranking[1]["name"] == "B"
        assert ranking[2]["name"] == "C"
    
    def test_compare_tie_breaking_by_decay(self):
        """Si H_eff es igual, menor decay gana."""
        scenarios = [
            Scenario("A", 50.0, 2.0),
            Scenario("B", 50.0, 1.0),  # Mismo H_eff, menor decay
        ]
        
        ranking = compare(scenarios)
        
        assert ranking[0]["name"] == "B"  # Menor decay
        assert ranking[1]["name"] == "A"
    
    def test_compare_metrics_structure(self):
        """Verificar estructura de resultados."""
        scenarios = [Scenario("Test", 60.0, 1.5)]
        ranking = compare(scenarios)
        
        assert len(ranking) == 1
        result = ranking[0]
        
        assert "name" in result
        assert "H_eff" in result
        assert "dH_eff_dt" in result
        assert "class" in result
        
        assert result["name"] == "Test"
        assert result["H_eff"] == 60.0
        assert result["dH_eff_dt"] > 0  # Debe haber degradación calculada
    
    def test_compare_classification_integration(self):
        """Verificar que compare usa classify correctamente."""
        scenarios = [
            Scenario("Alpha", 70.0, 0.8),
            Scenario("Beta", 50.0, 2.0),
            Scenario("Gamma", 25.0, 4.0),
        ]
        
        ranking = compare(scenarios)
        
        assert ranking[0]["class"] == "Alpha"
        assert ranking[1]["class"] == "Beta"
        assert ranking[2]["class"] == "Gamma"
    
    def test_compare_empty_list(self):
        """Verificar comportamiento con lista vacía."""
        ranking = compare([])
        assert ranking == []
    
    def test_compare_single_scenario(self):
        """Verificar con un solo escenario."""
        scenarios = [Scenario("Solo", 45.0, 1.2)]
        ranking = compare(scenarios)
        
        assert len(ranking) == 1
        assert ranking[0]["name"] == "Solo"
    
    def test_compare_custom_thresholds(self):
        """Verificar que compare respeta umbrales personalizados."""
        scenarios = [Scenario("Test", 55.0, 0.5)]
        
        # Con umbrales estándar
        ranking_default = compare(scenarios)
        assert ranking_default[0]["class"] == "Beta"  # 55 < 60
        
        # Con umbrales personalizados (alpha_h_min=50)
        ranking_custom = compare(scenarios, alpha_h_min=50.0, alpha_decay_max=1.0)
        assert ranking_custom[0]["class"] == "Alpha"  # 55 > 50


class TestConstants:
    """Tests para constantes del módulo."""
    
    def test_default_constants_values(self):
        """Verificar valores por defecto de constantes."""
        assert ALPHA_H_EFF_MIN == 60.0
        assert ALPHA_DECAY_MAX == 1.0
        assert BETA_H_EFF_MIN == 30.0
    
    def test_constants_are_reasonable(self):
        """Verificar que constantes tienen valores razonables."""
        assert ALPHA_H_EFF_MIN > BETA_H_EFF_MIN
        assert ALPHA_DECAY_MAX > 0
        assert BETA_H_EFF_MIN > 0


# Fixtures para casos de uso comunes
@pytest.fixture
def example_scenarios():
    """Fixture con escenarios de ejemplo para tests."""
    return [
        Scenario("Escenario A", 72.4, 0.8),
        Scenario("Escenario B", 51.6, 2.1),
        Scenario("Escenario C", 28.9, 4.5),
    ]


def test_integration_full_workflow(example_scenarios):
    """Test de integración: workflow completo."""
    # Simular escenarios
    for scenario in example_scenarios:
        values = scenario.simulate(steps=10)
        assert len(values) == 10
        assert all(v >= 0 for v in values)  # Ningún valor negativo
    
    # Comparar
    ranking = compare(example_scenarios)
    
    # Verificar ranking correcto
    assert len(ranking) == 3
    assert ranking[0]["name"] == "Escenario A"
    assert ranking[0]["class"] == "Alpha"
    
    # Verificar orden decreciente de H_eff
    assert ranking[0]["H_eff"] > ranking[1]["H_eff"] > ranking[2]["H_eff"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
