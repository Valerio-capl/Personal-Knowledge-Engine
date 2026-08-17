# Custom RAG & Personal Knowledge Engine

A completely custom RAG system built from scratch in Python and TypeScript. 

Instead of relying on heavy abstractions like LangChain or LlamaIndex, this project implements the core mechanics of a vector search engine, document indexing, and answer generation from the ground up, focusing on Clean Architecture and Domain-Driven Design.

## Key Features

* **Custom Vector Store**: In-memory vector database built with NumPy using cosine similarity, with disk persistence via `.npy` + `.json`.
* **Sync Engine**: Tracks document state using SQLite. Only chunks and re-embeds files that are new or modified, based on content hashing.
* **Hybrid Embedding & Generation Providers**: Switch between local models (Ollama) and cloud APIs (OpenAI) via a Factory pattern, for both embedding and answer generation. Each embedding provider+model combination gets its own isolated vector space.
* **Answer Engine**: Retrieval-augmented answers with source citations (`[1]`, `[2]`), with a per-provider relevance threshold to avoid answering from irrelevant context.
* **FastAPI Backend**: REST API for sync, search, ask, and space discovery.
* **React Frontend**: Local web UI built with TypeScript and Tailwind CSS.

## Tech Stack
**Backend**
* Python 3, FastAPI, SQLite, NumPy
* OpenAI API, Ollama

**Frontend**
* TypeScript, React, Tailwind CSS

**Testing**
* Pytest (backend)

## Getting Started
### Backend

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY if you plan to use OpenAI
uvicorn api.main:app --reload --app-dir src
```

API available at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`.

### Local models (optional)

To use Ollama, install [Ollama](https://ollama.com) and pull the models you plan to use (e.g., ollama pull nomic-embed-text-v2-moe for embeddings and ollama pull llama3.1 for generation).

### Tests

```bash
pytest .\tests\
```

## Project Status
Core pipeline complete and working end-to-end through both the API and the web UI

Remaining known gaps:
* No automatic retry on generation provider failures (embedding providers already retry with backoff).
* Vector search is brute-force cosine similarity over the full in-memory matrix (O(N) per query), not an approximate nearest-neighbor index — fine for small/medium personal collections, but won't scale to very large document sets without a different vector store backend.