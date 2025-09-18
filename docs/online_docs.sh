#!/bin/bash
echo "Launching documentation online in localhost:8080..."
python -m http.server 8080 --directory .
