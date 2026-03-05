import pytest

from explanations import (
    Interpreter,
    obtener_explicacion,
    obtener_explicacion_ia,
    obtener_explicacion_con_fuente,
)


class DummyResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class DummyResponsesAPI:
    def __init__(self, output_text: str = "Explicación IA", fail: bool = False):
        self.output_text = output_text
        self.fail = fail

    def create(self, **kwargs):
        if self.fail:
            raise RuntimeError("IA no disponible")
        return DummyResponse(self.output_text)


class DummyClient:
    def __init__(self, output_text: str = "Explicación IA", fail: bool = False):
        self.responses = DummyResponsesAPI(output_text=output_text, fail=fail)


def valid_scenario():
    return {"name": "Escenario A", "H_eff": 72.4, "decay": 0.8}


class TestInterpreter:
    @pytest.mark.parametrize("oyente", ["técnico", "no técnico", "gerencial", "usuario final"])
    def test_interpreter_supported_audiences(self, oyente):
        text = Interpreter(valid_scenario(), "Alpha", oyente).interpret()
        assert "'Escenario A'" in text
        assert "Alpha" in text
        # Verificar que cada audiencia tiene contenido específico diferente
        if oyente == "técnico":
            assert "H_eff" in text or "Holgura efectiva" in text
        elif oyente == "no técnico":
            assert "¿Qué significa esto?" in text or "significa" in text.lower()
        elif oyente == "gerencial":
            assert "IMPACTO" in text or "negocio" in text.lower()
        elif oyente == "usuario final":
            assert "sistema" in text.lower()
    
    def test_interpreter_narratives_vary_by_classification(self):
        """Verificar que las narrativas varían según clasificación"""
        scenarios = [
            ({"name": "Alpha", "H_eff": 80.0, "decay": 0.5}, "Alpha"),
            ({"name": "Beta", "H_eff": 50.0, "decay": 2.0}, "Beta"),
            ({"name": "Gamma", "H_eff": 20.0, "decay": 5.0}, "Gamma"),
        ]
        
        for scenario, classification in scenarios:
            text_tecnico = Interpreter(scenario, classification, "técnico").interpret()
            text_gerencial = Interpreter(scenario, classification, "gerencial").interpret()
            
            # Cada clasificación debe tener indicadores específicos
            if classification == "Alpha":
                assert "resiliente" in text_tecnico.lower() or "bien" in text_gerencial.lower()
            elif classification == "Beta":
                assert "moderada" in text_tecnico.lower() or "medio" in text_gerencial.lower()
            elif classification == "Gamma":
                assert "crítico" in text_tecnico.lower() or "riesgo" in text_gerencial.lower()
    
    def test_interpreter_narratives_vary_by_audience(self):
        """Verificar que las narrativas varían según tipo de audiencia"""
        scenario = valid_scenario()
        
        text_tecnico = Interpreter(scenario, "Beta", "técnico").interpret()
        text_notecnico = Interpreter(scenario, "Beta", "no técnico").interpret()
        text_gerencial = Interpreter(scenario, "Beta", "gerencial").interpret()
        text_usuario = Interpreter(scenario, "Beta", "usuario final").interpret()
        
        # Todos deben ser diferentes
        narrativas = [text_tecnico, text_notecnico, text_gerencial, text_usuario]
        for i, n1 in enumerate(narrativas):
            for j, n2 in enumerate(narrativas):
                if i != j:
                    # Las narrativas deben ser sustancialmente diferentes
                    assert n1 != n2, f"Narrativas {i} y {j} son idénticas"

    def test_interpreter_unknown_audience(self):
        with pytest.raises(ValueError, match="Tipo de oyente desconocido"):
            Interpreter(valid_scenario(), "Alpha", "desconocido")


class TestIA:
    def test_obtener_explicacion_ia_success(self):
        client = DummyClient(output_text="Texto IA OK")
        text = obtener_explicacion_ia(valid_scenario(), "Alpha", "técnico", client=client)
        assert text == "Texto IA OK"

    def test_obtener_explicacion_ia_empty_response(self):
        client = DummyClient(output_text="   ")
        with pytest.raises(RuntimeError, match="Respuesta de IA vacía"):
            obtener_explicacion_ia(valid_scenario(), "Alpha", "técnico", client=client)


class TestFallback:
    def test_obtener_explicacion_fallback_local(self):
        client = DummyClient(fail=True)
        text = obtener_explicacion(valid_scenario(), "Alpha", "gerencial", client=client)
        assert "IMPACTO" in text or "Resumen ejecutivo" in text

    def test_obtener_explicacion_uses_ia_when_available(self):
        client = DummyClient(output_text="Respuesta IA preferida")
        text = obtener_explicacion(valid_scenario(), "Alpha", "no técnico", client=client)
        assert text == "Respuesta IA preferida"

    def test_obtener_explicacion_con_fuente_ia(self):
        client = DummyClient(output_text="Respuesta IA")
        text, source = obtener_explicacion_con_fuente(
            valid_scenario(),
            "Alpha",
            "técnico",
            client=client,
        )
        assert text == "Respuesta IA"
        assert source == "IA"

    def test_obtener_explicacion_con_fuente_fallback(self):
        client = DummyClient(fail=True)
        text, source = obtener_explicacion_con_fuente(
            valid_scenario(),
            "Alpha",
            "técnico",
            client=client,
        )
        assert "'Escenario A'" in text
        assert source == "LOCAL_FALLBACK"


class TestValidations:
    def test_invalid_scenario_name(self):
        with pytest.raises(ValueError, match="name"):
            obtener_explicacion({"name": "", "H_eff": 10.0, "decay": 1.0}, "Alpha", "técnico")

    def test_invalid_h_eff(self):
        with pytest.raises(ValueError, match="H_eff"):
            obtener_explicacion({"name": "X", "H_eff": 0, "decay": 1.0}, "Alpha", "técnico")

    def test_invalid_decay(self):
        with pytest.raises(ValueError, match="decay"):
            obtener_explicacion({"name": "X", "H_eff": 10.0, "decay": -1.0}, "Alpha", "técnico")

    def test_accepts_dh_eff_dt_as_decay_alias(self):
        scenario = {"name": "X", "H_eff": 10.0, "dH_eff_dt": 1.2}
        text = obtener_explicacion(scenario, "Beta", "usuario final", client=DummyClient("IA"))
        assert text == "IA"

    def test_invalid_classification(self):
        with pytest.raises(ValueError, match="classification"):
            obtener_explicacion(valid_scenario(), "", "técnico")
