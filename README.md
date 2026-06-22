# Gov-Policy-Insight 🏛️

A production-ready RAG (Retrieval-Augmented Generation) application designed for government policy analysis. This project focuses on deterministic evaluation, PII safety, and verifiable citations.

**[Live Demo](https://chat-gpi.com)**

## 🚀 Overview

Gov-Policy-Insight allows users to query complex public policy documents and receive accurate, cited answers. Unlike a standard POC, this system includes:
- **PII Redaction**: Ensuring sensitive data never reaches the LLM via Microsoft Presidio.
- **Semantic Caching**: High-performance caching using embedding similarity to reduce API costs.
- **Parallel Retrieval**: Multi-query retrieval optimized with concurrency.
- **Streamlit UI**: A fast, interactive interface for policy researchers.
- **FastAPI Backend**: A robust REST API for serving the RAG pipeline.

## 🛠️ Tech Stack

- **Cloud:** AWS EC2 & Docker Compose
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

### 1. Prerequisites
- Python 3.10+
- [Google AI API Key](https://aistudio.google.com/app/apikey) (for Gemini 1.5 Flash)

### 2. Local Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/gov-policy-insight.git
   cd gov-policy-insight
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the example file and add your keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

### 3. Ingest Policy Documents
Before querying, you need to vectorize the PDFs in the `data/` directory:
```bash
python backend/core/ingestion.py
```

### 4. Running the Application
You can run the application using two terminal windows:

**Terminal 1 (Backend):**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
streamlit run frontend/app.py
```

---

## 🐳 Running with Docker

The easiest way to get everything running in a production-like environment:

```bash
docker-compose up --build
```
- **UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

---

## ☁️ Deployment (AWS EC2)

The application is currently deployed on an **AWS EC2 instance (`t2.micro`/`t3.micro`)** running Docker Compose.

- **Current Demo URL:** [http://3.27.134.224:8501/](http://3.27.134.224:8501/)

⚠️ **Security Warning:**
The current live deployment is accessed via a raw public IPv4 address over unencrypted HTTP (`http://`). This is **potentially risky** and not recommended for production because:
1. **No Encryption (Unsecured HTTP):** Chat queries, system inputs, and metadata travel across the network in plain text, making them vulnerable to interception.
2. **IP Ephemerality:** If the EC2 instance is stopped and restarted, the public IP address will change, breaking the URL.
3. **Browser Warnings:** Visitors will see a "Not Secure" warning in their address bar.

### 🛡️ Planned Security Improvements
To secure the application for public sharing, we are evaluating the following production-ready options:
- **Option 1: Cloudflare Tunnel (Highly Recommended & Cost-Effective):** Secures the application behind a custom domain with automatic HTTPS/SSL without opening any inbound ports on the EC2 security group.
- **Option 2: Dockerized Caddy Server Reverse Proxy:** Setting up Caddy in Docker alongside an Elastic IP and domain name. Caddy will automatically provision and renew Let's Encrypt HTTPS certificates for free.
- **Option 3: DuckDNS + Caddy Reverse Proxy:** A completely free solution to obtain a custom subdomain (`yourdomain.duckdns.org`) with automated SSL certification if buying a custom domain is not desired.
- **Option 4: AWS Application Load Balancer (ALB) + ACM:** Routing traffic through an AWS ALB with a free SSL certificate from AWS Certificate Manager (subject to AWS ALB hourly billing).

For detailed instructions on launching and configuring the server, refer to [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md).

---

## 📖 Usage Guide

### Using the Web Interface
1. Open http://localhost:8501 in your browser.
2. Select the **Service Mode** (Local RAG or Mock) in the sidebar.
3. Type a policy question (e.g., *"What are the cyber incident reporting requirements for NSW agencies?"*).
4. View the generated response along with **Citations** that link directly to the source PDFs.

### Using the API
The backend provides a RESTful interface for the RAG pipeline:
- **POST `/chat`**: Send a query to the RAG system.
  ```json
  {
    "prompt": "Your question here",
    "conversation_id": "unique-id",
    "stream": false
  }
  ```
- **POST `/chat/greeting`**: Get a professional welcome message.

### Running Tests
To ensure everything is working correctly:
```bash
pytest tests/
```

---
*Note: This project is designed for enterprise/government standards, prioritizing security and observability.*
