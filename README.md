# Syncarium

**Syncarium** es una herramienta de software desarrollada en el marco de la tesis doctoral _"Time Transfer and High Precision Synchronization in Spine-Leaf Topologies for Datacenters"_ en la Universidad de Granada. Su objetivo es facilitar la configuración, despliegue y monitorización de plataformas de sincronización temporal en entornos distribuidos.

---

## 🧪 Propósito

Syncarium permite:
- Automatizar el despliegue de herramientas de sincronización en nodos distribuidos.
- Automatizar el desarrollo de experimentos para mediciones temporales.
- Monitorizar la precisión de sincronización temporal entre dispositivos.
- Integrarse con herramientas de análisis y visualización de datos temporales.

---

## ⚙️ Características

- Soporte para protocolos de sincronización (solamente soporte actual para PTP).
- Interfaz modular para experimentación con diferentes configuraciones.
- Registro detallado de métricas de sincronización.
- Compatible con entornos Linux y Python 3.11.

---

## 📦 Instalación

```bash
git clone https://github.com/aoruizUGR/syncarium.git

pip install -r requirements.txt
```

---

## 🚀 Uso básico

```bash
python -m syncarium.main
```

---

## 📁 Estructura del proyecto

```
syncarium/
│
├── config/                         # Plantillas de configuración para los componentes del programa
│   ├── datasources_scenarios/      # Plantillas para fuentes de datos
│   ├── dpdk_profiles/              # Plantillas para perfiles DPDK
│   ├── experiments_scenarios/      # Plantillas para scenarios de experimentos
│   ├── load_scenarios/             # Plantillas para scenarios de lanza de carga
│   ├── namespaces_scenarios/       # Plantillas para scenarios de namespaces
│   ├── ntp_profiles/               # Plantillas para perfiles NTP
│   └── ptp_ptofiles/               # Plantillas para perfiles PTP
│
├── logs/           # Archivos de logs temporales
├── options/        # Opciones configurables globales para la ejecución del programa
├── output/         # Salidas de Syncarium
├── scripts/        # Scripts shell para tareas del SO
├── submodules/     # Submódulos externos
├── tui/            # TUI del programa
│   ├── core/       # Core del programa
│   └── utils/      # Utilidades para la ejecución del programa
│
├── main.py             # Entrypoint del programa
├── __init__.py         # Módulo del entrypoint
├── requirements.txt    # Dependencias
└── README.md           # Este archivo
```

---

## 🖥️ Compatible Environment

- Operating System: **Linux**
- Recommended Distribution: **Ubuntu** (tested)

---

## 📜 Licencia

Este software se distribuye bajo la licencia **GNUv3**. Puedes consultarla en el archivo `LICENSE`.

> Si eres investigador y deseas reutilizar Syncarium en tus experimentos, por favor cita adecuadamente esta herramienta y su autoría.

---

## 👨‍🔬 Autor

**Alberto Ortega Ruiz**  
PhD Student
Time-based Technologies and Networks Lab
University of Granada
aoruiz@ugr.es

---


## 🤝 Contribuciones

- Víctor Vázquez Rodríguez
- NetTimeLogic GmbH, Switzerland

Las contribuciones están abiertas para investigadores y desarrolladores interesados en la sincronización temporal. Por favor, abre un _issue_ o envía un _pull request_.
```
