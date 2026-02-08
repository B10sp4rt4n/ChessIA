# test_demo.py
# Tests unitarios para Demo Grafo

import pytest
import networkx as nx
import random
from demo import (
    Node,
    build_graph,
    compute_metrics
)


class TestNode:
    """Tests para la clase Node."""
    
    def test_node_initialization(self):
        """Verificar inicialización correcta de Node."""
        node = Node("N1", capacity=100.0, load=60.0)
        
        assert node.name == "N1"
        assert node.capacity == 100.0
        assert node.load == 60.0
    
    def test_node_slack_calculation(self):
        """Verificar cálculo de holgura (slack)."""
        node = Node("N1", capacity=100.0, load=60.0)
        assert node.slack == 40.0
    
    def test_node_slack_zero_when_full(self):
        """Slack debe ser 0 cuando carga = capacidad."""
        node = Node("N1", capacity=100.0, load=100.0)
        assert node.slack == 0.0
    
    def test_node_slack_non_negative(self):
        """Slack no debe ser negativo incluso si load > capacity."""
        node = Node("N1", capacity=100.0, load=120.0)
        assert node.slack == 0.0  # max() protege contra negativos
    
    def test_node_repr(self):
        """Verificar representación string de Node."""
        node = Node("N1", capacity=100.0, load=60.0)
        repr_str = repr(node)
        
        assert "N1" in repr_str
        assert "L=60" in repr_str or "60" in repr_str
        assert "C=100" in repr_str or "100" in repr_str
    
    def test_node_slack_is_property(self):
        """Verificar que slack es un property (recalcula automáticamente)."""
        node = Node("N1", capacity=100.0, load=60.0)
        assert node.slack == 40.0
        
        # Cambiar load y verificar que slack se actualiza
        node.load = 80.0
        assert node.slack == 20.0


class TestBuildGraph:
    """Tests para build_graph."""
    
    def test_build_graph_basic(self):
        """Verificar que build_graph construye un grafo."""
        random.seed(42)
        G, nodes = build_graph(n=6)
        
        assert isinstance(G, nx.Graph)
        assert isinstance(nodes, dict)
        assert len(nodes) == 6
    
    def test_build_graph_node_count(self):
        """Verificar que se crean n nodos."""
        random.seed(42)
        
        for n in [3, 6, 10]:
            G, nodes = build_graph(n=n)
            assert len(nodes) == n
            assert G.number_of_nodes() == n
    
    def test_build_graph_nodes_are_node_objects(self):
        """Verificar que los nodos son instancias de Node."""
        random.seed(42)
        G, nodes = build_graph(n=5)
        
        for name, node in nodes.items():
            assert isinstance(node, Node)
            assert node.name == name
    
    def test_build_graph_capacity_range(self):
        """Verificar que capacidades están en rango [80, 120]."""
        random.seed(42)
        G, nodes = build_graph(n=10)
        
        for node in nodes.values():
            assert 80 <= node.capacity <= 120
    
    def test_build_graph_load_valid(self):
        """Verificar que load está entre 40 y capacity."""
        random.seed(42)
        G, nodes = build_graph(n=10)
        
        for node in nodes.values():
            assert 40 <= node.load <= node.capacity
    
    def test_build_graph_has_edges(self):
        """Verificar que el grafo tiene aristas."""
        random.seed(42)
        G, nodes = build_graph(n=6)
        
        # Debe haber al menos n+2 aristas según código
        assert G.number_of_edges() >= 6  # Puede variar por random.sample
    
    def test_build_graph_edge_attributes(self):
        """Verificar que aristas tienen atributo friction."""
        random.seed(42)
        G, nodes = build_graph(n=5)
        
        for u, v, data in G.edges(data=True):
            assert 'friction' in data
            assert 0.1 <= data['friction'] <= 0.5
    
    def test_build_graph_reproducibility(self):
        """Verificar que con misma seed produce mismo grafo."""
        rng1 = random.Random(42)
        G1, nodes1 = build_graph(n=6, rng=rng1)
        
        rng2 = random.Random(42)
        G2, nodes2 = build_graph(n=6, rng=rng2)
        
        # Mismo número de nodos y aristas
        assert G1.number_of_nodes() == G2.number_of_nodes()
        assert G1.number_of_edges() == G2.number_of_edges()
        
        # Mismas capacidades y cargas
        for name in nodes1.keys():
            assert nodes1[name].capacity == nodes2[name].capacity
            assert nodes1[name].load == nodes2[name].load
    
    def test_build_graph_different_sizes(self):
        """Verificar que diferentes tamaños producen grafos diferentes."""
        rng = random.Random(42)
        G_small, _ = build_graph(n=3, rng=rng)
        
        rng = random.Random(42)
        G_large, _ = build_graph(n=12, rng=rng)
        
        assert G_small.number_of_nodes() < G_large.number_of_nodes()


class TestComputeMetrics:
    """Tests para compute_metrics."""
    
    def test_compute_metrics_basic(self):
        """Verificar que compute_metrics retorna 3 valores numéricos."""
        random.seed(42)
        G, nodes = build_graph(n=6)
        H, H_eff, S = compute_metrics(G, nodes)
        
        assert isinstance(H, (int, float))
        assert isinstance(H_eff, (int, float))
        assert isinstance(S, (int, float))
    
    def test_compute_metrics_h_is_sum_of_slacks(self):
        """Verificar que H es la suma de todos los slacks."""
        random.seed(42)
        G, nodes = build_graph(n=5)
        H, _, _ = compute_metrics(G, nodes)
        
        expected_H = sum(node.slack for node in nodes.values())
        assert abs(H - expected_H) < 0.01  # Tolerancia numérica
    
    def test_compute_metrics_h_eff_le_h(self):
        """Verificar que H_eff <= H siempre."""
        random.seed(42)
        
        for n in [3, 6, 10]:
            G, nodes = build_graph(n=n)
            H, H_eff, _ = compute_metrics(G, nodes)
            
            assert H_eff <= H, f"H_eff ({H_eff}) debe ser <= H ({H})"
    
    def test_compute_metrics_empty_graph(self):
        """Verificar comportamiento con grafo vacío."""
        G = nx.Graph()
        nodes = {}
        
        H, H_eff, S = compute_metrics(G, nodes)
        
        assert H == 0.0
        assert H_eff == 0.0
        # S puede ser problemático con lista vacía, pero debería manejarse
    
    def test_compute_metrics_single_node_no_edges(self):
        """Verificar métricas con un solo nodo sin conexiones."""
        G = nx.Graph()
        node = Node("N0", 100.0, 50.0)
        nodes = {"N0": node}
        G.add_node("N0", slack=node.slack)
        
        H, H_eff, S = compute_metrics(G, nodes)
        
        assert H == 50.0  # slack de 50
        assert H_eff == 0.0  # Sin conexiones, grado = 0, H_eff = 0
        assert S >= 0.0
    
    def test_compute_metrics_fully_connected_vs_disconnected(self):
        """Comparar H_eff entre grafo conectado y desconectado."""
        # Grafo conectado (todos tienen conexiones)
        random.seed(42)
        G_connected, nodes_connected = build_graph(n=6)
        _, H_eff_connected, _ = compute_metrics(G_connected, nodes_connected)
        
        # Grafo desconectado (nodos aislados)
        G_disconnected = nx.Graph()
        nodes_disconnected = {}
        for i in range(6):
            node = Node(f"N{i}", 100.0, 50.0)
            nodes_disconnected[f"N{i}"] = node
            G_disconnected.add_node(f"N{i}", slack=node.slack)
        
        _, H_eff_disconnected, _ = compute_metrics(G_disconnected, nodes_disconnected)
        
        # Conectado debe tener mayor H_eff
        assert H_eff_connected > H_eff_disconnected
        assert H_eff_disconnected == 0.0  # Sin conexiones
    
    def test_compute_metrics_entropy_calculation(self):
        """Verificar que entropía S se calcula correctamente."""
        # Crear grafo con nodos balanceados (mismo load/capacity)
        G_balanced = nx.Graph()
        nodes_balanced = {}
        for i in range(5):
            node = Node(f"N{i}", 100.0, 50.0)  # Todos 50% utilizados
            nodes_balanced[f"N{i}"] = node
            G_balanced.add_node(f"N{i}", slack=node.slack)
        
        _, _, S_balanced = compute_metrics(G_balanced, nodes_balanced)
        
        # Entropía debe ser 0 (o muy baja) con utilización uniforme
        assert S_balanced < 0.01
        
        # Crear grafo con nodos desbalanceados
        G_unbalanced = nx.Graph()
        nodes_unbalanced = {
            "N0": Node("N0", 100.0, 10.0),  # 10% usado
            "N1": Node("N1", 100.0, 90.0),  # 90% usado
        }
        for name, node in nodes_unbalanced.items():
            G_unbalanced.add_node(name, slack=node.slack)
        
        _, _, S_unbalanced = compute_metrics(G_unbalanced, nodes_unbalanced)
        
        # Entropía debe ser mayor con desbalance
        assert S_unbalanced > S_balanced
    
    def test_compute_metrics_accessibility_factor(self):
        """Verificar que accesibilidad (grado) afecta H_eff."""
        # Nodo con alto grado (bien conectado)
        G_high_degree = nx.Graph()
        node = Node("N0", 100.0, 50.0)
        nodes_high = {"N0": node}
        G_high_degree.add_node("N0", slack=node.slack)
        
        # Conectar a varios nodos sin slack para que solo N0 contribuya
        for i in range(1, 6):
            G_high_degree.add_node(f"N{i}", slack=0)
            G_high_degree.add_edge("N0", f"N{i}")
        
        _, H_eff_high, _ = compute_metrics(G_high_degree, nodes_high)
        
        # Nodo con bajo grado (mal conectado)
        G_low_degree = nx.Graph()
        node2 = Node("N0", 100.0, 50.0)
        nodes_low = {"N0": node2}
        G_low_degree.add_node("N0", slack=node2.slack)
        G_low_degree.add_node("N1", slack=0)
        G_low_degree.add_edge("N0", "N1")  # Solo 1 conexión
        
        _, H_eff_low, _ = compute_metrics(G_low_degree, nodes_low)
        
        # Mayor grado → mayor H_eff (o al menos >=)
        assert H_eff_high >= H_eff_low
    
    def test_compute_metrics_all_non_negative(self):
        """Verificar que todas las métricas son no negativas."""
        random.seed(42)
        
        for _ in range(10):  # Probar varios grafos aleatorios
            G, nodes = build_graph(n=random.randint(3, 10))
            H, H_eff, S = compute_metrics(G, nodes)
            
            assert H >= 0, f"H negativo: {H}"
            assert H_eff >= 0, f"H_eff negativo: {H_eff}"
            assert S >= 0, f"S negativo: {S}"


class TestIntegration:
    """Tests de integración."""
    
    def test_full_workflow(self):
        """Test de flujo completo: construir grafo y calcular métricas."""
        random.seed(42)
        G, nodes = build_graph(n=8)
        H, H_eff, S = compute_metrics(G, nodes)
        
        # Verificar consistencia
        assert G.number_of_nodes() == 8
        assert len(nodes) == 8
        assert H > 0
        assert H_eff > 0
        assert S >= 0
        assert H_eff <= H
    
    def test_state_detection(self):
        """Verificar detección de estados del sistema."""
        random.seed(42)
        G, nodes = build_graph(n=6)
        H, H_eff, S = compute_metrics(G, nodes)
        
        # Determinar estado
        if H_eff > 0:
            state = "VIVO"
        elif H > 0:
            state = "ZOMBI"
        else:
            state = "COLAPSADO"
        
        # En un grafo recién construido, debería estar VIVO
        assert state == "VIVO"
        assert H > 0
        assert H_eff > 0
    
    def test_reproducibility_full_pipeline(self):
        """Verificar reproducibilidad completa del pipeline."""
        rng1 = random.Random(123)
        G1, nodes1 = build_graph(n=7, rng=rng1)
        H1, H_eff1, S1 = compute_metrics(G1, nodes1)
        
        rng2 = random.Random(123)
        G2, nodes2 = build_graph(n=7, rng=rng2)
        H2, H_eff2, S2 = compute_metrics(G2, nodes2)
        
        assert abs(H1 - H2) < 0.01
        assert abs(H_eff1 - H_eff2) < 0.01
        assert abs(S1 - S2) < 0.01


# Fixtures
@pytest.fixture
def sample_graph():
    """Fixture con grafo de ejemplo."""
    random.seed(42)
    return build_graph(n=6)


@pytest.fixture
def balanced_nodes():
    """Fixture con nodos perfectamente balanceados."""
    nodes = {}
    for i in range(5):
        nodes[f"N{i}"] = Node(f"N{i}", 100.0, 50.0)
    return nodes


def test_with_sample_graph_fixture(sample_graph):
    """Test usando fixture de grafo de ejemplo."""
    G, nodes = sample_graph
    H, H_eff, S = compute_metrics(G, nodes)
    
    assert H > 0
    assert H_eff > 0
    assert H_eff <= H


def test_with_balanced_nodes_fixture(balanced_nodes):
    """Test usando fixture de nodos balanceados."""
    # Todos los nodos tienen misma utilización
    utilizations = [n.load / n.capacity for n in balanced_nodes.values()]
    
    assert all(u == 0.5 for u in utilizations)
    
    # Entropía debe ser cercana a 0
    mean = sum(utilizations) / len(utilizations)
    variance = sum((u - mean) ** 2 for u in utilizations) / len(utilizations)
    assert variance < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
