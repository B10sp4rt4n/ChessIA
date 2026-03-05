# compare_v42_app.py
# Interfaz Streamlit para Comparador Estructural v4.2

import streamlit as st
from compare_v42 import (
    Scenario,
    ALPHA_H_EFF_MIN,
    ALPHA_DECAY_MAX,
    BETA_H_EFF_MIN
)
from compare_v42_ui_bridge import compare_from_ui
from explanations import obtener_explicacion_con_fuente
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

st.divider()
st.subheader("🌐 Escenario D — Demo Servicios Web")
st.caption(
    "Escenario orientado a audiencia web/académica. "
    "'Capacidad disponible' equivale a H_eff; "
    "'Degradación por ciclo de carga' equivale a decay."
)

col_d1, col_d2, col_d3 = st.columns([2, 2, 2])
with col_d1:
    d_name = st.text_input(
        "Nombre del sistema",
        value="Portal Inscripciones DGAE (pico enero)",
        key="d_name",
        help="Nombre del servicio o sistema web a analizar"
    )
with col_d2:
    d_h_eff = st.number_input(
        "Capacidad disponible del sistema (0–100)",
        value=22.0,
        min_value=0.1,
        max_value=100.0,
        step=1.0,
        key="d_h",
        help="Margen libre antes de saturación: CPU idle %, ms libres antes de timeout, requests/seg absorbibles"
    )
with col_d3:
    d_decay = st.number_input(
        "Degradación por ciclo de carga",
        value=6.1,
        min_value=0.1,
        max_value=20.0,
        step=0.1,
        key="d_d",
        help="Cuánto se deteriora la respuesta por cada ciclo de carga adicional (ej. cada 100 usuarios concurrentes)"
    )

use_scenario_d = st.checkbox("Incluir Escenario D en la comparación", value=True)

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

        # Agregar Escenario D si está habilitado
        if use_scenario_d:
            try:
                scenarios.append(Scenario(d_name, d_h_eff, d_decay))
            except Exception as e:
                st.warning(f"Error en Escenario D ({d_name}): {e}")
        
        # Agregar personalizados
        for name, h_eff, decay in custom_scenarios:
            try:
                scenarios.append(Scenario(name, h_eff, decay))
            except Exception as e:
                st.warning(f"Error en {name}: {e}")
        
        # Ejecutar comparación
        ranking = compare_from_ui(
            scenarios=scenarios,
            alpha_h=alpha_h,
            alpha_decay=alpha_decay,
            beta_h=beta_h,
            sim_steps=sim_steps,
        )
        
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
        ranking_item = next((r for r in ranking if r["name"] == selected_scenario), None)
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

        if ranking_item is not None:
            st.divider()
            st.subheader("🧠 Explicación del escenario")

            oyente_type = st.radio(
                "Selecciona el tipo de oyente:",
                ["técnico", "no técnico", "gerencial", "usuario final"],
                horizontal=True,
            )

            explanation_scenario = {
                "name": ranking_item["name"],
                "H_eff": ranking_item["H_eff"],
                "decay": ranking_item["dH_eff_dt"],
            }

            # Nota contextual para el Escenario D
            if ranking_item["name"] == d_name and use_scenario_d:
                st.info(
                    f"📌 **Lectura web:** "
                    f"Capacidad disponible = {ranking_item['H_eff']:.0f}/100 · "
                    f"Degradación por ciclo = {ranking_item['dH_eff_dt']:.1f} pts/ciclo"
                )

            try:
                explicacion, fuente = obtener_explicacion_con_fuente(
                    scenario=explanation_scenario,
                    classification=ranking_item["class"],
                    oyente_type=oyente_type,
                )
                if fuente == "IA":
                    st.caption("Fuente de explicación: IA")
                else:
                    st.caption("Fuente de explicación: Local (fallback)")
                st.text_area("Explicación", value=explicacion, height=180)
            except ValueError as e:
                st.error(f"Entrada inválida para explicación: {e}")

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
