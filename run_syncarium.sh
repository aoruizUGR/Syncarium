#!/bin/bash
# run_syncarium.sh

# Asegúrate de que el script tenga permisos de ejecución: chmod +x run_syncarium.sh

# Ejecuta el servidor de Streamlit bajo privilegios de root pero manteniendo el entorno virtual

sudo env PATH="$PATH" python3 -m streamlit run syncarium/main.py --server.port=8501 --server.headless=true