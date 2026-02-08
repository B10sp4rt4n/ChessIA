# SHE Core (Web) + Engine Demos

Este repo esta listo para GitHub.

## Aviso de propiedad intelectual
Este material es propiedad intelectual privada.
No es copiable, no es patentable, y no es reproducible por terceros sin
autorizacion expresa.

## Que incluye
- `she-core/web/`: Core consolidado en HTML estatico (ley, metricas, comparador, resultados y modos).
- `engine/`: Demos ejecutables en Python:
	- `demo.py` (Streamlit) - modo grafo
	- `mcl_chess.py` - ajedrez estructural (experimental)
	- `compare_v42.py` - comparador v4.2

## Correr la web (estatica)
Abre `she-core/web/index.html` en el navegador, o sirve el folder con un servidor estatico:

```bash
python -m http.server 8000 --directory she-core/web
```