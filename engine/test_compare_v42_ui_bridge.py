import pytest

from compare_v42 import Scenario
from compare_v42_ui_bridge import build_thresholds, compare_from_ui


class TestUIBridge:
    """Tests de integración entre parámetros de UI y motor compare_v42."""

    def test_build_thresholds_mapping(self):
        thresholds = build_thresholds(60.0, 1.0, 30.0)

        assert thresholds == {
            "alpha_h_min": 60.0,
            "alpha_decay_max": 1.0,
            "beta_h_min": 30.0,
        }

    def test_compare_from_ui_propagates_steps(self):
        scenarios = [Scenario("Escenario X", 10.0, 2.0)]

        ranking = compare_from_ui(
            scenarios=scenarios,
            alpha_h=60.0,
            alpha_decay=1.0,
            beta_h=30.0,
            sim_steps=3,
        )

        assert len(ranking) == 1
        assert ranking[0]["H_eff"] == 6.0
        assert ranking[0]["dH_eff_dt"] == 2.0

    def test_compare_from_ui_propagates_thresholds(self):
        scenarios = [Scenario("Escenario Y", 50.0, 0.5)]

        ranking = compare_from_ui(
            scenarios=scenarios,
            alpha_h=45.0,
            alpha_decay=1.0,
            beta_h=30.0,
            sim_steps=1,
        )

        assert ranking[0]["class"] == "Alpha"

    def test_compare_from_ui_invalid_steps(self):
        scenarios = [Scenario("Escenario Z", 50.0, 1.0)]

        with pytest.raises(ValueError, match="steps fuera de rango"):
            compare_from_ui(
                scenarios=scenarios,
                alpha_h=60.0,
                alpha_decay=1.0,
                beta_h=30.0,
                sim_steps=0,
            )
