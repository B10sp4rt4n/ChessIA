# demo.py
# Structural Health Engine - Demo Grafo
# Visualización estructural (Streamlit)
# NOTA: Este es un DEMO simplificado, no el motor productivo.

from typing import Dict, Tuple
import streamlit as st
import networkx as nx
import random

# Reproducibilidad para demos
random.seed(42)

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
# Construcción del grafo
# -----------------------------
def build_graph(n: int = 6) -> Tuple[nx.Graph, Dict[str, Node]]:
    """Construye un grafo aleatorio con nodos estructurales."""
    G = nx.Graph()
    nodes = {}

    for i in range(n):
        cap = random.randint(80, 120)
        load = random.randint(40, cap)
        node = Node(f"N{i}", cap, load)
        nodes[node.name] = node
        G.add_node(node.name, slack=node.slack)

    # Asegurar conectividad mínima
    for _ in range(n + 2):
        a, b = random.sample(list(nodes.keys()), 2)
        G.add_edge(a, b, friction=random.uniform(0.1, 0.5))

    return G, nodes


# -----------------------------
# Métricas estructurales
# -----------------------------
def compute_metrics(G: nx.Graph, nodes: Dict[str, Node]) -> Tuple[float, float, float]:
    """
    Calcula métricas estructurales observables.
    
    H: holgura total (suma de slacks)
    H_eff: holgura efectiva (ponderada por conectividad estructural)
    S: entropía estructural (desbalance de carga)
    
    NOTA: H_eff aquí usa grado normalizado como proxy de accesibilidad.
    El motor productivo usa criterios más complejos no revelados.
    """
    H = sum(n.slack for n in nodes.values())
    
    # H_eff: ponderar slack por accesibilidad estructural (grado del nodo)
    if G.number_of_edges() == 0:
        # Grafo sin conexiones: H_eff = 0 (ninguna holgura es accesible)
        H_eff = 0.0
    else:
        max_degree = max(dict(G.degree()).values()) if G.number_of_nodes() > 0 else 1
        H_eff = 0.0
        for name, node in nodes.items():
            if node.slack > 0:
                degree = G.degree(name)
                accessibility = degree / max_degree  # Factor estructural observable
                H_eff += node.slack * accessibility
    
    # Entropía S: desviación estándar de la utilización normalizada
    utilizations = [n.load / n.capacity if n.capacity > 0 else 0 for n in nodes.values()]
    mean_util = sum(utilizations) / len(utilizations) if utilizations else 0
    variance = sum((u - mean_util) ** 2 for u in utilizations) / len(utilizations) if utilizations else 0
    S = variance ** 0.5
    
    return H, H_eff, S


# -----------------------------
# UI
# -----------------------------
st.sidebar.header("Parámetros")
num_nodes = st.sidebar.slider("Número de nodos", 3, 12, 6)

if st.sidebar.button("Generar sistema"):
    random.seed()  # Permitir variación en generaciones manuales
    st.session_state["graph"] = build_graph(num_nodes)

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
    degree = G.degree(n.name)
    st.write(f"- {n.name}: carga={n.load}, capacidad={n.capacity}, holgura={n.slack}, grado={degree}")

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
