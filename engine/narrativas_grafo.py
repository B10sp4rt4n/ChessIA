"""
narrativas_grafo.py
Motor de narrativas específico para Demo Grafo
Genera explicaciones contextualizadas para sistemas de grafos/redes
"""

from typing import Tuple
import networkx as nx
import logging
import os

logger = logging.getLogger(__name__)


def generar_narrativa_grafo(
    G: nx.Graph,
    nodes: dict,
    H: float,
    H_eff: float,
    S: float,
    oyente_type: str = "técnico"
) -> Tuple[str, str]:
    """
    Genera narrativa específica para sistema de grafo.
    
    Args:
        G: Grafo NetworkX
        nodes: Diccionario de nodos con sus propiedades
        H: Holgura total
        H_eff: Holgura efectiva
        S: Entropía
        oyente_type: Tipo de audiencia
    
    Returns:
        Tuple[str, str]: (narrativa, fuente)
    """
    # Clasificar según H_eff
    if H_eff > 50:
        classification = "Alpha"
    elif H_eff > 20:
        classification = "Beta"
    else:
        classification = "Gamma"
    
    # Métricas del grafo
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = nx.density(G)
    
    # Calcular conectividad
    if nx.is_connected(G):
        connectivity_status = "CONECTADO"
        components = 1
    else:
        connectivity_status = "FRAGMENTADO"
        components = nx.number_connected_components(G)
    
    # Decay estimado
    ratio = (H_eff / H * 100) if H > 0 else 0
    decay_rate = (100 - ratio) / max(num_nodes, 1)
    
    # Intentar generar con IA
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "sk-your-key-here":
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            
            # Prompt específico para GRAFOS
            system_msg = _get_system_message_grafo(oyente_type)
            prompt = _build_grafo_prompt(
                num_nodes, num_edges, density, connectivity_status,
                components, H, H_eff, S, ratio, decay_rate,
                classification, oyente_type
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            text = response.choices[0].message.content
            if text and text.strip():
                return text.strip(), "IA"
    
    except Exception as e:
        logger.warning(f"Error en IA para grafo: {e}")
    
    # Fallback local específico para grafos
    return _generar_fallback_grafo(
        num_nodes, num_edges, density, connectivity_status,
        components, H, H_eff, S, ratio, decay_rate,
        classification, oyente_type
    ), "LOCAL"


def _get_system_message_grafo(oyente_type: str) -> str:
    """Mensajes de sistema específicos para análisis de grafos."""
    messages = {
        "técnico": (
            "Eres un experto en análisis de redes y sistemas estructurales. "
            "Explicas métricas de conectividad, redundancia y capacidad de redistribución "
            "con precisión técnica y recomendaciones de ingeniería."
        ),
        "no técnico": (
            "Eres un comunicador experto que explica sistemas de redes de forma simple. "
            "Usas analogías como redes eléctricas, carreteras o tuberías. "
            "Lenguaje accesible sin perder la esencia estructural."
        ),
        "gerencial": (
            "Eres un consultor ejecutivo que traduce métricas de redes a impacto de negocio, "
            "disponibilidad de servicio, ROI de redundancia y decisiones de inversión en infraestructura."
        ),
        "usuario final": (
            "Eres un asistente amigable que explica el estado de la red de forma ultra-simple, "
            "enfocándote en si el servicio funcionará bien y qué esperar."
        )
    }
    return messages.get(oyente_type, messages["técnico"])


def _build_grafo_prompt(
    num_nodes, num_edges, density, connectivity_status,
    components, H, H_eff, S, ratio, decay_rate,
    classification, oyente_type
) -> str:
    """Construye prompt específico para contexto de grafos."""
    
    return (
        f"ANÁLISIS ESTRUCTURAL DE SISTEMA DE RED/GRAFO\n\n"
        f"Topología de la red:\n"
        f"- Nodos: {num_nodes}\n"
        f"- Conexiones (aristas): {num_edges}\n"
        f"- Densidad: {density:.2%} (qué tan conectada está la red)\n"
        f"- Estado de conectividad: {connectivity_status}\n"
        f"- Componentes independientes: {components}\n\n"
        f"Métricas estructurales:\n"
        f"- Clasificación: {classification}\n"
        f"- Holgura total (H): {H:.2f} (capacidad total disponible en todos los nodos)\n"
        f"- Holgura efectiva (H_eff): {H_eff:.2f} (capacidad accesible considerando conectividad)\n"
        f"- Entropía (S): {S:.3f} (desbalance de carga entre nodos)\n"
        f"- Ratio de accesibilidad: {ratio:.1f}% (H_eff/H)\n"
        f"- Tasa de degradación estimada: {decay_rate:.2f}/nodo\n\n"
        f"Genera una explicación COMPLETA para audiencia '{oyente_type}' sobre esta RED/GRAFO:\n"
        f"1. Por qué recibió esta clasificación estructural ({classification})\n"
        f"2. Qué significa el ratio de accesibilidad {ratio:.1f}% para la redundancia del sistema\n"
        f"3. Implicaciones de la conectividad ({connectivity_status}) y entropía ({S:.3f})\n"
        f"4. Recomendaciones específicas para mejorar o mantener la red\n\n"
        f"IMPORTANTE: Usa terminología de REDES/GRAFOS (nodos, conexiones, redundancia, rutas, "
        f"distribución de carga) NO de ajedrez. Formato claro con emojis 🕸️📊🔗. Completa todas las secciones."
    )


def _generar_fallback_grafo(
    num_nodes, num_edges, density, connectivity_status,
    components, H, H_eff, S, ratio, decay_rate,
    classification, oyente_type
) -> str:
    """Fallback local específico para grafos."""
    
    estado_emoji = "✅" if classification == "Alpha" else "⚠️" if classification == "Beta" else "🚨"
    
    base = (
        f"{estado_emoji} **Análisis de Red Estructural**\n\n"
        f"**Clasificación:** {classification}\n"
        f"**Topología:** {num_nodes} nodos, {num_edges} conexiones\n"
        f"**Conectividad:** {connectivity_status} ({components} componente{'s' if components > 1 else ''})\n"
        f"**Densidad:** {density:.1%}\n\n"
        f"**Métricas Estructurales:**\n"
        f"- Capacidad total (H): {H:.1f}\n"
        f"- Capacidad accesible (H_eff): {H_eff:.1f}\n"
        f"- Ratio de accesibilidad: {ratio:.1f}%\n"
        f"- Entropía (S): {S:.3f} (desbalance de carga)\n\n"
    )
    
    if classification == "Alpha":
        base += (
            "🕸️ **Red Resiliente**\n"
            f"El sistema tiene alta redundancia y conectividad. Con {ratio:.0f}% de capacidad "
            "accesible, la red puede redistribuir carga eficientemente y tolerar múltiples fallas.\n\n"
            "🎯 **Recomendación:** Monitoreo estándar suficiente. Red apta para crecimiento."
        )
    elif classification == "Beta":
        base += (
            "🔗 **Red Funcional con Límites**\n"
            f"El sistema tiene redundancia moderada. Con {ratio:.0f}% de capacidad "
            "accesible, la red funciona pero fallas adicionales podrían comprometer el servicio.\n\n"
            "🎯 **Recomendación:** Agregar conexiones críticas, balancear carga entre nodos."
        )
    else:
        base += (
            "⚡ **Red en Riesgo Crítico**\n"
            f"El sistema tiene redundancia mínima o nula. Con solo {ratio:.0f}% de capacidad "
            "accesible, la red es vulnerable a fallas en cascada.\n\n"
            "🎯 **Recomendación:** Refuerzo urgente de conectividad, identificar nodos críticos, "
            "agregar rutas alternativas inmediatamente."
        )
    
    return base
