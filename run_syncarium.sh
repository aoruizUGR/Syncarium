#!/bin/bash
# run_syncarium.sh

# chmod +x run_syncarium.sh

sudo env PATH="$PATH" python3 -m streamlit run syncarium/main.py --server.port=8501 --server.headless=true