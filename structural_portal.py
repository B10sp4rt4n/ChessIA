import time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FixCel Structural Portal", page_icon="🧩", layout="wide")

STEPS = ["Solicitud", "Validar", "Inventario", "Pago", "Confirmar", "Factura"]
DATA = {
    "Operación normal": [(120,8,98,94,82),(135,10,98,93,80),(142,12,97,92,76),(155,14,97,91,72),(148,10,98,93,78),(130,6,99,95,86)],
    "Latencia creciente": [(120,8,98,94,82),(160,12,97,92,75),(250,18,95,88,62),(820,37,78,63,24),(1450,61,61,42,8),(2200,84,39,21,2)],
    "Desborde de cola": [(110,12,98,95,84),(130,22,97,92,71),(155,39,94,84,55),(220,58,88,70,34),(410,79,70,48,14),(760,96,44,18,3)],
    "Deriva estructural": [(120,8,98,94,82),(125,9,94,91,76),(140,11,89,86,64),(150,13,77,73,44),(160,15,64,56,21),(170,17,48,38,9)],
}

def classify(d):
    lat,q,match,she,edge=d
    if edge<=5 or she<25 or q>90: return "DESBORDE", "La sesión salió del corredor estructural."
    if edge<=20 or she<50: return "CRÍTICO", "Pérdida fuerte de confinamiento estructural."
    if edge<=40 or she<70: return "PRE-DESBORDE", "Trayectoria aproximándose al borde histórico."
    if match<85: return "DERIVA", "La trama dejó de coincidir plenamente con el patrón."
    return "NORMAL", "Trayectoria dentro del corredor histórico."

st.sidebar.title("FixCel 2.0")
st.sidebar.caption("Structural Conformance Portal")
section=st.sidebar.radio("Portal", ["Resumen","Patrones","Sesiones","Memoria estructural","Hallazgos","Simulador"])
st.sidebar.divider()
st.sidebar.selectbox("Tenant", ["SynAppsSys Lab","Cliente Demo A","Cliente Demo B"])
st.sidebar.caption("Motor: FixCel + UPL + SHE")

st.title("FixCel Structural Portal")
st.caption("Patrón · Registro · Memoria · Conformidad · Estabilidad")

if section=="Resumen":
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Salud estructural","91%","Estable")
    c2.metric("Patrones reconocidos","12","3 activos")
    c3.metric("Sesiones","248","24 h")
    c4.metric("Rupturas","7","2 críticas")
    st.subheader("Mapa de conformidad")
    st.write("**P-001:** A → B → C → D → E → F")
    chart=pd.DataFrame({"Centro memoria":[62,66,72,78,73,76],"Sesión actual":[62,66,72,78,70,61]},index=STEPS)
    st.line_chart(chart)
    st.info("La sesión permanece conforme, pero se separa del centro de memoria en Pago → Confirmar.")
    st.subheader("Hallazgos recientes")
    st.dataframe(pd.DataFrame([
        ["F-104","Deriva temporal","Media","Pago tarda 34% más que la memoria nominal"],
        ["F-103","Borde de cola","Alta","Tres sesiones consecutivas tocaron borde"],
        ["F-101","Conformidad parcial","Baja","Subtrama reconocida con 87% de encaje"],
    ],columns=["ID","Hallazgo","Severidad","Detalle"]),use_container_width=True,hide_index=True)

elif section=="Patrones":
    st.subheader("Biblioteca de patrones")
    st.dataframe(pd.DataFrame([
        ["P-001","Pedido Web","A → B → C → D → E → F",248,"96%"],
        ["P-002","Alta Tenant","Identidad → Admin → Política → Evidencia",61,"93%"],
        ["P-003","Ingesta Evento","Fuente → Normaliza → Custodia → Índice",34,"89%"],
    ],columns=["Patrón","Nombre","Trama","Sesiones","Match medio"]),use_container_width=True,hide_index=True)
    st.code('{"pattern_id":"P-001","entry":"A","exit":"F","memory_profile":"MEM-P001","tolerance_model":"corridor-v1"}',language="json")

elif section=="Sesiones":
    st.subheader("Registro de sesiones")
    st.dataframe(pd.DataFrame([
        ["SIM-248","P-001","96%","91%","Normal"],
        ["SIM-247","P-001","81%","63%","Pre-desborde"],
        ["SIM-246","P-002","93%","88%","Normal"],
        ["SIM-245","P-003","69%","41%","Crítico"],
    ],columns=["Sesión","Patrón","Match","SHE","Estado"]),use_container_width=True,hide_index=True)

elif section=="Memoria estructural":
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Muestras","248"); c2.metric("Centro","0.92"); c3.metric("Variación","±0.08"); c4.metric("Deriva","+4.7%")
    st.subheader("Corredor histórico")
    df=pd.DataFrame({"Borde superior":[80,84,88,92,90,91],"Centro":[62,66,72,78,73,76],"Borde inferior":[44,48,56,64,56,61],"Actual":[62,66,72,78,70,61]},index=STEPS)
    st.line_chart(df)
    st.caption("La memoria no es otro log: es la forma derivada de múltiples recorridos comparables.")

elif section=="Hallazgos":
    st.subheader("F-104 · Deriva temporal")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Esperado","610 ms"); c2.metric("Actual","817 ms"); c3.metric("Desviación","34%"); c4.metric("Confianza","0.91")
    st.warning("La transición D → E sigue siendo válida en el patrón, pero se separa de la memoria histórica.")

else:
    st.subheader("Structural Tape Simulator")
    scenario=st.selectbox("Escenario",list(DATA.keys()))
    if "frame" not in st.session_state: st.session_state.frame=0
    a,b,c,d=st.columns(4)
    if a.button("◀ Atrás",use_container_width=True): st.session_state.frame=max(0,st.session_state.frame-1)
    if b.button("Siguiente ▶",use_container_width=True): st.session_state.frame=min(5,st.session_state.frame+1)
    if c.button("Reiniciar",use_container_width=True): st.session_state.frame=0
    autoplay=d.button("▶ Reproducir",use_container_width=True)
    if autoplay:
        for i in range(st.session_state.frame,6):
            st.session_state.frame=i
            time.sleep(.35)
            st.rerun()
    f=st.session_state.frame
    lat,q,match,she,edge=DATA[scenario][f]
    state,msg=classify(DATA[scenario][f])
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Frame",f"{f+1:03}"); c2.metric("FixCel",f"{match}%"); c3.metric("SHE",f"{she}%"); c4.metric("Borde",f"{edge}%")
    st.write("**Patrón:** A → B → C → D → E → F")
    st.write("**Registro:** "+" → ".join(chr(65+i) for i in range(f+1)))
    st.progress(match/100,text=f"Conformidad FixCel · {match}%")
    st.progress(she/100,text=f"Estabilidad SHE · {she}%")
    st.progress(max(0,min(1,(100-edge)/100)),text=f"Proximidad al borde · {100-edge}%")
    hist=[62,66,72,78,73,76]
    drift=[0,0,0,10,22,35] if scenario!="Operación normal" else [0]*6
    current=[hist[i]-drift[i] if i<=f else None for i in range(6)]
    st.line_chart(pd.DataFrame({"Centro memoria":hist,"Recorrido actual":current},index=STEPS))
    st.info(f"{state} — {msg}")
    st.json({"session":"SIM-001","frame":f+1,"pattern":"P-001","step":chr(65+f),"latency_ms":lat,"queue_pct":q,"pattern_match":match/100,"she_stability":she/100,"distance_to_edge":edge/100,"state":state,"memory_ref":"MEM-P001","evidence_ref":f"EV-{f+1:04}"})
