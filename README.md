# CLEAR: A Knowledge-Centric Vessel Trajectory Analysis Platform

[![Demo Video](https://img.shields.io/badge/Demo-Video-blue)](https://github.com/hyLiu1994/CLEAR)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

**CLEAR** (**C**omprehensive Vesse**l** Traj**e**ctory **A**nalysis Platfo**r**m) is a knowledge-centric platform that transforms raw AIS (Automatic Identification System) data into complete, interpretable, and easily explorable vessel trajectories. By leveraging Large Language Models (LLMs) and a Structured Data-derived Knowledge Graph (SD-KG), CLEAR makes maritime trajectory analysis accessible to non-expert users.

## 🚢 Overview

Maritime vessel trajectories from AIS provide critical insights for analyzing ship movements, operational efficiency, and safety compliance. However, AIS data presents two major challenges:

1. **Missing Observations**: Gaps from communication outages, intentional AIS switch-off, and heterogeneous sampling policies
2. **Semantic Complexity**: Requires combining kinematic signals with vessel attributes, regulations, and contextual information

CLEAR addresses these challenges through:
- **Automated trajectory completion** using knowledge-driven imputation
- **Transparent explanations** for all inferred behaviors and imputation decisions
- **Interactive exploration** of both trajectories and underlying maritime knowledge
- **Accessible interface** designed for users without deep maritime or database expertise

## ✨ Key Features

### 🔄 Data–Knowledge–Data Loop
Built on the [VISTA framework](https://github.com/hyLiu1994/VISTA), CLEAR implements a continuous loop that:
1. **Distills knowledge** from observed AIS trajectories into a structured knowledge graph
2. **Applies knowledge** back to complete missing trajectory segments
3. **Updates knowledge** as new data is processed

### 🧠 Structured Data-derived Knowledge Graph (SD-KG)
The SD-KG integrates three types of nodes:
- **Static Attribute Nodes**: Vessel types, navigation statuses, spatial contexts, vessel dimensions, etc.
- **Behavior Pattern Nodes**: Port-Entry: Decelerate–Align, Open-Sea: Steady Cruise, etc.
- **Imputation Method Nodes**: Executable functions optimized for specific behavior patterns

### 📊 Knowledge-Centric Analysis
CLEAR offers three core analysis functions that enable non-expert users to interpret individual trajectories and explore the underlying maritime knowledge:

#### 1. Comprehensive Analysis Reports
CLEAR provides detailed, evidence-backed reports for all SD-KG node types:
- **Segment Reports**: Display static attributes, inferred behavior context (previous, current, and next behaviors), and explanatory reasoning for behavioral and imputation estimates, alongside a SD-KG subgraph showing related nodes
- **Static Attribute Reports**: Show vessels, behaviors, and imputation methods associated with specific attributes (e.g., vessel type "Cargo", navigation status "Underway using engine")
- **Behavior Pattern Reports**: Present detailed pattern characteristics (speed, course, heading, navigation intent, duration) and associated static attributes and imputation methods
- **Imputation Method Reports**: Describe function implementations, applicable behavior patterns, and success metrics with SD-KG evidence

#### 2. Interactive Map-Based Trajectory Analysis
- **Segment-level Interaction**: Click any trajectory segment on the map to open its knowledge-centric analysis report
- **Visual Distinction**: Observed segments displayed in purple, imputed segments in red
- **Filtering Capabilities**: Filter trajectories by MMSI, time range, or geographic region
- **Knowledge Navigation**: Seamlessly navigate from map segments to related SD-KG nodes and their analysis reports

#### 3. Dedicated SD-KG Graph Viewer
CLEAR supports deep knowledge exploration through two complementary modes:
- **Graph Visualization**: Interactive network graph presenting SD-KG nodes and their connections
  - Filter nodes by type (static attributes, behavior patterns, imputation methods) or keyword
  - Drag nodes to highlight connected edges and explore relationships
  - Zoom to view node labels and examine graph structure
  - Click nodes to open their detailed analysis reports
- **Reciprocal Report Navigation**: Within any analysis report, click related nodes to access their reports, enabling seamless exploration of evidence chains and knowledge connections across the SD-KG

## 🏗️ System Architecture

CLEAR is a full-stack web platform built on the VISTA framework:

```
┌─────────────────────────────────────────────────────────┐
│                   CLEAR Platform                        │
└─────────────────────────────────────────────────────────┘
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│   Frontend   │  │   Backend    │  │ VISTA Framework  │
│  (Vue 3)     │◄─┤  (FastAPI)   │◄─┤ (Git Submodule)  │
└──────────────┘  └──────────────┘  └──────────────────┘
│                 │                 │                  │
│ • Map View      │ • Trajectory    │ • SD-KG          │
│ • SD-KG         │   API           │   Construction   │
│   Explorer      │ • SD-KG API     │ • Trajectory     │
│ • Node Docs     │ • VISTA         │   Imputation     │
│ • Settings      │   Integration   │ • Workflow Mgmt  │
└─────────────────└─────────────────└──────────────────┘
```

**VISTA Framework** is integrated as a Git submodule (`clear-backend/vista/`). For detailed information about the VISTA framework architecture and its data-knowledge-data loop, see the [VISTA documentation](https://github.com/hyLiu1994/VISTA).

### Project Structure

```
CLEAR/
├── clear-frontend/          # Vue 3 + Vite frontend application
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue     # Landing page
│   │   │   ├── Map.vue      # Interactive trajectory map
│   │   │   ├── SDKG.vue     # Knowledge graph explorer
│   │   │   ├── NodeDoc.vue  # Node documentation viewer
│   │   │   └── Settings.vue # Configuration interface
│   │   ├── components/      # Reusable Vue components
│   │   ├── router/          # Vue Router configuration
│   │   └── main.js          # Application entry point
│   └── package.json
│
├── clear-backend/           # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── trajectory.py # Trajectory endpoints
│   │   │   ├── sdkg.py      # SD-KG endpoints
│   │   │   ├── vista.py     # VISTA integration
│   │   │   └── update.py    # Update endpoints
│   │   ├── core/
│   │   │   └── config.py    # Application configuration
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt
│   └── vista/               # VISTA framework (Git submodule)
│
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm
- Git (for cloning and submodule management)
- An LLM API key (OpenAI, Alibaba Cloud DashScope, or compatible service)

### Installation

```bash
# Clone the repository with submodules
git clone --recurse-submodules https://github.com/hyLiu1994/CLEAR.git
cd CLEAR

# If you already cloned without --recurse-submodules, initialize the submodule
git submodule update --init --recursive

# Install backend dependencies
cd clear-backend
pip install -r requirements.txt

# Install VISTA framework environment
cd vista
bash environment_install.sh
cd ..

# Install frontend dependencies
cd ../clear-frontend
npm install
cd ..
```

### Quick Start

```bash
# Terminal 1: Start the backend server
cd clear-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend development server
cd clear-frontend
npm run dev
```

Access the platform at `http://localhost:5173` (Vite default port)

## 📖 Usage Guide

### Scenario I: Knowledge-Centric Trajectory Analysis

1. **Open Map Viewer**: Click the "Map" button
2. **Filter Trajectories**: Use the sidebar to filter by MMSI, time range, or geographic region
3. **Select a Segment**: Click any trajectory segment on the map
4. **View Analysis Report**: Examine:
   - Behavior patterns (speed, course, heading, intent)
   - Static vessel attributes
   - Imputation methods (for reconstructed segments)
   - Related SD-KG subgraph

### Scenario II: Exploring the SD-KG

1. **Open Graph Viewer**: Click the "SD-KG" button
2. **Filter Nodes**: Use keyword search or filter by node type
3. **Examine Relationships**:
   - Drag nodes to highlight connected edges
   - Zoom to view node labels
   - Click nodes to open detailed analysis reports
4. **Navigate Between Views**: Seamlessly move between graph view and map view

### Scenario III: Configure and Process Data

1. **Open Settings**: Click the "Settings" button to configure data processing
2. **Select Data Source**: Choose **AIS-DK** ([Denmark](http://aisdata.ais.dk/)) or **AIS-US** ([United States](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/))
3. **Configure Parameters**: Set date range, time intervals, and VISTA processing options
4. **Execute Pipeline**: Click buttons to build SD-KG, run imputation, and generate reports
5. **View Results**: Navigate to Map or SD-KG views to explore completed trajectories and knowledge graph

For detailed data preparation instructions, see the [Data Guide](https://github.com/hyLiu1994/VISTA/src/data).

For SD-KG construction and trajectory imputation details, see the [VISTA Pipeline](https://github.com/hyLiu1994/VISTA).


## 🙏 Acknowledgments

This research is funded by the European Union's Horizon Europe programme through the [MobiSpaces](https://mobispaces.eu/) project (grant agreement no. 101070279) and [6G-XCEL](https://www.6g-xcel.eu) project (grant agreement no. 101139194).
