# Vanguard - AI-Powered Fault Detection and Self-Healing for Linux Kernel and Drivers

Vanguard is an AI-driven system designed to predict and prevent Linux kernel and driver failures by monitoring system logs, performance metrics, and analyzing kernel behaviors. It provides proactive fault detection, identifies the root causes of system crashes, and implements automated self-healing mechanisms, ensuring system reliability and minimizing downtime. 

The system is modular and extensible, with separate services responsible for monitoring system health, running machine learning inference for fault detection, and healing the system by applying real-time fixes.

---

## Features

- **Predict and Prevent Kernel Failures**: Monitor kernel logs (dmesg, oops reports, panic messages) and system performance (CPU usage, memory allocation, I/O operations) to identify early failure signs using machine learning models.
- **Root Cause Analysis**: Identify the causes of kernel and driver failures, such as memory errors, race conditions, or hardware faults.
- **Automated Self-Healing**: Apply dynamic recovery actions without rebooting the system. These actions include restarting drivers, reallocating memory, and rolling back system states.
- **Real-Time Monitoring**: Continuous monitoring of system health with real-time alerts for critical kernel failures and performance degradation.
- **Security and Privacy**: Safeguard system logs and kernel debug data to prevent unauthorized access and ensure privacy.
- **Modular Design**: The system is divided into three core services:
  - **Monitoring**: Collects and analyzes system logs and metrics.
  - **Inference**: Runs AI-powered fault detection and root cause analysis.
  - **Healing**: Implements recovery actions and fixes issues dynamically.

---

## Architecture

The Vanguard system consists of the following modules:

1. **Monitor (monitor/)**:
   - Collects logs (dmesg, syslog, journalctl, kernel panics) and system metrics (CPU, memory, I/O, network).
   - Uses BPF/eBPF for live kernel tracing (optional).
   
2. **Inference (inference/)**:
   - Analyzes logs and metrics using machine learning models (Random Forest, LSTM, Autoencoder).
   - Provides fault detection, classification, and root cause analysis.

3. **Healer (healer/)**:
   - Applies real-time recovery actions like restarting drivers, reallocating memory, and rolling back to stable kernel configurations.
   - Includes predefined fix templates (e.g., memory leak fixes, driver restarts).

4. **CLI (cli/)**:
   - Command-line interface for controlling the Vanguard system (e.g., `sudo vanguard --run-all`).
   - Easy-to-use interface to start/stop monitoring, inference, and healing services.

---

## Installation

### Prerequisites

- A Linux system (Ubuntu/Debian preferred)
- Root privileges (sudo)
- C++ development tools (CMake, GCC, etc.)
- Python 3.x (for inference)

### Build the Project

1. Clone the repository:
   ```bash 
   git clone https://github.com/yourusername/vanguard.git
   cd vanguard
   ```
2. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential cmake python3-pip
   sudo apt-get install libbpfcc-dev # Optional: For BPF tracing
   ```
3. Build Project:
   ```bash
   mkdir build
   cd build
   cmake ..
   make
   ```
4. Install Python dependencies for inference:
   ```bash
   cd ai_inference
   pip install -r requirements.txt
   ```
## Usage
Once the system is built, you can run the application using the following commands.
```bash
sudo ./vanguard --run-all
```
This will start the monitoring service, inference service, and self-healing service in one go.
```bash
sudo ./vanguard --monitor-only
```
This will start the monitoring service that collects logs and system metrics in real-time.

## File structure:
```bash
vanguard/
├── include/                          # Header files
│   ├── monitor/
│   │   ├── LogCollector.hpp
│   │   ├── MetricsAgent.hpp
│   │   ├── KernelTrace.hpp
│   ├── inference/
│   │   ├── InferenceBridge.hpp       # Interface to Python/ML layer
│   ├── healer/
│   │   ├── Reasoner.hpp
│   │   ├── Executor.hpp
│   │   ├── RollbackManager.hpp
│   ├── core/
│   │   ├── Config.hpp
│   │   ├── Logger.hpp
│   │   ├── Utils.hpp
│   └── cli/
│       └── VanguardCLI.hpp

├── src/                              # Implementation files
│   ├── monitor/
│   │   ├── LogCollector.cpp
│   │   ├── MetricsAgent.cpp
│   │   ├── KernelTrace.cpp
│   ├── inference/
│   │   ├── InferenceBridge.cpp       # C++ ↔ Python or REST client
│   ├── healer/
│   │   ├── Reasoner.cpp
│   │   ├── Executor.cpp
│   │   ├── RollbackManager.cpp
│   ├── core/
│   │   ├── Config.cpp
│   │   ├── Logger.cpp
│   │   ├── Utils.cpp
│   └── cli/
│       └── VanguardCLI.cpp

├── ai_inference/                     # Python ML Inference engine
│   ├── run_inference.py              # API or CLI to run inference
│   ├── model_loader.py
│   ├── preprocess.py
│   ├── postprocess.py
│   └── models/
│       ├── random_forest.pkl
│       ├── lstm.pt
│       └── autoencoder.tflite

├── templates/                        # Predefined C/shell fixes
│   ├── fix_memory_leak.c
│   └── restart_driver.sh

├── scripts/
│   ├── setup.sh                      # Installs dependencies, builds project
│   └── vanguard.service              # Optional systemd integration

├── tests/
│   ├── test_log_collector.cpp
│   ├── test_inference_bridge.cpp
│   └── test_executor.cpp

├── docs/
│   ├── README.md
│   ├── architecture.md
│   └── usage.md

├── logs/                             # Runtime logs (gitignored)
│   └── vanguard.log

├── CMakeLists.txt                    # CMake build system
├── main.cpp                          # Entrypoint
├── LICENSE
└── README.md
```



