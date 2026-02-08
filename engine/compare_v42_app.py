# compare_v42_app.py
# Interfaz Streamlit para Comparador Estructural v4.2

import streamlit as st
from compare_v42 import (
    Scenario,
    compare,
    ALPHA_H_EFF_MIN,
    ALPHA_DECAY_MAX,
    BETA_H_EFF_MIN
)
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="SHE Comparador v4.2", layout="wide")

st.title("Structural Health Engine · Comparador v4.2")
st.caption("Clasificación y ranking estructural de escenarios")

st.info(
    """
    **Comparador v4.2** clasifica escenarios según su salud estructural:
    - **Alpha**: Alta holgura efectiva + baja degradación
    - **Beta**: Holgura moderada
    - **Gamma**: Holgura baja o degradación rápida
    """
)

# -----------------------------
# Sidebar: Configuración de umbrales
# -----------------------------
st.sidebar.header("Umbrales de Clasificación")

alpha_h = st.sidebar.number_input(
    "Alpha: H_eff mínimo",
    min_value=0.0,
    max_value=200.0,
    value=ALPHA_H_EFF_MIN,
    step=5.0,
    help="Holgura efectiva mínima para clasificar como Alpha"
)

alpha_decay = st.sidebar.number_input(
    "Alpha: Decay máximo",
    min_value=0.0,
    max_value=10.0,
    value=ALPHA_DECAY_MAX,
    step=0.1,
    help="Máxima tasa de degradación para clasificar como Alpha"
)

beta_h = st.sidebar.number_input(
    "Beta: H_eff mínimo",
    min_value=0.0,
    max_value=200.0,
    value=BETA_H_EFF_MIN,
    step=5.0,
    help="Holgura efectiva mínima para clasificar como Beta"
)

st.sidebar.divider()
st.sidebar.header("Simulación")
sim_steps = st.sidebar.slider(
    "Pasos de simulación",
    min_value=5,
    max_value=100,
    value=10,
    step=5,
    help="Número de pasos temporales para simular degradación"
)

# -----------------------------
# Escenarios predefinidos
# -----------------------------
st.subheader("Escenarios Predefinidos")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### Escenario A")
    a_h_eff = st.number_input("H_eff inicial A", value=72.4, step=1.0, key="a_h")
    a_decay = st.number_input("Decay A", value=0.8, step=0.1, key="a_d")

with col2:
    st.markdown("##### Escenario B")
    b_h_eff = st.number_input("H_eff inicial B", value=51.6, step=1.0, key="b_h")
    b_decay = st.number_input("Decay B", value=2.1, step=0.1, key="b_d")

with col3:
    st.markdown("##### Escenario C")
    c_h_eff = st.number_input("H_eff inicial C", value=28.9, step=1.0, key="c_h")
    c_decay = st.number_input("Decay C", value=4.5, step=0.1, key="c_d")

# -----------------------------
# Escenarios personalizados
# -----------------------------
st.divider()
st.subheader("Escenarios Personalizados (Opcional)")

use_custom = st.checkbox("Agregar escenarios personalizados")

custom_scenarios = []
if use_custom:
    num_custom = st.number_input("Número de escenarios", min_value=1, max_value=5, value=1, step=1)
    
    for i in range(num_custom):
        col_name, col_h, col_d = st.columns([2, 2, 2])
        with col_name:
            name = st.text_input(f"Nombre {i+1}", value=f"Custom {i+1}", key=f"custom_name_{i}")
        with col_h:
            h_eff = st.number_input(f"H_eff {i+1}", value=50.0, step=1.0, key=f"custom_h_{i}")
        with col_d:
            decay = st.number_input(f"Decay {i+1}", value=2.0, step=0.1, key=f"custom_d_{i}")
        
        custom_scenarios.append((name, h_eff, decay))

# -----------------------------
# Ejecutar comparación
# -----------------------------
st.divider()

if st.button("🔍 Comparar Escenarios", type="primary"):
    try:
        # Crear escenarios
        scenarios = [
            Scenario("Escenario A", a_h_eff, a_decay),
            Scenario("Escenario B", b_h_eff, b_decay),
            Scenario("Escenario C", c_h_eff, c_decay),
        ]
        
        # Agregar personalizados
        for name, h_eff, decay in custom_scenarios:
            try:
                scenarios.append(Scenario(name, h_eff, decay))
            except Exception as e:
                st.warning(f"Error en {name}: {e}")
        
        # Ejecutar comparación
        ranking = compare(scenarios, alpha_h, alpha_decay, beta_h)
        
        st.session_state['ranking'] = ranking
        st.session_state['scenarios'] = scenarios
        st.session_state['sim_steps'] = sim_steps
        st.success(f"✅ Comparación completada ({len(ranking)} escenarios)")
        
    except Exception as e:
        st.error(f"Error en comparación: {e}")
        logger.error(f"Error en comparación: {e}", exc_info=True)

# -----------------------------
# Mostrar resultados
# -----------------------------
if 'ranking' in st.session_state:
    ranking = st.session_state['ranking']
    scenarios_dict = {s.name: s for s in st.session_state['scenarios']}
    
    st.divider()
    st.subheader("📊 Ranking Estructural")
    
    # Tabla de resultados
    st.write("**Clasificación ordenada por salud estructural:**")
    
    for i, r in enumerate(ranking, 1):
        class_emoji = {
            "Alpha": "🟢",
            "Beta": "🟡",
            "Gamma": "🔴"
        }
        
        cols = st.columns([0.5, 2, 1.5, 1.5, 1])
        with cols[0]:
            st.markdown(f"**{i}.**")
        with cols[1]:
            st.markdown(f"**{r['name']}**")
        with cols[2]:
            st.metric("H_eff", f"{r['H_eff']:.1f}")
        with cols[3]:
            st.metric("dH/dt", f"{r['dH_eff_dt']:.2f}")
        with cols[4]:
            st.markdown(f"{class_emoji.get(r['class'], '⚪')} **{r['class']}**")
    
    # Visualización de evolución temporal
    st.divider()
    st.subheader("📈 Evolución Temporal")
    
    selected_scenario = st.selectbox(
        "Selecciona un escenario para ver su simulación:",
        [r['name'] for r in ranking]
    )
    
    if selected_scenario in scenarios_dict:
        scenario = scenarios_dict[selected_scenario]
        sim_steps_display = st.session_state.get('sim_steps', 10)
        
        try:
            series = scenario.simulate(sim_steps_display)
            
            st.line_chart(
                data={"H_eff": series},
                height=400
            )
            
            st.caption(f"Evolución de H_eff para {selected_scenario} ({sim_steps_display} pasos)")
            
            # Métricas adicionales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("H_eff inicial", f"{series[0]:.1f}")
            with col2:
                st.metric("H_eff final", f"{series[-1]:.1f}")
            with col3:
                total_decay = series[0] - series[-1]
                st.metric("Decay total", f"{total_decay:.1f}")
            with col4:
                avg_decay = total_decay / len(series) if len(series) > 0 else 0
                st.metric("Decay promedio", f"{avg_decay:.2f}/paso")
                
        except Exception as e:
            st.error(f"Error simulando {selected_scenario}: {e}")
            logger.error(f"Error en simulación: {e}", exc_info=True)

# -----------------------------
# Información adicional
# -----------------------------
st.divider()
st.subheader("ℹ️ Criterios de Clasificación")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🟢 Alpha**
    - H_eff > {:.1f}
    - dH/dt < {:.1f}
    - Sistemas resilientes
    """.format(alpha_h, alpha_decay))

with col2:
    st.markdown("""
    **🟡 Beta**
    - H_eff > {:.1f}
    - Degradación moderada
    - Requiere monitoreo
    """.format(beta_h))

with col3:
    st.markdown("""
    **🔴 Gamma**
    - H_eff bajo
    - Degradación rápida
    - Riesgo de colapso
    """)

st.markdown("""
---
**Nota:** Los umbrales son configurables en el sidebar y dependen del contexto específico del sistema.
El modelo de degradación usado es lineal simplificado para fines demostrativos.
""")
