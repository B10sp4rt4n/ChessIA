# demo_app.py
# Interfaz Streamlit para Demo Grafo (Structural Health Engine)

import streamlit as st
import networkx as nx
import random
import logging
from typing import Optional
from demo import (
    build_graph,
    compute_metrics,
    Node,
    TimeoutError
)
from rate_limiter import validate_computational_cost

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_cached_cost_validation(
    cache_key: str,
    *,
    max_moves: int,
    max_nodes: Optional[int] = None,
    warn_threshold: float = 0.7,
    force_refresh: bool = False
) -> dict:
    """Obtiene validación de costo con caché en session_state."""
    cache = st.session_state.get(cache_key)
    cache_params = (max_moves, max_nodes, warn_threshold)

    if (
        force_refresh
        or cache is None
        or cache.get("params") != cache_params
    ):
        result = validate_computational_cost(
            max_moves=max_moves,
            max_nodes=max_nodes,
            warn_threshold=warn_threshold
        )
        st.session_state[cache_key] = {
            "params": cache_params,
            "result": result
        }
        return result

    return cache["result"]


def get_cached_graph_metrics(G, nodes):
    """Calcula métricas solo cuando cambia el sistema generado."""
    cache = st.session_state.get("demo_graph_metrics_cache")
    if cache is not None and cache.get("graph_ref") is G and cache.get("nodes_ref") is nodes:
        return cache["metrics"]

    metrics = compute_metrics(G, nodes)
    st.session_state["demo_graph_metrics_cache"] = {
        "graph_ref": G,
        "nodes_ref": nodes,
        "metrics": metrics
    }
    return metrics

st.set_page_config(page_title="SHE Demo - Modo Grafo", layout="wide")

st.title("Structural Health Engine · Demo Grafo")
st.caption("Demo experimental — holgura, accesibilidad estructural y colapso")

st.warning(
    """
    ⚠️ **Demo Simplificado**
    
    Este demo muestra conceptos estructurales observables:
    - **H (Holgura total)**: Capacidad disponible en el sistema
    - **H_eff (Holgura efectiva)**: Capacidad accesible según conectividad
    - **S (Entropía)**: Desbalance de carga en la estructura
    
    El motor productivo usa criterios más complejos no revelados aquí.
    """
)

# -----------------------------
# Sidebar: Parámetros
# -----------------------------
st.sidebar.header("Parámetros")
num_nodes = st.sidebar.slider("Número de nodos", 3, 20, 6)
generate_clicked = st.sidebar.button("🎲 Generar sistema", type="primary")

# Validar costo computacional
cost_validation = get_cached_cost_validation(
    "demo_app_cost_validation",
    max_moves=100,
    max_nodes=num_nodes,
    force_refresh=generate_clicked
)
if cost_validation['warning']:
    if cost_validation['allowed']:
        st.sidebar.warning(cost_validation['warning'])
    else:
        st.sidebar.error(cost_validation['warning'])
        num_nodes = 6  # Forzar valor seguro

st.sidebar.divider()
st.sidebar.header("Acciones")

if generate_clicked:
    try:
        # Crear nuevo RNG para cada generación manual
        new_rng = random.Random()
        with st.spinner(f"Generando sistema con {num_nodes} nodos..."):
            G, nodes = build_graph(num_nodes, rng=new_rng)
            st.session_state["graph"] = (G, nodes)
            st.session_state["num_nodes"] = num_nodes
        st.success(f"✅ Sistema generado con {num_nodes} nodos")
    except TimeoutError:
        st.error("⏱️ Timeout: La generación del sistema tomó demasiado tiempo (>30s). Reduce el número de nodos.")
        logger.error(f"Timeout en generación con num_nodes={num_nodes}")
    except Exception as e:
        st.error(f"Error generando sistema: {e}")
        logger.error(f"Error en generación manual: {e}", exc_info=True)

# Inicializar grafo si no existe
if "graph" not in st.session_state:
    try:
        with st.spinner("Inicializando sistema..."):
            G, nodes = build_graph(num_nodes)
            st.session_state["graph"] = (G, nodes)
            st.session_state["num_nodes"] = num_nodes
    except Exception as e:
        st.error(f"Error inicializando sistema: {e}")
        logger.critical(f"Error en inicialización: {e}", exc_info=True)
        st.stop()

# Obtener grafo actual
try:
    G, nodes = st.session_state["graph"]
except Exception as e:
    st.error(f"Error recuperando grafo: {e}")
    st.stop()

# -----------------------------
# Métricas principales
# -----------------------------
st.subheader("📊 Métricas Estructurales")

try:
    H, H_eff, S = get_cached_graph_metrics(G, nodes)

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Holgura total (H)", 
            f"{H:.1f}",
            help="Suma de capacidad no utilizada en todos los nodos"
        )
    
    with col2:
        st.metric(
            "Holgura efectiva (H_eff)", 
            f"{H_eff:.1f}",
            help="Capacidad accesible ponderada por conectividad estructural"
        )
    
    with col3:
        st.metric(
            "Entropía (S)", 
            f"{S:.3f}",
            help="Desviación estándar de utilización (mayor S = mayor fragilidad)"
        )

    # Clasificación de estado
    if H_eff > 0:
        state = "🟢 VIVO"
        state_help = "Sistema con holgura accesible para redistribuir presión"
    elif H > 0:
        state = "🟡 ZOMBI"
        state_help = "Sistema con capacidad pero sin accesibilidad estructural"
    else:
        state = "🔴 COLAPSADO"
        state_help = "Sistema sin capacidad disponible"
    
    with col4:
        st.metric(
            "Estado", 
            state,
            help=state_help
        )

except Exception as e:
    st.error(f"Error calculando métricas: {e}")
    logger.error(f"Error en compute_metrics: {e}", exc_info=True)

# -----------------------------
# Visualización de nodos
# -----------------------------
st.divider()
st.subheader("🔧 Detalles de Nodos")

try:
    # Crear tabla de datos
    node_data = []
    for n in nodes.values():
        degree = G.degree(n.name)
        utilization = (n.load / n.capacity * 100) if n.capacity > 0 else 0
        
        node_data.append({
            "Nodo": n.name,
            "Carga": f"{n.load:.0f}",
            "Capacidad": f"{n.capacity:.0f}",
            "Holgura": f"{n.slack:.1f}",
            "Utilización": f"{utilization:.1f}%",
            "Grado": degree
        })
    
    st.dataframe(
        node_data,
        use_container_width=True,
        hide_index=True
    )
    
    # Estadísticas adicionales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_load = sum(n.load for n in nodes.values())
        total_capacity = sum(n.capacity for n in nodes.values())
        st.metric("Carga total", f"{total_load:.0f}")
    
    with col2:
        st.metric("Capacidad total", f"{total_capacity:.0f}")
    
    with col3:
        avg_utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0
        st.metric("Utilización promedio", f"{avg_utilization:.1f}%")

except Exception as e:
    st.error(f"Error mostrando nodos: {e}")
    logger.error(f"Error en visualización de nodos: {e}", exc_info=True)

# -----------------------------
# Topología del grafo
# -----------------------------
st.divider()
st.subheader("🕸️ Topología de Red")

try:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nodos", G.number_of_nodes())
    
    with col2:
        st.metric("Aristas", G.number_of_edges())
    
    with col3:
        is_connected = nx.is_connected(G)
        st.metric("Conectado", "✓ Sí" if is_connected else "✗ No")
    
    with col4:
        if is_connected:
            avg_path = nx.average_shortest_path_length(G)
            st.metric("Distancia promedio", f"{avg_path:.2f}")
        else:
            components = nx.number_connected_components(G)
            st.metric("Componentes", components)
    
    # Información de aristas
    if st.checkbox("Mostrar detalles de aristas"):
        edge_data = []
        for u, v, data in G.edges(data=True):
            friction = data.get('friction', 0)
            edge_data.append({
                "Desde": u,
                "Hasta": v,
                "Fricción": f"{friction:.3f}"
            })
        
        st.dataframe(
            edge_data,
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Error analizando topología: {e}")
    logger.error(f"Error en análisis de topología: {e}", exc_info=True)

# -----------------------------
# Interpretación
# -----------------------------
st.divider()
st.subheader("💡 Interpretación")

st.markdown("""
Este demo muestra cómo **la holgura efectiva** depende de la conectividad estructural, no solo de la capacidad total.

### Métricas Clave:

- **H (Holgura total)**: Suma de capacidad disponible en todos los nodos. Mide el "espacio" total del sistema.

- **H_eff (Holgura efectiva)**: Mide cuánta de esa capacidad es realmente **accesible** para redistribuir presión estructural. 
  Pondera la holgura de cada nodo por su conectividad (grado normalizado).

- **S (Entropía estructural)**: Mide el desbalance interno del sistema. Mayor S significa mayor heterogeneidad 
  en la utilización de capacidad → sistema más frágil.

### Estados Estructurales:

1. **🟢 VIVO** (H_eff > 0): Sistema saludable con capacidad accesible
2. **🟡 ZOMBI** (H > 0, H_eff = 0): Tiene capacidad pero no puede usarla (nodos desconectados o mal estructurados)
3. **🔴 COLAPSADO** (H = 0): Sin capacidad disponible

### Ejemplo de Estado ZOMBI:

Un sistema con H > 0 pero H_eff = 0 está en **estado ZOMBI**: tiene capacidad total disponible, 
pero esa capacidad no es estructuralmente accesible. Esto puede ocurrir cuando:
- Nodos con holgura están desconectados
- Los nodos conectados están todos saturados
- La fricción de las conexiones es muy alta

---
**Nota:** Este demo usa un modelo simplificado donde la accesibilidad se aproxima con el grado del nodo normalizado. 
El motor productivo usa criterios estructurales más complejos.
""")

# -----------------------------
# Footer
# -----------------------------
st.divider()
st.caption("SHE Demo Grafo v4.5 | Laboratorio de métricas estructurales")
