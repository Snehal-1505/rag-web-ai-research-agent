# ✨ Loomi AI — RAG + Web AI Research Workspace

> *"Weaving knowledge into answers."*

![Python Version](https://img.shields.io/badge/Python-3.11-blue.svg)
![Frontend](https://img.shields.io/badge/Frontend-React_18_+_TypeScript_+_Vite-61DAFB.svg)
![Styling](https://img.shields.io/badge/Design-Tailwind_CSS_+_Warm_Editorial-E66A4E.svg)
![Framework](https://img.shields.io/badge/Haystack-2.x-orange.svg)
![Vector DB](https://img.shields.io/badge/Vector_DB-ChromaDB_Persistent-teal.svg)
![Chat DB](https://img.shields.io/badge/Chat_History-SQLite_WAL-blue.svg)
![LLM](https://img.shields.io/badge/Google-Gemini_Flash-purple.svg)
![Web Search](https://img.shields.io/badge/Search-Tavily%20%2F%20DuckDuckGo-green.svg)

---

## 🌟 Overview

**Loomi AI** is a Gen-Z inspired, warm editorial AI research workspace designed for curious minds. It blends:
- **Persistent Local Document RAG**: PDF, TXT, and DOCX ingestion with ChromaDB vector storage and SHA-256 deduplication.
- **Autonomous Web Research**: Real-time web intelligence via Tavily API with zero-cost DuckDuckGo fallback.
- **Hybrid Intent Router**: Dynamically routes between local knowledge and the live web, synthesizing authoritative answers with interactive citation cards.
- **Modern Full-Stack Architecture**: React 18, TypeScript, Vite, Tailwind CSS, Lucide icons, and Framer Motion powered by a high-performance FastAPI backend.
- **Unified Workspace Experience**: Clean, fast, and responsive workspace running on `http://localhost:8000` (production) or `http://localhost:5173` (Vite dev).

---

## 🎨 Visual Identity & Design Tokens

Loomi AI adopts a **Creative Studio / Warm Editorial** aesthetic with carefully tuned light and dark palettes:

| Token Name | Light Theme Hex | Dark Theme Hex | Purpose |
| :--- | :--- | :--- | :--- |
| **Warm Ivory / Deep Ink** | `#F7F2E9` | `#141613` | Main workspace background surface |
| **Brand Coral** | `#E66A4E` | `#F07A60` | Primary actions, accents, active indicators |
| **Ink Charcoal / Soft Text** | `#252821` | `#F5EFE6` | Primary editorial typography |
| **Sand Beige / Dark Elevated** | `#EFE5D8` | `#252822` | Cards, composer surfaces, dividers |
| **Secondary Muted** | `#77746D` | `#9E9A91` | Metadata, timestamps, helper labels |

---

## 🏗️ Architecture & Pipeline Flow

```mermaid
flowchart TD
    subgraph Frontend - Loomi AI (React + TypeScript)
        UI[Sidebar, ChatHeader, MessageList, ChatInput, DocumentUpload]
        Store[useChat, useSessions, useTheme]
        UI <--> Store
    end

    subgraph Backend Adapter - server.py (FastAPI)
        API[REST & SSE Endpoints]
        Store <-->|REST & Server-Sent Events| API
    end

    subgraph Knowledge & Persistence Layer
        DB[(SQLite - chat_history.db)]
        Chroma[(ChromaDB - data/chroma_db/)]
        Uploads[Local Uploads - data/uploads/]
        API <--> DB
        API <--> Chroma
        API --> Uploads
    end

    subgraph RAG & Research Agent (Haystack 2.x)
        Agent{Research Agent Router}
        DocSearch[ChromaDB Vector Retrieval]
        WebSearch[Tavily & DuckDuckGo Search]
        Gemini[Google Gemini 3.8 Flash]

        API --> Agent
        Agent --> DocSearch
        Agent --> WebSearch
        DocSearch --> Chroma
        Agent --> Gemini
    end
```

---

## ⚡ Quick Start & Local Execution

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Virtual Environment & Dependencies
```bash
# Activate virtual environment
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # macOS/Linux

# Install Python backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
npm --prefix frontend install
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and provide your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here   # Optional (falls back to DuckDuckGo)
DATA_DIR=./data                           # Defaults to ./data locally, /var/data on Render
```

---

## 🚀 Running Loomi AI

### Option A: Production Mode (Single Command)
Builds the React bundle and serves both the API and UI through FastAPI on `http://localhost:8000`:
```bash
# 1. Build React frontend
npm --prefix frontend run build

# 2. Run unified server
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```
Open your browser to: **`http://localhost:8000`**

### Option B: Development Mode (Hot-Reloading)
Run the FastAPI backend on port 8000 and the Vite dev server on port 5173:
```bash
# Terminal 1: Backend API
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: React Vite Dev Server
npm --prefix frontend run dev
```
Open your browser to: **`http://localhost:5173`** (API requests are automatically proxied to port 8000).

---

## 🔌 API Adapter Contract (`server.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health status, indexed chunk count, and configured service status. |
| `GET` | `/api/sessions` | List all conversation sessions ordered newest first. |
| `POST` | `/api/sessions` | Create a new conversation session. |
| `GET` | `/api/sessions/{session_id}` | Retrieve session messages in chronological order. |
| `PATCH` | `/api/sessions/{session_id}` | Rename conversation session title. |
| `DELETE` | `/api/sessions/{session_id}` | Safely delete a session and its message history. |
| `POST` | `/api/chat` | Synchronous RAG answer generation with document and web sources. |
| `POST` | `/api/chat/stream` | Server-Sent Events (SSE) streaming endpoint emitting real-time delta tokens and sources. |
| `POST` | `/api/documents/upload` | Upload and index `.pdf`, `.txt`, `.docx` into ChromaDB with SHA-256 deduplication. |
| `GET` | `/api/documents` | List registered documents and indexed filenames. |
| `GET` | `/api/documents/{id}/status` | Poll ingestion and indexing progress for uploaded documents. |

---

## 🧪 Automated Tests

The test suite covers Haystack components, vector retrieval, chunking, web search fallback, and the FastAPI adapter contract:

```bash
# Run complete test suite (27 passing tests)
pytest -v
```

---

## ☁️ Deployment on Render

This repository includes a production-ready `render.yaml` Blueprint and `Procfile`:
- **Build Command:** `npm --prefix frontend install && npm --prefix frontend run build && pip install torch --extra-index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt`
- **Start Command:** `python startup.py && python -m uvicorn server:app --host 0.0.0.0 --port $PORT`
- **Persistent Disk:** Mounted at `/var/data` with environment variable `DATA_DIR=/var/data`.

---

## 📜 License
MIT License. Created with Haystack AI, Google Gemini, and React.