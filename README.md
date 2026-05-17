# Gov-Policy-Insight 🏛️

A production-ready RAG (Retrieval-Augmented Generation) application designed for government policy analysis. This project focuses on deterministic evaluation, PII safety, and verifiable citations.

## 🚀 Overview

Gov-Policy-Insight allows users to query complex public policy documents and receive accurate, cited answers. Unlike a standard POC, this system includes:
- **PII Redaction**: Ensuring sensitive data never reaches the LLM.
- **Advanced Retrieval**: Utilizing re-ranking (FlashRank) for higher precision.
- **Deterministic Evals**: Automated testing via `Promptfoo` to measure faithfulness and relevance.
- **Streamlit UI**: A fast, interactive interface for policy researchers.

## 🛠️ Tech Stack

- **Interface:** [Streamlit](https://streamlit.io/)
- **Orchestration:** [LangChain](https://www.langchain.com/)
- **Vector Database:** [ChromaDB](https://www.trychroma.com/)
- **Embeddings/LLM:** Gemini 1.5 Pro / GPT-4o
- **Evaluation:** [Promptfoo](https://www.promptfoo.dev/)
- **Security:** Microsoft Presidio (PII Redaction)

## 📂 Project Structure

```text
gov-policy-insight/
├── data/               # Source PDFs (Public Policies)
├── src/
│   ├── app.py          # Streamlit Application
│   ├── ingestion.py    # PDF Processing & Vector Ingestion
│   ├── chains.py       # RAG Logic & Prompt Templates
│   └── security.py     # PII Redaction & Guardrails
├── evals/              # Promptfoo Eval Suite
├── tests/              # Unit tests
└── requirements.txt    # Python dependencies
```

## 🚦 Getting Started

1. **Clone the repo**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Setup environment:** Copy `.env.example` to `.env` and add your API keys.
4. **Ingest data:** Run `python src/ingestion.py`
5. **Launch App:** `streamlit run src/app.py`

---
*Note: This project is designed for enterprise/government standards, prioritizing security and observability.*
