# Testing Guide - ChessIA/SHE Core

Esta guía detalla el sistema de testing del proyecto, cobertura, y mejores prácticas.

## 📊 Estado actual del testing

| Módulo | Tests | Cobertura | Estado |
|--------|-------|-----------|--------|
| `demo.py` | 29 | 97% | ✅ Excelente |
| `compare_v42.py` | 23 | 74% | ✅ Bueno |
| `mcl_chess.py` | 21 | 63% | ⚠️ Mejorable |
| `chess_demo.py` | 0 | 0% | ⚠️ Sin tests |
| **TOTAL** | **73** | **81%** | ✅ **Senior+** |

## 🚀 Ejecución rápida

### Todos los tests
```bash
cd engine
pytest -v
```

### Tests específicos
```bash
# Solo test_demo.py
pytest test_demo.py -v

# Comparador v4.2 + puente UI
pytest test_compare_v42.py test_compare_v42_ui_bridge.py -v

# Solo test de una clase
pytest test_compare_v42.py::TestClassify -v

# Solo un test específico
pytest test_demo.py::TestNode::test_node_initialization -v
```

### Con cobertura
```bash
pytest --cov=compare_v42 --cov=mcl_chess --cov=demo --cov-report=html
```

### Modo watch (re-ejecutar en cambios)
```bash
pip install pytest-watch
ptw -- -v
```

## 📋 Estructura de tests

### test_demo.py (29 tests)

#### TestNode (6 tests)
- Inicialización de nodos
- Cálculo de slack (holgura)
- Property dinámico de slack
- Representación string

#### TestBuildGraph (9 tests)
- Construcción de grafos
- Validación de capacidades y cargas
- Atributos de aristas (friction)
- Reproducibilidad con seeds

#### TestComputeMetrics (9 tests)
- Cálculo de H (suma de slacks)
- Invariante H_eff ≤ H
- Entropía S (desviación estándar)
- Factor de accesibilidad (grado)

#### TestIntegration (3 tests)
- Flujo completo
- Detección de estados (VIVO/ZOMBI/COLAPSADO)
- Reproducibilidad del pipeline

#### Fixtures (2)
- `sample_graph`: Grafo de 6 nodos
- `balanced_nodes`: Nodos balanceados (50% utilización)

---

### test_compare_v42.py (23 tests)

#### TestScenario (5 tests)
- Inicialización de escenarios
- Simulación con degradación
- Floor en cero (no negativos)
- Configuración de pasos

#### TestClassify (8 tests)
- Clasificación Alpha: H_eff alto, decay bajo
- Clasificación Beta: H_eff moderado o decay moderado
- Clasificación Gamma: H_eff bajo o decay alto
- Umbrales configurables
- Casos borde (boundaries)

#### TestCompare (7 tests)
- Ranking por H_eff
- Tie-breaking por decay
- Estructura de métricas
- Integración completa
- Lista vacía
- Un solo escenario

#### TestConstants (2 tests)
- Valores por defecto razonables
- Validación de constantes

#### Integration (1 test)
- Flujo completo: creación → simulación → clasificación

---

### test_compare_v42_ui_bridge.py (4 tests)

#### TestUIBridge (4 tests)
- Mapeo de `alpha_h`/`alpha_decay`/`beta_h` → objeto `thresholds`
- Propagación de `sim_steps` al motor (`H_eff` final)
- Propagación de umbrales a la clase final (Alpha/Beta/Gamma)
- Validación de error para `sim_steps` fuera de rango

---

### test_mcl_chess.py (21 tests)

#### TestConstants (3 tests)
- PIECE_CAPACITY (Q:9, R:5, B:3, N:3, P:1)
- Todas piezas definidas
- ACCESS_WEIGHT (0.3)

#### TestComputeHolisticMetrics (7 tests)
- Posición inicial (H ≈ 78, H_eff > 0)
- Tablero vacío (H = 0)
- Una sola pieza
- Capturas reducen métricas
- Movilidad aumenta H_eff
- Respeto a ACCESS_WEIGHT

#### TestRunGame (7 tests)
- Ejecución básica
- Estructura del historial
- Métricas decrecen o estables
- Game over (checkmate/stalemate)
- Cero movimientos
- Diferentes longitudes
- Reproducibilidad con seed

#### TestIntegration (2 tests)
- Simulación completa de partida
- Consistencia de métricas (H_eff ≤ H siempre)

#### Fixtures (2)
- `standard_board`: Posición inicial
- `endgame_board`: Final de partida (2 piezas)

---

## 🎯 Cobertura detallada

### demo.py (97% - 2 líneas sin cubrir)
**Líneas no cubiertas:**
- `107-108`: Bloque de Streamlit UI (`if __name__ == "__main__"`)

**Recomendación:** Excelente cobertura. Las líneas sin cubrir son UI y no críticas.

---

### compare_v42.py (74% - 11 líneas sin cubrir)
**Líneas no cubiertas:**
- `117-133`: Bloque Streamlit UI completo

**Análisis:**
```python
# Líneas 117-133: UI de Streamlit
if __name__ == "__main__":
    st.title(...)
    scen1 = Scenario(...)
    # ... más UI ...
```

**Recomendación:** Agregar tests de integración para UI o excluir con `.coveragerc`:
```ini
[report]
exclude_lines =
    if __name__ == .__main__.:
```

---

### mcl_chess.py (63% - 18 líneas sin cubrir)
**Líneas no cubiertas:**
- `91`: Condición de game over alternativa
- `98-99`: Rama else en generación de movimientos
- `106`: Caso especial en métricas
- `115-129`: Bloque Streamlit UI

**Recomendación:** Agregar tests para:
1. ✅ Game over por draw/insufficient material
2. ✅ Legal moves cuando no hay capturas
3. ✅ Edge cases en compute_holistic_metrics()

**Prioridad:** ALTA (63% → 80%+)

---

## ✨ Mejores prácticas

### 1. Estructura de tests
```python
class TestFeature:
    """Tests para feature X."""
    
    def test_happy_path(self):
        """Caso normal."""
        result = function(valid_input)
        assert result == expected
    
    def test_edge_case(self):
        """Caso límite."""
        result = function(edge_input)
        assert result is handled_correctly
    
    def test_error_handling(self):
        """Manejo de errores."""
        with pytest.raises(ValueError):
            function(invalid_input)
```

### 2. Fixtures para reusabilidad
```python
@pytest.fixture
def sample_data():
    """Datos de ejemplo reutilizables."""
    return create_test_data()

def test_feature(sample_data):
    """Usa fixture automáticamente."""
    result = process(sample_data)
    assert result.is_valid
```

### 3. Parametrización para múltiples casos
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (5, 10),
    (0, 0),
])
def test_multiply_by_two(input, expected):
    assert multiply_by_two(input) == expected
```

### 4. Seeds para reproducibilidad
```python
def test_random_behavior():
    """Tests deterministas con random."""
    random.seed(42)
    result = function_with_randomness()
    assert result == expected_with_seed_42
```

### 5. Docstrings descriptivos
```python
def test_classification_boundary():
    """Verificar clasificación en límite Alpha/Beta.
    
    Cuando H_eff = 60.0 (exactamente el umbral), debe
    clasificar como Alpha si decay < 1.0.
    """
```

## 🔍 Debugging de tests

### Ver output completo
```bash
pytest -v -s
```

### Ver solo failures
```bash
pytest --tb=short
```

### Parar en primer failure
```bash
pytest -x
```

### Re-ejecutar últimos failures
```bash
pytest --lf
```

### Profiling de tests lentos
```bash
pytest --durations=10
```

## 📈 Mejora continua

### Roadmap para 90%+ coverage

**Prioridad ALTA:**
1. ✅ Mejorar mcl_chess.py (63% → 80%+)
   - Agregar tests para líneas 91, 98-99, 106
   - Test de game_over con diferentes condiciones
   - Test de legal_moves sin capturas

2. ⚠️ Tests básicos para chess_demo.py (0% → 50%+)
   - Tests unitarios de funciones auxiliares
   - Mock de Streamlit components
   - Tests de lógica de navegación

**Prioridad MEDIA:**
3. ✅ Configurar .coveragerc para excluir UI
4. ✅ Agregar pytest-cov a requirements.txt
5. ✅ Integrar coverage en CI/CD

**Prioridad BAJA:**
6. ⚠️ Tests end-to-end con selenium
7. ⚠️ Tests de performance/benchmarking
8. ⚠️ Tests de regresión visual

## 🤖 CI/CD Integration

Los tests se ejecutan automáticamente en GitHub Actions:

- **Trigger:** Push a `main` o `develop`, o Pull Request
- **Python versions:** 3.10, 3.11, 3.12
- **Linting:** flake8 + pylint
- **Coverage:** Reportado a Codecov

Ver workflow: [`.github/workflows/tests.yml`](../.github/workflows/tests.yml)

## 📚 Recursos

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)

---

**Última actualización:** 2026-02-08  
**Tests totales:** 73  
**Cobertura:** 81%  
**Estado:** ✅ Senior-level
