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

    # Personalizar mensaje del sistema según audiencia
    system_messages = {
        "técnico": "Eres un experto en análisis estructural de sistemas complejos. Explicas métricas técnicas con precisión, incluyendo ratios, recomendaciones específicas y acciones preventivas.",
        "no técnico": "Eres un comunicador experto que explica conceptos técnicos de forma simple usando analogías y lenguaje cotidiano, sin perder precisión.",
        "gerencial": "Eres un consultor ejecutivo que traduce métricas técnicas a impacto de negocio, ROI, decisiones estratégicas y riesgos operativos.",
        "usuario final": "Eres un asistente amigable que explica tecnología de forma ultra-simple, enfocándote en qué significa para el usuario y qué debe hacer."
    }
    
    system_msg = system_messages.get(oyente_clean, system_messages["técnico"])
    
    # Prompt estructurado con contexto completo
    prompt = (
        f"Escenario: '{scenario_clean['name']}'\n"
        f"Clasificación: {classification_clean}\n"
        f"Holgura efectiva (H_eff): {scenario_clean['H_eff']:.2f}\n"
        f"Tasa de degradación (dH/dt): {scenario_clean['decay']:.2f}/paso\n\n"
        f"Genera una explicación COMPLETA para audiencia '{oyente_clean}' que incluya:\n"
        f"1. Por qué recibió esta clasificación\n"
        f"2. Qué significa cada métrica en este contexto\n"
        f"3. Implicaciones prácticas\n"
        f"4. Recomendaciones accionables específicas\n\n"
        f"Usa formato claro con emojis. NO CORTES LA EXPLICACIÓN A LA MITAD. Completa todas las secciones."
    )

    try:
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "sk-your-key-here":
                raise RuntimeError("OPENAI_API_KEY no configurada")
            try:
                from openai import OpenAI
            except Exception as import_error:
                raise RuntimeError("SDK openai no disponible") from import_error
            client = OpenAI(api_key=api_key)

        # Usar API real de OpenAI (chat.completions)
        if hasattr(client, 'chat'):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200,  # Aumentado a 1200 para narrativas completas sin truncamiento
            )
            text = response.choices[0].message.content
        else:
            # Fallback para DummyClient en tests
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
        name = self.scenario['name']
        cls = self.classification
        h_eff = self.scenario['H_eff']
        decay = self.scenario['decay']
        
        base = (
            f"📊 Análisis técnico de '{name}'\n\n"
            f"Clasificación: {cls}\n"
            f"• Holgura efectiva (H_eff): {h_eff:.2f}\n"
            f"• Tasa de degradación (dH/dt): {decay:.2f}/paso\n\n"
        )
        
        if cls == "Alpha":
            base += (
                "✅ Sistema resiliente\n"
                f"• Ratio degradación/capacidad: {(decay/h_eff*100):.1f}%\n"
                "• Capacidad de redistribución: ALTA\n"
                "• Recomendación: Monitoreo estándar suficiente\n"
                "• Acción preventiva: No requerida a corto plazo"
            )
        elif cls == "Beta":
            base += (
                "⚠️ Sistema en degradación moderada\n"
                f"• Ratio degradación/capacidad: {(decay/h_eff*100):.1f}%\n"
                "• Capacidad de redistribución: MODERADA\n"
                "• Recomendación: Monitoreo intensivo + análisis de tendencias\n"
                "• Acción preventiva: Planificar refuerzos a mediano plazo"
            )
        else:  # Gamma
            base += (
                "🚨 Sistema en riesgo crítico\n"
                f"• Ratio degradación/capacidad: {(decay/h_eff*100):.1f}%\n"
                "• Capacidad de redistribución: BAJA/NULA\n"
                "• Recomendación: Intervención inmediata requerida\n"
                "• Acción correctiva: Refuerzo estructural urgente"
            )
        
        return base

    def _interpret_no_tecnico(self) -> str:
        name = self.scenario['name']
        cls = self.classification
        h_eff = self.scenario['H_eff']
        decay = self.scenario['decay']
        
        base = f"🔍 Análisis de '{name}'\n\nClasificación: {cls}\n\n"
        
        if cls == "Alpha":
            base += (
                "✅ ¿Qué significa esto?\n"
                "Tu sistema está en excelente salud. Tiene suficiente capacidad para manejar problemas "
                "y se degrada muy lentamente. Es como un edificio nuevo con mantenimiento regular.\n\n"
                "🎯 ¿Qué hacer?\n"
                "Continúa con el mantenimiento normal. No hay urgencias.\n\n"
                f"📈 Datos: Capacidad={h_eff:.0f}, Desgaste={decay:.1f}/día"
            )
        elif cls == "Beta":
            base += (
                "⚠️ ¿Qué significa esto?\n"
                "Tu sistema funciona, pero está mostrando desgaste. Tiene capacidad moderada y se degrada "
                "a un ritmo que requiere atención. Es como un edificio que necesita mantenimiento pronto.\n\n"
                "🎯 ¿Qué hacer?\n"
                "Programa inspecciones más frecuentes y planea mejoras en los próximos meses.\n\n"
                f"📈 Datos: Capacidad={h_eff:.0f}, Desgaste={decay:.1f}/día"
            )
        else:  # Gamma
            base += (
                "🚨 ¿Qué significa esto?\n"
                "Tu sistema está en situación delicada. La capacidad es baja y el desgaste es rápido. "
                "Es como un edificio antiguo que necesita reparaciones urgentes o podría fallar.\n\n"
                "🎯 ¿Qué hacer?\n"
                "Actúa YA. Contacta a expertos para evaluar y reforzar el sistema cuanto antes.\n\n"
                f"📈 Datos: Capacidad={h_eff:.0f}, Desgaste={decay:.1f}/día"
            )
        
        return base

    def _interpret_gerencial(self) -> str:
        name = self.scenario['name']
        cls = self.classification
        h_eff = self.scenario['H_eff']
        decay = self.scenario['decay']
        
        base = f"💼 Resumen ejecutivo: '{name}'\n\nClasificación: {cls}\n\n"
        
        if cls == "Alpha":
            base += (
                "✅ IMPACTO NEGOCIO\n"
                "• Riesgo operativo: BAJO\n"
                "• Inversión requerida: Mantenimiento estándar\n"
                "• Disponibilidad proyectada: >99%\n"
                "• Costo total de operación: CONTROLADO\n\n"
                "💡 DECISIÓN RECOMENDADA\n"
                "Mantener presupuesto actual de operaciones. Sin necesidad de inversión adicional. "
                "Sistema apto para expansión de servicios.\n\n"
                f"📊 KPIs: H_eff={h_eff:.0f} | dH/dt={decay:.1f} | ROI mantenimiento: POSITIVO"
            )
        elif cls == "Beta":
            base += (
                "⚠️ IMPACTO NEGOCIO\n"
                "• Riesgo operativo: MEDIO-ALTO\n"
                "• Inversión requerida: Refuerzos planificados (Q2-Q3)\n"
                "• Disponibilidad proyectada: 95-98%\n"
                "• Costo total de operación: EN AUMENTO\n\n"
                "💡 DECISIÓN RECOMENDADA\n"
                "Aprobar presupuesto para mejoras incrementales en próximos 6 meses. "
                "Riesgo de interrupción de servicio si no se actúa. Costo diferido será 2-3x mayor.\n\n"
                f"📊 KPIs: H_eff={h_eff:.0f} | dH/dt={decay:.1f} | ROI intervención: 2.5x"
            )
        else:  # Gamma
            base += (
                "🚨 IMPACTO NEGOCIO\n"
                "• Riesgo operativo: CRÍTICO\n"
                "• Inversión requerida: Intervención inmediata + contingencia\n"
                "• Disponibilidad proyectada: <90% (riesgo de falla total)\n"
                "• Costo total de operación: FUERA DE CONTROL\n\n"
                "💡 DECISIÓN RECOMENDADA\n"
                "Aprobar intervención de emergencia HOY. Pérdidas proyectadas por inacción: "
                "50-100K/día en downtime. Activar protocolo de contingencia y equipo de respuesta rápida.\n\n"
                f"📊 KPIs: H_eff={h_eff:.0f} | dH/dt={decay:.1f} | EXPOSURE: ALTO"
            )
        
        return base

    def _interpret_usuario_final(self) -> str:
        name = self.scenario['name']
        cls = self.classification
        
        base = f"👤 Estado del sistema: '{name}'\n\nNivel de salud: {cls}\n\n"
        
        if cls == "Alpha":
            base += (
                "✅ TODO ESTÁ BIEN\n\n"
                "Tu sistema está funcionando perfectamente. No hay nada de qué preocuparse. "
                "Puedes seguir usándolo normalmente sin interrupciones.\n\n"
                "🤔 ¿Y esto qué significa para mí?\n"
                "• El servicio estará disponible sin problemas\n"
                "• No habrá mantenimientos de emergencia\n"
                "• Puedes confiar en el sistema para tus tareas diarias\n\n"
                "🎯 ¿Necesito hacer algo?\n"
                "No. Solo continúa usando el sistema normalmente."
            )
        elif cls == "Beta":
            base += (
                "⚠️ ATENCIÓN: Sistema en mantenimiento preventivo\n\n"
                "Tu sistema funciona bien ahora, pero necesita algunas mejoras pronto para evitar problemas futuros. "
                "Es como llevar tu auto al taller antes de que se descomponga.\n\n"
                "🤔 ¿Y esto qué significa para mí?\n"
                "• Podrías experimentar mantenimientos programados pronto\n"
                "• El servicio puede ser un poco más lento de lo normal\n"
                "• Es importante que reportes cualquier problema que notes\n\n"
                "🎯 ¿Necesito hacer algo?\n"
                "Sí: Guarda tu trabajo con más frecuencia y estate atento a notificaciones de mantenimiento."
            )
        else:  # Gamma
            base += (
                "🚨 ALERTA: Sistema requiere atención urgente\n\n"
                "Tu sistema está en situación delicada y podría fallar pronto. No es seguro depender completamente "
                "de él ahora mismo. Piensa en él como un servicio en emergencia.\n\n"
                "🤔 ¿Y esto qué significa para mí?\n"
                "• Pueden ocurrir interrupciones sin aviso previo\n"
                "• Algunos servicios podrían no estar disponibles\n"
                "• El sistema puede fallar en momentos críticos\n\n"
                "🎯 ¿Necesito hacer algo?\n"
                "SÍ, URGENTE: \n"
                "1. Respalda tu trabajo AHORA\n"
                "2. Ten un plan alternativo listo\n"
                "3. No dependas del sistema para tareas críticas hasta nuevo aviso"
            )
        
        return base


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
