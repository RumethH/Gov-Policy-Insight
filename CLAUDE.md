# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the backend (FastAPI):**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Run the frontend (Streamlit):**
```bash
streamlit run frontend/app.py
```

**Run with Docker Compose (both services together):**
```bash
docker-compose up --build
```

**Ingest PDFs into ChromaDB (must be done before first run):**
```bash
python backend/core/ingestion.py
```

**Run all tests:**
```bash
pytest tests/
```

**Run a specific test category:**
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/security/
pytest tests/hallucination/
pytest -m unit          # by marker
pytest -m "not e2e"    # exclude expensive tests
```

**Run a single test file:**
```bash
pytest tests/unit/test_security_pii_redaction.py -v
```

## Environment Variables

Copy `.env.example` to `.env`. Required keys:
- `GOOGLE_API_KEY` — Gemini LLM and embeddings
- `CHROMA_DB_PATH` — defaults to `./chroma_db`
- `CACHE_DB_PATH` — defaults to `./chroma_db/cache.sqlite` (must be inside the chroma_db volume for Docker)
- `PII_REDACTION_ENABLED` — `true`/`false`, defaults to `true`
- `LANGCHAIN_API_KEY` + `LANGCHAIN_TRACING_V2=true` — optional LangSmith observability
- `CHATGPI_API_BASE_URL` — used by the frontend when `mode == "api"`, defaults to `http://localhost:8000`

## Architecture

The app is a RAG system for querying NSW Government policy PDFs. There are two independent processes: a **FastAPI backend** and a **Streamlit frontend**.

### RAG Pipeline (`backend/core/chains.py` — `RAGChain`)

Every query through `RAGChain.run()` follows this sequence:

1. **Injection check** (`SecurityManager.check_injection`) — blacklist of prompt injection phrases; blocked queries return early.
2. **Embedding** — pre-computes a single query embedding (reused across steps to save API calls).
3. **Semantic cache lookup** (`SemanticCache.get`) — cosine similarity ≥ 0.95 against SQLite-stored embeddings; cache hit skips steps 4–6.
4. **Multi-query rewrite** (`rewrite_query`) — generates 5 query variants via the LLM to broaden retrieval coverage.
5. **Parallel retrieval** — `ThreadPoolExecutor` fetches k=5 docs per query variant from ChromaDB; original query reuses the pre-computed embedding.
6. **Re-ranking** (`rerank_docs`) — FlashRank cross-encoder re-ranks the top 15 unique docs; top 5 pass to generation.
7. **LLM generation** (`generate_response`) — Gemini Flash with a grounded system prompt that enforces `[Source, Page X]` citations.
8. **PII redaction** (`SecurityManager.redact_pii`) — Presidio replaces names, emails, phones, locations, etc., in the final answer.
9. **Cache write** — result stored in SQLite if non-empty.

Streaming is supported throughout: the frontend uses `st.write_stream()` and the chain wraps a `caching_gen()` generator that writes to cache after the stream completes.

### Frontend (`frontend/`)

`frontend/app.py` is the Streamlit entrypoint. It delegates to `frontend/services/chat_service.py`, which defines three service implementations under a common `ChatService` protocol:

- `MockChatService` — static local fallback, no API calls.
- `LocalRAGChatService` — directly imports and calls `RAGChain` in-process; used when `service_mode == "local_rag"`.
- `FastAPIChatService` — HTTP client to the FastAPI backend; used when `service_mode == "api"` (the Docker Compose deployment path).

`build_chat_service(mode)` selects the implementation. In Docker, the frontend container sets `CHATGPI_API_BASE_URL=http://backend:8000` and uses `FastAPIChatService`.

### Ingestion (`backend/core/ingestion.py`)

Run once (or when new PDFs are added to `data/`). Loads all PDFs via `PyPDFLoader`, splits into 1000-char chunks with 200-char overlap, and batches embeddings 50 at a time with 65-second delays (Google AI Free Tier rate limit: 100 RPM). Output persists to `chroma_db/`.

### Security (`backend/core/security.py`)

`SecurityManager` wraps Microsoft Presidio with `en_core_web_sm` (lightweight spaCy model). `check_injection()` is a fast blacklist check. `redact_pii()` replaces entities with typed labels (`[NAME]`, `[EMAIL]`, etc.).

### Semantic Cache (`backend/core/cache.py`)

SQLite-backed. Stores query embeddings as binary blobs; on lookup, computes cosine similarity against all stored embeddings in Python/NumPy. The similarity threshold is 0.95 — intentionally high to avoid false cache hits on policy queries with subtle differences.

### Test Structure

Tests are organized by concern, not by layer:
- `tests/unit/` — isolated chain method tests using `conftest.py`'s `fake_chain` fixture (no real LLM/DB calls).
- `tests/integration/` — component interaction tests (splitter→embeddings, retrieval→rerank→context).
- `tests/e2e/` — full pipeline tests with stubbed LLM; test policy query grounding, ambiguous query refusal, and conflicting doc behavior.
- `tests/security/` — prompt injection, metadata poisoning, malicious ingestion inputs, env secret leakage.
- `tests/hallucination/` — citation presence, retrieval faithfulness, unsupported claims.

The `fake_chain` fixture in `conftest.py` builds a `RAGChain` via `object.__new__()` and monkey-patches all external dependencies (`llm`, `vectorstore`, `embeddings`, `cache`, `ranker`, `security`) with in-memory fakes.

## Key Invariants

- `CACHE_DB_PATH` must resolve to a path **inside the `chroma_db` Docker volume**; otherwise the SQLite file lands in the container's ephemeral filesystem and is lost on restart.
- FlashRank models are cached in `flashrank_models/` at the project root; this directory is not in `.gitignore` so models persist across container rebuilds when the directory is mounted.
- The frontend imports `backend.core.chains` directly in `LocalRAGChatService` — both services must run in the same Python environment for this mode to work.
