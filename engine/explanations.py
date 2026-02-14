from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import logging
import os


logger = logging.getLogger(__name__)

OYENTE_TYPES = {
    "técnico",
    "no técnico",
    "gerencial",
    "usuario final",
}


def _validate_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(scenario, dict):
        raise ValueError(f"scenario debe ser dict, recibido {type(scenario).__name__}")

    name = scenario.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("scenario['name'] debe ser string no vacío")

    h_eff = scenario.get("H_eff")
    if not isinstance(h_eff, (int, float)) or h_eff <= 0:
        raise ValueError("scenario['H_eff'] debe ser numérico y > 0")

    decay = scenario.get("decay", scenario.get("dH_eff_dt"))
    if not isinstance(decay, (int, float)) or decay <= 0:
        raise ValueError("scenario['decay'] (o dH_eff_dt) debe ser numérico y > 0")

    return {
        "name": name.strip(),
        "H_eff": float(h_eff),
        "decay": float(decay),
    }


def _validate_classification(classification: str) -> str:
    if not isinstance(classification, str) or not classification.strip():
        raise ValueError("classification debe ser string no vacío")
    return classification.strip()


def _validate_oyente_type(oyente_type: str) -> str:
    if not isinstance(oyente_type, str):
        raise ValueError(f"oyente_type debe ser str, recibido {type(oyente_type).__name__}")
    normalized = oyente_type.strip()
    if normalized not in OYENTE_TYPES:
        raise ValueError(f"Tipo de oyente desconocido: {normalized}")
    return normalized


def obtener_explicacion_ia(
    scenario: Dict[str, Any],
    classification: str,
    oyente_type: str,
    *,
    model: str = "gpt-4o-mini",
    client: Any = None,
) -> str:
    scenario_clean = _validate_scenario(scenario)
    classification_clean = _validate_classification(classification)
    oyente_clean = _validate_oyente_type(oyente_type)

    prompt = (
        f"El sistema clasificó el escenario como {classification_clean}. "
        f"Explica por qué fue clasificado así para un oyente {oyente_clean}. "
        f"Usa lenguaje claro y accionable. "
        f"Detalles: nombre={scenario_clean['name']}, H_eff={scenario_clean['H_eff']:.2f}, "
        f"decay={scenario_clean['decay']:.2f}."
    )

    try:
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY no configurada")
            try:
                from openai import OpenAI
            except Exception as import_error:
                raise RuntimeError("SDK openai no disponible") from import_error
            client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.7,
            max_output_tokens=220,
        )

        text = getattr(response, "output_text", None)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Respuesta de IA vacía")
        return text.strip()

    except Exception as e:
        logger.error(f"Error al obtener explicación de IA: {e}")
        raise


@dataclass
class Interpreter:
    scenario: Dict[str, Any]
    classification: str
    oyente_type: str = "técnico"

    def __post_init__(self):
        self.scenario = _validate_scenario(self.scenario)
        self.classification = _validate_classification(self.classification)
        self.oyente_type = _validate_oyente_type(self.oyente_type)

    def interpret(self) -> str:
        if self.oyente_type == "técnico":
            return self._interpret_tecnico()
        if self.oyente_type == "no técnico":
            return self._interpret_no_tecnico()
        if self.oyente_type == "gerencial":
            return self._interpret_gerencial()
        if self.oyente_type == "usuario final":
            return self._interpret_usuario_final()
        raise ValueError("Tipo de oyente desconocido")

    def _interpret_tecnico(self) -> str:
        return (
            f"Escenario: {self.scenario['name']}\n"
            f"Clasificación: {self.classification}\n"
            f"Holgura efectiva (H_eff): {self.scenario['H_eff']:.2f}\n"
            f"Tasa de degradación (dH_eff/dt): {self.scenario['decay']:.2f}\n"
            "Modelo usado: degradación lineal simplificada."
        )

    def _interpret_no_tecnico(self) -> str:
        return (
            f"Escenario: {self.scenario['name']}\n"
            f"Clasificación: {self.classification}\n"
            "La clasificación depende de cuánta holgura tiene el sistema y qué tan rápido se degrada. "
            "Alpha indica salud alta, Beta intermedia y Gamma riesgo elevado."
        )

    def _interpret_gerencial(self) -> str:
        return (
            f"Escenario: {self.scenario['name']}\n"
            f"Clasificación: {self.classification}\n"
            "Impacto negocio: degradación alta incrementa riesgo operativo y costo de mantenimiento. "
            "Recomendación: priorizar mitigación temprana en escenarios Beta/Gamma."
        )

    def _interpret_usuario_final(self) -> str:
        return (
            f"Escenario: {self.scenario['name']}\n"
            f"Clasificación: {self.classification}\n"
            "Esta clasificación resume qué tan estable está el sistema hoy y su tendencia. "
            "Alpha suele ser estable; Gamma requiere atención pronta."
        )


def obtener_explicacion(
    scenario: Dict[str, Any],
    classification: str,
    oyente_type: str = "técnico",
    *,
    client: Any = None,
) -> str:
    text, _ = obtener_explicacion_con_fuente(
        scenario=scenario,
        classification=classification,
        oyente_type=oyente_type,
        client=client,
    )
    return text


def obtener_explicacion_con_fuente(
    scenario: Dict[str, Any],
    classification: str,
    oyente_type: str = "técnico",
    *,
    client: Any = None,
) -> tuple[str, str]:
    scenario_clean = _validate_scenario(scenario)
    classification_clean = _validate_classification(classification)
    oyente_clean = _validate_oyente_type(oyente_type)

    try:
        text = obtener_explicacion_ia(
            scenario_clean,
            classification_clean,
            oyente_clean,
            client=client,
        )
        return text, "IA"
    except Exception as e:
        logger.warning(f"Falló la IA, usando interpretación local: {e}")
        interpreter = Interpreter(scenario_clean, classification_clean, oyente_clean)
        return interpreter.interpret(), "LOCAL_FALLBACK"
