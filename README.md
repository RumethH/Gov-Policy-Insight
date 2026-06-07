# Gov-Policy-Insight 🏛️

A production-ready RAG (Retrieval-Augmented Generation) application designed for government policy analysis. This project focuses on deterministic evaluation, PII safety, and verifiable citations.

## 🚀 Overview

Gov-Policy-Insight allows users to query complex public policy documents and receive accurate, cited answers. Unlike a standard POC, this system includes:
- **PII Redaction**: Ensuring sensitive data never reaches the LLM via Microsoft Presidio.
- **Semantic Caching**: High-performance caching using embedding similarity to reduce API costs.
- **Parallel Retrieval**: Multi-query retrieval optimized with concurrency.
- **Streamlit UI**: A fast, interactive interface for policy researchers.
- **FastAPI Backend**: A robust REST API for serving the RAG pipeline.

## 🛠️ Tech Stack

- **Interface:** [Streamlit](https://streamlit.io/)
- **API Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Orchestration:** [LangChain](https://www.langchain.com/)
- **Vector Database:** [ChromaDB](https://www.trychroma.com/)
- **Embeddings/LLM:** Gemini 1.5 Flash
- **Reranker:** [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank)
- **Security:** Microsoft Presidio (PII Redaction)

## 📂 Project Structure

```text
gov-policy-insight/
├── data/               # Source PDFs (Public Policies)
├── backend/            # RAG Logic & FastAPI Server
│   ├── main.py         # API Entrypoint
│   └── core/           # Core Pipeline (Chains, Security, Cache)
├── frontend/           # Streamlit Application
├── scripts/            # Audit and Utility scripts
├── evals/              # Evaluation Suite (Promptfoo)
└── tests/              # Unit and Integration tests
```

## 🚦 Getting Started

1. **Clone the repo**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Setup environment:** Copy `.env.example` to `.env` and add your API keys.
4. **Ingest data:** `python backend/core/ingestion.py`
5. **Launch Backend:** `uvicorn backend.main:app --reload`
6. **Launch Frontend:** `streamlit run frontend/app.py`

---
*Note: This project is designed for enterprise/government standards, prioritizing security and observability.*
