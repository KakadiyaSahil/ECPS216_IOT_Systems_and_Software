# Smart Swarm Sensor Array Network System

A distributed IoT and embedded systems project built using **ESP8266 devices, Raspberry Pi, light sensors, LEDs, UDP communication, data logging, and web-based visualization**.

The project progressively develops a single-node light-monitoring application into a dynamically scalable **multi-device swarm network**, where ESP8266 devices communicate wirelessly, elect a Master based on light intensity, and report data to a Raspberry Pi for monitoring, logging, and visualization.

---

## Project Overview

The system consists of:

- **ESP8266** — distributed sensor nodes
- **Raspberry Pi** — central controller, logger, and visualization server
- **Photoresistor / LDR** — ambient light measurement
- **TCS34725 RGB sensor** — RGB/light sensing in the initial implementation
- **RGB LEDs** — light-level and system-status indication
- **LED bar graph** — light-intensity visualization
- **LED Matrix** — photocell data visualization
- **7-Segment Display** — current Master-device indication
- **Pushbutton** — swarm reset and system control
- **UDP over Wi-Fi** — wireless communication
- **Node-RED** — web-based monitoring and visualization

---

# Project Architecture

```text
                    ┌──────────────────────┐
                    │     Raspberry Pi     │
                    │                      │
                    │  • UDP Receiver      │
                    │  • Master Tracking   │
                    │  • Data Logging      │
                    │  • Web Server        │
                    │  • Node-RED          │
                    │  • LED Matrix        │
                    │  • 7-Segment Display │
                    └──────────┬───────────┘
                               │
                         Wi-Fi / UDP
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐     ┌──────────┐
        │ ESP8266  │     │ ESP8266  │     │ ESP8266  │
        │ Node 1   │     │ Node 2   │     │ Node 3   │
        │          │     │          │     │          │
        │ LDR      │     │ LDR      │     │ LDR      │
        │ LED      │     │ LED      │     │ LED      │
        └──────────┘     └──────────┘     └──────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                       Dynamic Swarm
                       Master Election
```

The final system is designed to dynamically support multiple ESP8266 devices. The device with the highest light-sensor reading becomes the **Master** and provides data to the Raspberry Pi.

---

# Assignments

## 01 — Light Up Your Life

The first assignment establishes the foundation of the project by using an **ESP8266** with a **TCS34725 RGB color sensor** to monitor ambient light.

### Features

- Ambient light measurement
- Light-intensity processing
- Threshold-based LED activation
- Multilevel light-intensity indication
- Dynamic LED flashing based on measured intensity
- Pushbutton-based mode selection

### Operating Modes

The system provides different visual feedback based on measured light intensity:

```text
Light Intensity
      │
      ├── Low    → Green LED
      │
      ├── Medium → Yellow LED
      │
      └── High   → Red / Blue LED
```

The dynamic flashing mode changes the flashing rate according to the measured light intensity.

### Concepts Demonstrated

- ESP8266 programming
- Sensor interfacing
- GPIO control
- LED control
- Pushbutton input
- Real-time embedded control

---

# 02 — UDP Implementation

The second assignment introduces **wireless network communication** between an ESP8266 and a Raspberry Pi.

The ESP8266 reads light-level data from an **LDR/photoresistor**, processes the measurements, and sends the resulting information to the Raspberry Pi using **UDP over Wi-Fi**.

### Features

- ESP8266 Wi-Fi connectivity
- UDP communication
- LDR sensor acquisition
- Sensor-data processing
- Average light-intensity calculation
- Raspberry Pi communication
- State-based communication
- Handshake synchronization

### Communication

```text
ESP8266
   │
   │ Light Sensor Data
   │
   ▼
Wi-Fi / UDP
   │
   ▼
Raspberry Pi
```

This assignment establishes the communication infrastructure used by later swarm implementations.

---

# 03 — UDP Implementation Final Version

The third assignment extends the ESP8266–Raspberry Pi communication system into a more complete distributed light-monitoring application.

### Features

- ESP8266 light sensing
- Raspberry Pi central control
- UDP packet communication
- Wi-Fi networking
- RGB LED control
- Light-intensity classification
- Error handling
- User-triggered system reset

The Raspberry Pi processes the sensor data received from the ESP8266 and controls LEDs according to the measured light level.

```text
            ESP8266
               │
          Photoresistor
               │
               ▼
        Sensor Processing
               │
               ▼
          UDP / Wi-Fi
               │
               ▼
         Raspberry Pi
               │
        ┌──────┴──────┐
        ▼             ▼
    Processing      RGB LEDs
```

---

# 04 — All for One, and One for All

The fourth assignment introduces the **swarm architecture**.

Multiple ESP8266 devices monitor light levels and communicate as part of a distributed system.

### Swarm Components

```text
              Raspberry Pi
                   │
            Wi-Fi / UDP
                   │
       ┌───────────┼───────────┐
       │           │           │
       ▼           ▼           ▼
    ESP8266     ESP8266     ESP8266
       │           │           │
      LDR         LDR         LDR
       │           │           │
       └───────────┼───────────┘
                   │
            Master Election
```

### Master Selection

Each ESP8266 measures its local light intensity.

The device with the **highest light-sensor reading** becomes the Master.

```text
ESP8266 #1 → Light = 350
ESP8266 #2 → Light = 720  ← MASTER
ESP8266 #3 → Light = 510
```

The Master communicates its data to the Raspberry Pi for logging and monitoring.

### Features

- Multi-ESP8266 communication
- Dynamic Master selection
- Raspberry Pi central controller
- Sensor-data logging
- LED status indication
- Pushbutton-based swarm reset
- Support for dynamic 1–3 ESP8266 operation

---

# 05 — The Plot Thickens

The fifth assignment expands the swarm system with **data logging and visualization**.

The Raspberry Pi records information from the Master ESP8266 and generates graphs for analyzing the swarm behavior.

### Data Logged

The Raspberry Pi records:

- ESP8266 devices that become Master
- Master IP addresses
- Master duration
- Raw sensor data
- Data associated with the current swarm run

### System Flow

```text
ESP8266 Nodes
      │
      ▼
Master Election
      │
      ▼
Current Master
      │
      ▼
Raspberry Pi
      │
      ├── Data Logging
      │
      ├── Master Tracking
      │
      └── Graph Generation
```

The system continues to support dynamic operation with multiple ESP8266 devices.

---

# 06 — Implement Remote Logging

The final assignment extends the swarm into a more complete **IoT monitoring and visualization system**.

The system is designed to dynamically support **3–6 ESP8266 devices** without hard-coded device IP addresses. Broadcast communication is permitted for device discovery.

## ESP8266 Features

At least one ESP8266 can be equipped with an **LED bar graph** that displays the current light-intensity level.

```text
Light Level

██████████  High
███████
████
██          Low
```

The ESP8266 continues to participate in the swarm and Master-selection process.

---

## Raspberry Pi LED Matrix

The Raspberry Pi uses an **LED Matrix** to display the photocell data trace over approximately the previous 30 seconds.

The display provides a compact real-time representation of sensor activity.

---

## Master Identification

For team implementations, a **4-digit 7-segment display** can indicate the last three digits of the IP address of the current Master.

Example:

```text
Master IP: 192.168.1.135

7-Segment:

  135
```

---

# Remote Logging

The Raspberry Pi manages log files containing data from the current swarm session.

When the Raspberry Pi reset button is pressed:

1. All ESP8266 devices are reset.
2. The Raspberry Pi Yellow LED turns on for approximately 3 seconds.
3. The current log file is saved.
4. A new log file is created.
5. The filename includes the current date and time.
6. The monitoring graphs/charts are reset.
7. The new swarm session begins.

### Logged Information

Each log contains:

- Current date/time
- ESP8266 devices that became Master
- Master IP addresses
- Master duration
- Raw sensor measurements

---

# Web-Based Monitoring

The Raspberry Pi provides web-based monitoring using **Node-RED**.

The monitoring interface provides two primary visualizations.

## 1. Photocell Data Trace

Displays photocell/light-sensor measurements over time.

The system can support:

- Static visualization from saved log files
- Real-time visualization
- Approximately 30 seconds of recent data
- Periodic updates

For multi-device implementations, Master transitions can be represented through changes in the trace.

---

## 2. Master Device Duration

A bar chart displays the ESP8266 devices that have acted as Master and the amount of time each device has remained Master.

Example:

```text
Master Device

192.168.1.101 | ███████████
192.168.1.102 | ██████
192.168.1.103 | ███████████████
```

This provides a way to analyze Master-node behavior across the swarm.

---

# Final System

The completed project combines:

```text
        ┌─────────────────────────────┐
        │       ESP8266 Swarm         │
        │                             │
        │  Sensor Acquisition         │
        │  UDP Communication          │
        │  Master Election            │
        │  LED Feedback               │
        └──────────────┬──────────────┘
                       │
                    Wi-Fi
                       │
                       ▼
        ┌─────────────────────────────┐
        │       Raspberry Pi          │
        │                             │
        │  UDP Communication          │
        │  Master Tracking            │
        │  Data Processing            │
        │  Remote Logging             │
        │  System Reset               │
        │  Web Server                 │
        │  Node-RED                   │
        │  LED Matrix                 │
        └──────────────┬──────────────┘
                       │
                       ▼
             Web-Based Monitoring
```

The final system demonstrates a progression from basic embedded sensor interfacing to a distributed, dynamically scalable IoT swarm network.

---

# Key Technologies

| Category | Technologies |
|---|---|
| Microcontroller | ESP8266 |
| Central Controller | Raspberry Pi |
| Programming | C/C++, Python |
| Communication | UDP, Wi-Fi |
| Sensors | LDR / Photoresistor, TCS34725 |
| Embedded I/O | GPIO, LEDs, Pushbuttons |
| Visualization | Node-RED, LED Matrix |
| Display | RGB LEDs, LED Bar Graph, 7-Segment |
| Data Management | Local Log Files |
| Architecture | Distributed IoT / Swarm Network |

---

# Key Concepts Demonstrated

- Embedded systems programming
- ESP8266 firmware development
- Raspberry Pi development
- GPIO programming
- Sensor interfacing
- Wi-Fi networking
- UDP communication
- Handshake synchronization
- State-machine-based control
- Distributed systems
- Dynamic Master-node election
- Multi-node swarm communication
- Real-time sensor processing
- Data logging
- Web-based visualization
- IoT system integration
- Hardware/software integration

---

# Repository Structure

```text
Smart Swarm Sensor Array Network System/
│
├── 01 - Light Up Your Life/
│
├── 02 - UDP Implementation/
│
├── 03 - UDP Implementation Final Version/
│
├── 04 - All for One, and One for All/
│
├── 05 - The Plot Thickens/
│
└── 06 - Implement Remote Logging/
```

Each directory contains the implementation associated with the corresponding stage of the project.

---

# Project Progression

```text
01
Light Sensor + LEDs
        │
        ▼
02
UDP Communication
        │
        ▼
03
ESP8266 ↔ Raspberry Pi
        │
        ▼
04
Multi-Node Swarm
        │
        ▼
05
Logging + Graphing
        │
        ▼
06
Dynamic Swarm + Remote Logging
+ Node-RED + Real-Time Visualization
```

---

## Project Focus

This project demonstrates the development of a distributed embedded IoT system from **basic sensor interfacing to dynamic multi-node swarm communication, data logging, and real-time monitoring**.