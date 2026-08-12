# Custom RAG & Personal Knowledge Engine

A completely custom RAG system built from scratch in Python. 

Instead of relying on heavy abstractions like LangChain or LlamaIndex, this project implements the core mechanics of a vector search engine and document indexing system from the ground up, focusing on Clean Architecture and Domain-Driven Design.

## Key Features

* **Custom Vector Store**: In-memory vector database built with NumPy using cosine similarity for fast and lightweight semantic search.
* **Smart Sync Engine**: Tracks document state using SQLite. It only chunks and embeds files that are new or modified, automatically removing deleted files.
* **Hybrid Embedding Support**: Seamlessly switch between local models (Ollama) and cloud APIs (OpenAI) using a Factory pattern. Each model gets its own isolated vector space.
* **FastAPI Backend**: A clean, RESTful API routing search and sync operations.

## Tech Stack
* **Language**: Python 3
* **API Framework**: FastAPI
* **Database**: SQLite
* **Vector Math**: NumPy
* **Testing**: Pytest

## Project Status
Currently in development. Next up: building the generation Engine (prompt building with source citations) and the React Frontend interface.