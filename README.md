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

cd Syncarium/

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
syncarium/                              # Project root
│
├── docs/                               # Documentation
│
├── submodules/                         # Submodules Links
│   ├── dpdk/                           
│   ├── linuxptp/                       
│   └── TimeStick/                      
│
├── syncarium/                          # Program
│   ├── config/                         # Scenarios examples
│   ├── core/                           # Program core
│   │   ├── dsources/                   # Datasources
│   │   ├── data_ex.py                  # Data extractor
│   │   ├── exp_orchestra.py            # Experiment orchestration
│   │   ├── experiment.py               # Experiment
│   │   ├── load_gen.py                 # Load Generator
│   │   └── sync_core.py                # Syncronization core
│   │
│   ├── options/                        # Configurable global and private vars
│   ├── scripts/                        # Shell scripts
│   ├── utils/
│   │   ├── sysaux.py                   # Auxiliar system functions
│   │   ├── telegram.py                 # Telegram Bot Notifications
│   │   └── viewtools.py                # Rich and visual auxiliar functions
│   │
│   ├── main.py                         # Program entrypoint
│   └── tui.py                          # Textual User Interface
│
├── requirements.txt                    # Dependencies
└── README.md                           # This file
```

---

## 🖥️ Compatible Environment

- Operating System: **Linux 6.8.0-85-generic**
- Recommended Distribution: **Ubuntu 24.04.2 LTS** (tested)

---

## 📜 License

This software is distributed under the **GPL-3.0** license. You can find it in the `LICENSE` file.

> If you are a researcher and wish to reuse Syncarium in your experiments, please cite this tool and its authorship appropriately.

---

## 🤖 Tools

- [DPDK - Data Plane Development Kit](https://github.com/DPDK/dpdk)
- [OCP-Times Appliances Project - TimeStick](https://github.com/Time-Appliances-Project/TimeStick)
- [LinuxPTP](https://github.com/richardcochran/linuxptp)

---

## 👨‍🔬 Author

**Alberto Ortega Ruiz**  
PhD Student  
Time-based Technologies and Networks Lab  
University of Granada  
aoruiz@ugr.es

---

## 🤝 Contributions

- Víctor Vázquez Rodríguez  
- NetTimeLogic GmbH, Switzerland

Contributions are welcome from researchers and developers interested in time synchronization. Please open an _issue_ or submit a _pull request_.

