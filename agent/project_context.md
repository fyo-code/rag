# Project Context

## Stack Overview

**Backend:** FastAPI (Python 3.11+)
**Frontend:** Next.js 14+ (App Router)
**Data Storage:** DuckDB (70k CSV analytics)
**Vector DB:** ChromaDB (RAG/embeddings)

---

## Architecture

```
┌───────────────────────────────────────┐
│           Next.js Frontend            │
│   (React, TypeScript, Tailwind CSS)   │
└─────────────────┬─────────────────────┘
                  │ HTTP/REST
                  ▼
┌───────────────────────────────────────┐
│            FastAPI Backend            │
│   (Python, Pydantic, SQLAlchemy)      │
└─────────────────┬─────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│    DuckDB     │   │   ChromaDB    │
│  (Analytics)  │   │  (Vectors)    │
└───────────────┘   └───────────────┘
```

---

## Tech Stack Details

### Backend (Python/FastAPI)
- **FastAPI** for async API endpoints
- **Pydantic v2** for data validation
- **DuckDB** for analytical queries on CSV data
- **ChromaDB** for vector search and RAG
- **SQLAlchemy 2.0** (async) for ORM if needed

### Frontend (Next.js)
- **Next.js 14+** with App Router
- **React 18** with Server Components
- **TypeScript** (strict mode)
- **Tailwind CSS** for styling
- **TanStack Query** for data fetching

### Data Layer
- **Data Source:** 70k row CSV files
- **Analytics DB:** DuckDB (in-process, fast OLAP)
- **Vector Store:** ChromaDB (embeddings + semantic search)

---

## Directory Structure

```
project/
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── data/
│   └── *.csv
└── .agent/
    ├── workflows/
    ├── agents/
    └── skills/
```

---

## Key Decisions

1. **Why DuckDB?** Perfect for analytics on CSV data (70k rows). In-process, no server needed, SQL interface.

2. **Why ChromaDB?** Simple vector store for RAG. Persistent storage, easy integration with Python.

3. **Why FastAPI + Next.js?** Best of both worlds: Python data ecosystem + React UI. Type safety end-to-end.

4. **Why Tailwind?** Rapid UI development with consistent design system. Great dark mode support.

---

## Getting Started

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Available Agents

- `architect` - System design and technology decisions
- `backend` - FastAPI/Python development
- `frontend` - Next.js/React development
- `data_analyst` - SQL/Pandas/DuckDB queries
- `debugger` - Issue investigation and fixes

## Available Workflows

- `/create` - Build new features
- `/plan` - Project planning
- `/debug` - Investigate issues
- `/enhance` - Update existing features
- `/deploy` - Production deployment
- `/orchestrate` - Multi-agent coordination
