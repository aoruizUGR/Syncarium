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
cd syncarium
pip install -r requirements.txt
```

---

## 🚀 Uso básico

```bash
python -m main
```

---

## 📁 Estructura del proyecto

```
Syncarium/
├── core/               # Lógica principal del sistema
├── config/             # Archivos de configuración YAML
├── monitor/            # Módulos de monitorización
├── utils/              # Funciones auxiliares
├── tests/              # Pruebas unitarias
└── README.md           # Este archivo
```

---

## 🧰 Tools Used
- **Python**
- **Cisco TRex**
- **ptp4l**
- **Linux namespaces**
- **Custom network drivers**

## 🖥️ Compatible Environment

- Operating System: **Linux**
- Recommended Distribution: **Ubuntu** (tested)

## 📜 Licencia

Este software se distribuye bajo la licencia **MIT**. Puedes consultarla en el archivo `LICENSE`.

> Si eres investigador y deseas reutilizar Syncarium en tus experimentos, por favor cita adecuadamente esta herramienta y su autoría.

---

## 👨‍🔬 Autor

**Alberto Ortega Ruiz**  
Doctorando en Ingeniería de Telecomunicación  
Universidad de Granada  
alberto.ortega@ugr.es

---

## 📚 Referencias

- Ortega Ruiz, A. (2025). *Time Transfer and High Precision Synchronization in Spine-Leaf Topologies for Datacenters*. Universidad de Granada.
- IEEE 1588 Precision Time Protocol (PTP)
- NTP: Network Time Protocol

---

## 🤝 Contribuciones

Las contribuciones están abiertas para investigadores y desarrolladores interesados en la sincronización temporal. Por favor, abre un _issue_ o envía un _pull request_.
```

---

¿Quieres que te genere también el archivo `LICENSE` con la licencia MIT? Puedo hacerlo ahora mismo.