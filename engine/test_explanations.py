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
        assert "Escenario: Escenario A" in text
        assert "Clasificación: Alpha" in text

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
        assert "Impacto negocio" in text

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
        assert "Escenario: Escenario A" in text
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
