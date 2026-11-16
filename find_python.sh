#!/bin/bash

# find_python.sh
# Este script busca todos los archivos .py en el directorio actual y sus subdirectorios.

echo "Buscando archivos Python en el proyecto..."
echo "----------------------------------------"

# Usamos 'find' para localizar archivos .py
# -type f: busca solo archivos
# -name "*.py": filtra por extensión
# -not -path "*/.*": excluye archivos ocultos (como .git, .venv, etc.)
find . -type f -name "*.py" -not -path "*/.*" | sort | while read -r file; do
    echo "Archivo encontrado: $file"
done

echo "----------------------------------------"
echo "Búsqueda finalizada."
