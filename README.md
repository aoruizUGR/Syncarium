
# Syncarium

**Syncarium** is a software tool developed as part of the doctoral thesis _"Time Transfer and High Precision Synchronization in Spine-Leaf Topologies for Datacenters"_ at the University of Granada. Its goal is to simplify the configuration, deployment, and monitoring of time synchronization platforms in distributed environments.

---

## 🧪 Purpose

Syncarium enables:
- Automated deployment of synchronization tools across distributed nodes.
- Automated development of experiments for time measurements.
- Monitoring of time synchronization accuracy between devices.
- Integration with tools for temporal data analysis and visualization.

---

## ⚙️ Features

- Support for synchronization protocols (currently only PTP).
- Modular interface for experimenting with different configurations.
- Detailed logging of synchronization metrics.
- Compatible with Linux environments and Python 3.11.

---

## 📦 Installation

```bash
git clone https://github.com/aoruizUGR/syncarium.git

pip install -r requirements.txt
```

---

## 🚀 Basic Usage

```bash
python -m syncarium.main
```

---

## 📁 Project Structure

```
Syncarium/
│
├── config/                         # Configuration templates for program components
│   ├── datasources_scenarios/      # Templates for data sources
│   ├── dpdk_profiles/              # Templates for DPDK profiles
│   ├── experiments_scenarios/      # Templates for experiment scenarios
│   ├── load_scenarios/             # Templates for load generation scenarios
│   ├── namespaces_scenarios/       # Templates for namespace scenarios
│   ├── ntp_profiles/               # Templates for NTP profiles
│   └── ptp_profiles/               # Templates for PTP profiles
│
├── logs/           # Temporary log files
├── options/        # Global configurable options for program execution
├── output/         # Syncarium outputs
├── scripts/        # Shell scripts for OS tasks
├── submodules/     # External submodules
├── tui/            # Program's TUI
│   ├── core/       # Program core
│   └── utils/      # Utilities for program execution
│
├── main.py             # Program entrypoint
├── __init__.py         # Entrypoint module
├── requirements.txt    # Dependencies
└── README.md           # This file
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

## 📜 License

This software is distributed under the **MIT** license. You can find it in the `LICENSE` file.

> If you are a researcher and wish to reuse Syncarium in your experiments, please cite this tool and its authorship appropriately.

---

## 👨‍🔬 Author

**Alberto Ortega Ruiz**  
PhD Candidate in Telecommunication Engineering  
University of Granada  
alberto.ortega@ugr.es

---

## 📚 References

- Ortega Ruiz, A. (2025). *Time Transfer and High Precision Synchronization in Spine-Leaf Topologies for Datacenters*. University of Granada.
- IEEE 1588 Precision Time Protocol (PTP)
- NTP: Network Time Protocol

---

## 🤝 Contributions

Contributions are welcome from researchers and developers interested in time synchronization. Please open an _issue_ or submit a _pull request_.

---