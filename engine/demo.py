# demo.py
# Structural Health Engine - Demo Grafo
# Visualización estructural (Streamlit)
# NOTA: Este es un DEMO simplificado, no el motor productivo.

from typing import Dict, Tuple, Optional
import streamlit as st
import networkx as nx
import random
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# RNG aislado para demo (no usar random.seed() global)
_demo_rng = random.Random(42)

st.set_page_config(page_title="SHE Demo - Modo Grafo", layout="wide")

st.title("Structural Health Engine · Demo Grafo")
st.caption("Demo experimental — holgura, accesibilidad estructural y colapso")

# -----------------------------
# Modelo simple de nodo
# -----------------------------
class Node:
    """Contenedor estructural con capacidad y carga finitas."""
    
    def __init__(self, name: str, capacity: float, load: float):
        self.name = name
        self.capacity = capacity
        self.load = load

    @property
    def slack(self) -> float:
        """Holgura local: capacidad aún no utilizada."""
        return max(self.capacity - self.load, 0)

    def __repr__(self) -> str:
        return f"{self.name} (L={self.load}, C={self.capacity})"


# -----------------------------
# Validación
# -----------------------------
def validate_node_count(n: int) -> int:
    """Valida número de nodos."""
    if not isinstance(n, int):
        raise TypeError(f"Número de nodos debe ser int, recibido {type(n).__name__}")
    if not 1 <= n <= 100:
        raise ValueError(f"Número de nodos fuera de rango [1, 100]: {n}")
    return n


# -----------------------------
# Construcción del grafo
# -----------------------------
def build_graph(n: int = 6, rng: Optional[random.Random] = None) -> Tuple[nx.Graph, Dict[str, Node]]:
    """
    Construye un grafo aleatorio con nodos estructurales.
    
    Args:
        n: Número de nodos (1-100)
        rng: Generador random aislado (opcional)
        
    Returns:
        Tuple de (grafo, diccionario de nodos)
        
    Raises:
        TypeError: Si n no es int
        ValueError: Si n fuera de rango
    """
    try:
        n = validate_node_count(n)
        if rng is None:
            rng = _demo_rng
        
        logger.info(f"Construyendo grafo con {n} nodos")
        G = nx.Graph()
        nodes = {}

        for i in range(n):
            cap = rng.randint(80, 120)
            load = rng.randint(40, cap)
            node = Node(f"N{i}", cap, load)
            nodes[node.name] = node
            G.add_node(node.name, slack=node.slack)

        # Asegurar conectividad mínima
        for _ in range(n + 2):
            node_list = list(nodes.keys())
            if len(node_list) < 2:
                break
            a, b = rng.sample(node_list, 2)
            G.add_edge(a, b, friction=rng.uniform(0.1, 0.5))
        
        logger.info(f"Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G, nodes
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error validando parámetros: {e}")
        raise
    except Exception as e:
        logger.error(f"Error construyendo grafo: {e}", exc_info=True)
        raise RuntimeError(f"Fallo al construir grafo: {e}") from e


# -----------------------------
# Métricas estructurales
# -----------------------------
def compute_metrics(G: nx.Graph, nodes: Dict[str, Node]) -> Tuple[float, float, float]:
    """
    Calcula métricas estructurales observables.
    
    Args:
        G: Grafo de NetworkX
        nodes: Diccionario de nodos estructurales
        
    Returns:
        Tuple de (H, H_eff, S):
        - H: holgura total (suma de slacks)
        - H_eff: holgura efectiva (ponderada por conectividad estructural)
        - S: entropía estructural (desbalance de carga)
    
    Raises:
        ValueError: Si el grafo o nodos son inválidos
        
    NOTA: H_eff aquí usa grado normalizado como proxy de accesibilidad.
    El motor productivo usa criterios más complejos no revelados.
    """
    try:
        if not isinstance(G, nx.Graph):
            raise TypeError(f"G debe ser nx.Graph, recibido {type(G).__name__}")
        if not isinstance(nodes, dict):
            raise TypeError(f"nodes debe ser dict, recibido {type(nodes).__name__}")
        if len(nodes) == 0:
            logger.warning("compute_metrics llamado con 0 nodos")
            return 0.0, 0.0, 0.0
        
        logger.debug(f"Calculando métricas para {len(nodes)} nodos")
        
        H = sum(n.slack for n in nodes.values())
        
        # H_eff: ponderar slack por accesibilidad estructural (grado del nodo)
        if G.number_of_edges() == 0:
            # Grafo sin conexiones: H_eff = 0 (ninguna holgura es accesible)
            H_eff = 0.0
        else:
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 1
            H_eff = 0.0
            for name, node in nodes.items():
                if node.slack > 0 and name in degrees:
                    degree = degrees[name]
                    accessibility = degree / max_degree  # Factor estructural observable
                    H_eff += node.slack * accessibility
        
        # Entropía S: desviación estándar de la utilización normalizada
        utilizations = [n.load / n.capacity if n.capacity > 0 else 0 for n in nodes.values()]
        if not utilizations:
            S = 0.0
        else:
            mean_util = sum(utilizations) / len(utilizations)
            variance = sum((u - mean_util) ** 2 for u in utilizations) / len(utilizations)
            S = variance ** 0.5
        
        logger.debug(f"Métricas calculadas: H={H:.2f}, H_eff={H_eff:.2f}, S={S:.3f}")
        return H, H_eff, S
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error validando inputs: {e}")
        raise
    except Exception as e:
        logger.error(f"Error calculando métricas: {e}", exc_info=True)
        raise RuntimeError(f"Fallo al calcular métricas: {e}") from e


# -----------------------------
# UI
# -----------------------------
try:
    st.sidebar.header("Parámetros")
    num_nodes = st.sidebar.slider("Número de nodos", 3, 12, 6)

    if st.sidebar.button("Generar sistema"):
        try:
            # Crear nuevo RNG para cada generación manual
            new_rng = random.Random()
            st.session_state["graph"] = build_graph(num_nodes, rng=new_rng)
            st.success(f"Sistema generado con {num_nodes} nodos")
        except Exception as e:
            st.error(f"Error generando sistema: {e}")
            logger.error(f"Error en generación manual: {e}", exc_info=True)

    if "graph" not in st.session_state:
        st.session_state["graph"] = build_graph(num_nodes)

    G, nodes = st.session_state["graph"]

    H, H_eff, S = compute_metrics(G, nodes)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Holgura total (H)", f"{H:.1f}")
    col2.metric("Holgura efectiva (H_eff)", f"{H_eff:.1f}")
    col3.metric("Entropía (S)", f"{S:.3f}")

    state = "VIVO" if H_eff > 0 else ("ZOMBI" if H > 0 else "COLAPSADO")
    col4.metric("Estado", state)

    st.subheader("Nodos")
    for n in nodes.values():
        try:
            degree = G.degree(n.name)
            st.write(f"- {n.name}: carga={n.load}, capacidad={n.capacity}, holgura={n.slack}, grado={degree}")
        except Exception as e:
            st.error(f"Error mostrando nodo {n.name}: {e}")
            logger.error(f"Error en UI para nodo {n.name}: {e}")

    st.subheader("Interpretación")
    st.write(
        """
Este demo muestra cómo **la holgura efectiva** depende de la conectividad estructural, no solo de la capacidad total.

- **H** mide capacidad disponible.
- **H_eff** mide cuánta de esa capacidad es realmente accesible para redistribuir presión.
- **S** mide el desbalance interno (mayor S → sistema más frágil).

Un sistema con H > 0 pero H_eff = 0 está en **estado ZOMBI**: tiene capacidad, pero no puede usarla.
"""
    )

except Exception as e:
    st.error(f"⚠️ Error crítico en la aplicación: {e}")
    logger.critical(f"Error crítico en UI principal: {e}", exc_info=True)
    st.info("Por favor, recarga la página o contacta al administrador.")
