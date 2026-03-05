"""
narrativas_chess.py
Motor de narrativas específico para Chess Demo
Genera explicaciones contextualizadas para posiciones de ajedrez
"""

from typing import Tuple, Dict, Any
import chess
import logging
import os

logger = logging.getLogger(__name__)


def generar_narrativa_chess(
    board: chess.Board,
    H: float,
    H_eff: float,
    turn: int,
    oyente_type: str = "técnico"
) -> Tuple[str, str]:
    """
    Genera narrativa específica para posición de ajedrez.
    
    Args:
        board: Tablero de ajedrez
        H: Holgura total
        H_eff: Holgura efectiva
        turn: Número de movimiento
        oyente_type: Tipo de audiencia
    
    Returns:
        Tuple[str, str]: (narrativa, fuente)
    """
    # Clasificar según ratio H_eff/H
    ratio = (H_eff / H * 100) if H > 0 else 0
    
    if ratio >= 15:
        classification = "Alpha"
    elif ratio >= 8:
        classification = "Beta"
    else:
        classification = "Gamma"
    
    # Calcular decay
    if turn > 0:
        initial_h_eff = 20.0
        decay_rate = (initial_h_eff - H_eff) / turn
    else:
        decay_rate = 0.0
    
    # Métricas de ajedrez
    white_pieces = len([p for p in board.piece_map().values() if p.color == chess.WHITE])
    black_pieces = len([p for p in board.piece_map().values() if p.color == chess.BLACK])
    total_pieces = white_pieces + black_pieces
    legal_moves = board.legal_moves.count()
    
    # Intentar generar con IA
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "sk-your-key-here":
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            
            # Prompt específico para AJEDREZ
            system_msg = _get_system_message_chess(oyente_type)
            prompt = _build_chess_prompt(
                turn, total_pieces, white_pieces, black_pieces,
                legal_moves, H, H_eff, ratio, decay_rate,
                classification, oyente_type, board
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
        logger.warning(f"Error en IA para chess: {e}")
    
    # Fallback local específico para ajedrez
    return _generar_fallback_chess(
        turn, total_pieces, white_pieces, black_pieces,
        legal_moves, H, H_eff, ratio, decay_rate,
        classification, oyente_type
    ), "LOCAL"


def _get_system_message_chess(oyente_type: str) -> str:
    """Mensajes de sistema específicos para análisis de ajedrez."""
    messages = {
        "técnico": (
            "Eres un experto en análisis estructural de posiciones de ajedrez. "
            "Explicas métricas de movilidad, balance táctico y redistribución de piezas "
            "con precisión técnica y recomendaciones estratégicas."
        ),
        "no técnico": (
            "Eres un entrenador de ajedrez que explica posiciones de forma simple. "
            "Usas analogías cotidianas y lenguaje accesible sin perder la esencia táctica."
        ),
        "gerencial": (
            "Eres un consultor estratégico que traduce posiciones de ajedrez a decisiones tácticas, "
            "ventajas competitivas y evaluación de riesgos operacionales."
        ),
        "usuario final": (
            "Eres un asistente amigable que explica jugadas de ajedrez de forma ultra-simple, "
            "enfocándote en qué significa la posición y qué debería hacer el jugador."
        )
    }
    return messages.get(oyente_type, messages["técnico"])


def _build_chess_prompt(
    turn, total_pieces, white_pieces, black_pieces,
    legal_moves, H, H_eff, ratio, decay_rate,
    classification, oyente_type, board
) -> str:
    """Construye prompt específico para contexto de ajedrez."""
    
    # Estado del juego
    game_state = []
    if board.is_check():
        game_state.append("REY EN JAQUE")
    if board.is_checkmate():
        game_state.append("JAQUE MATE")
    if board.is_stalemate():
        game_state.append("TABLAS POR AHOGADO")
    
    estado_str = f" - Estado especial: {', '.join(game_state)}" if game_state else ""
    
    return (
        f"ANÁLISIS ESTRUCTURAL DE POSICIÓN DE AJEDREZ\n\n"
        f"Contexto del juego:\n"
        f"- Movimiento: {turn}\n"
        f"- Piezas activas: {total_pieces} ({white_pieces} blancas vs {black_pieces} negras)\n"
        f"- Movimientos legales: {legal_moves}\n"
        f"- Turno: {'Blancas' if board.turn else 'Negras'}{estado_str}\n\n"
        f"Métricas estructurales:\n"
        f"- Clasificación: {classification}\n"
        f"- Holgura total (H): {H:.2f} (capacidad base de todas las piezas)\n"
        f"- Holgura efectiva (H_eff): {H_eff:.2f} (capacidad ponderada por movilidad)\n"
        f"- Ratio de movilidad: {ratio:.1f}% (H_eff/H)\n"
        f"- Tasa de cambio: {decay_rate:.2f}/movimiento\n\n"
        f"Genera una explicación COMPLETA para audiencia '{oyente_type}' sobre esta POSICIÓN DE AJEDREZ:\n"
        f"1. Por qué recibió esta clasificación estructural ({classification})\n"
        f"2. Qué significa el ratio de movilidad {ratio:.1f}% en términos tácticos\n"
        f"3. Implicaciones para el juego (ventaja, equilibrio, desventaja)\n"
        f"4. Recomendaciones estratégicas específicas para esta posición\n\n"
        f"IMPORTANTE: Usa terminología de AJEDREZ (piezas, movilidad, táctica, desarrollo, control) "
        f"NO de ingeniería estructural. Formato claro con emojis ♔♕♖♗♘♙. Completa todas las secciones."
    )


def _generar_fallback_chess(
    turn, total_pieces, white_pieces, black_pieces,
    legal_moves, H, H_eff, ratio, decay_rate,
    classification, oyente_type
) -> str:
    """Fallback local específico para ajedrez."""
    
    estado_emoji = "✅" if classification == "Alpha" else "⚠️" if classification == "Beta" else "🚨"
    
    base = (
        f"{estado_emoji} **Análisis de Posición - Movimiento {turn}**\n\n"
        f"**Clasificación:** {classification}\n"
        f"**Material:** {total_pieces} piezas ({white_pieces}♔ vs {black_pieces}♚)\n"
        f"**Movimientos disponibles:** {legal_moves}\n\n"
        f"**Métricas de Movilidad:**\n"
        f"- Capacidad base (H): {H:.1f}\n"
        f"- Movilidad efectiva (H_eff): {H_eff:.1f}\n"
        f"- Ratio de actividad: {ratio:.1f}%\n"
        f"- Tendencia: {decay_rate:.2f}/movimiento\n\n"
    )
    
    if classification == "Alpha":
        base += (
            "♔ **Posición Excelente**\n"
            "Las piezas tienen alta movilidad y opciones tácticas. "
            f"Con {ratio:.0f}% de capacidad activa, la posición permite "
            "redistribución flexible y múltiples planes estratégicos.\n\n"
            "🎯 **Recomendación:** Mantener iniciativa, explotar movilidad superior."
        )
    elif classification == "Beta":
        base += (
            "⚖️ **Posición Equilibrada**\n"
            "Las piezas tienen movilidad moderada. "
            f"Con {ratio:.0f}% de capacidad activa, la posición requiere "
            "juego preciso para mantener el balance.\n\n"
            "🎯 **Recomendación:** Mejorar posición de piezas menos activas, evitar cambios desfavorables."
        )
    else:
        base += (
            "⚔️ **Posición Crítica**\n"
            "Las piezas tienen movilidad limitada o material reducido. "
            f"Con solo {ratio:.0f}% de capacidad activa, la posición requiere "
            "defensa precisa o podría colapsar.\n\n"
            "🎯 **Recomendación:** Buscar activación de piezas inmediatamente, considerar sacrificios posicionales."
        )
    
    return base
