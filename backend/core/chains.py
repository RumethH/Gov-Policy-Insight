import os
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add project root to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import necessary LangChain and other components
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from flashrank import Ranker, RerankRequest

from backend.core.security import SecurityManager
from backend.core.cache import SemanticCache

load_dotenv()

class RAGChain:
    def __init__(self):
        """
        Initialize the RAG components:
        1. LLM (Gemini)
        2. Vector Store (ChromaDB)
        3. Re-ranker (FlashRank)
        4. Security Manager
        5. Semantic Cache
        """
        # 1. Initialize Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

        # 2. Load Vector Store
        self.persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

        # 3. Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0,
            convert_system_message_to_human=True
        )

        # 4. Initialize FlashRank Ranker
        self.ranker = Ranker(cache_dir="flashrank_models")

        # 5. Initialize Security Manager
        self.security = SecurityManager()

        # 6. Initialize Semantic Cache
        self.cache = SemanticCache()

    def rewrite_query(self, query: str, llm=None) -> List[str]:
        """
        Multi-Query approach: Generate multiple versions of the user query to improve retrieval.
        """
        _llm = llm or self.llm
        prompt = ChatPromptTemplate.from_template("""
        You are an AI language model assistant. Your task is to generate five
        different versions of the given user question to retrieve relevant documents from a vector
        database. By generating multiple perspectives on the user question, your goal is to help
        the user overcome some of the limitations of the distance-based similarity search.

        Provide these alternative questions separated by newlines.
        Original question: {question}
        """)

        chain = prompt | _llm
        response = chain.invoke({"question": query})
        
        # Split by newline and clean up
        queries = [q.strip() for q in response.content.split("\n") if q.strip()]
        # Include original query
        if query not in queries:
            queries.append(query)
            
        return queries

    def retrieve_docs(self, query: str, k: int = 10, query_embedding: Optional[List[float]] = None) -> List[Any]:
        """
        Retrieve relevant documents from the vector store.
        """
        if query_embedding:
            return self.vectorstore.similarity_search_by_vector(query_embedding, k=k)
        return self.vectorstore.similarity_search(query, k=k)

    def rerank_docs(self, query: str, docs: List[Any]) -> List[Any]:
        """
        Use FlashRank to re-rank the retrieved documents for better precision.
        """
        if not docs:
            return []

        # Format docs for FlashRank
        passages = []
        for i, doc in enumerate(docs):
            passages.append({
                "id": i,
                "text": doc.page_content,
                "meta": doc.metadata
            })

        rerank_request = RerankRequest(
            query=query,
            passages=passages
        )

        results = self.ranker.rerank(rerank_request)

        # Reconstruct LangChain Document objects from ranked results
        ranked_docs = []
        for res in results:
            ranked_docs.append(Document(
                page_content=res["text"],
                metadata=res["meta"]
            ))
        
        return ranked_docs

    def generate_response(self, query: str, context_docs: List[Any], stream: bool = False, llm=None) -> Any:
        """
        Generate a final response using the retrieved context and a RAG prompt.
        Ensures citations are included.
        """
        context_text = "\n\n".join([
            f"--- Context {i+1} ---\nSource: {doc.metadata.get('source', 'Unknown')}\nPage: {doc.metadata.get('page', 'Unknown')}\nContent: {doc.page_content}"
            for i, doc in enumerate(context_docs)
        ])

        prompt = ChatPromptTemplate.from_template("""
        You are a helpful policy assistant specializing in NSW Government policies. 
        Your goal is to provide accurate information based ONLY on the provided context.

        Instructions:
        1. Use the provided context to answer the question.
        2. If the answer is not in the context, say "I don't know" or "The provided documents do not contain this information." Do not hallucinate.
        3. ALWAYS include citations in your answer using the format [Source, Page X].
        4. Be professional and concise.

        Context:
        {context}

        Question:
        {query}

        Answer:
        """)

        _llm = llm or self.llm
        chain = prompt | _llm

        # Extract unique citations
        citations = []
        seen = set()
        for doc in context_docs:
            source = os.path.basename(doc.metadata.get('source', 'Unknown'))
            page = doc.metadata.get('page', 'Unknown')
            cite_str = f"{source} (Page {page})"
            if cite_str not in seen:
                citations.append({
                    "source": source,
                    "page": page
                })
                seen.add(cite_str)

        if stream:
            return chain.stream({"context": context_text, "query": query}), citations
        else:
            response = chain.invoke({"context": context_text, "query": query})
            return {
                "answer": response.content,
                "citations": citations
            }

    def run(self, query: str, stream: bool = False, api_key: Optional[str] = None) -> Any:
        """
        The main entry point for the RAG pipeline.
        Optimized with parallel retrieval, throttled reranking, and semantic caching.
        If api_key is provided, request-scoped LLM/embedding instances are used for that call.
        """
        import concurrent.futures
        try:
            from google.api_core.exceptions import ResourceExhausted
        except ImportError:
            ResourceExhausted = None  # type: ignore[assignment,misc]

        def _quota_msg(user_key_used: bool) -> str:
            if user_key_used:
                return "Your API key's quota is also exhausted. Please try again later or use a different key."
            return (
                "We've hit our daily demo budget cap! "
                "To continue exploring, paste your own Google Gemini API key in the sidebar."
            )

        def _quota_response(user_key_used: bool):
            msg = _quota_msg(user_key_used)
            if stream:
                def _gen():
                    class Chunk:
                        def __init__(self, c): self.content = c
                    yield Chunk(msg)
                return _gen(), []
            return {"answer": msg, "citations": [], "metadata": {"quota_exceeded": True, "user_key_used": user_key_used}}

        # 0. Security Check (before any LLM or embedding calls)
        if self.security.check_injection(query):
            error_msg = "Potential prompt injection detected. Request denied."
            if stream:
                def error_gen():
                    class Chunk:
                        def __init__(self, c): self.content = c
                    yield Chunk(error_msg)
                return error_gen(), []
            return {
                "answer": error_msg,
                "citations": []
            }

        # Create request-scoped LLM/embeddings when the caller supplies their own API key.
        # When api_key is None, _llm stays None and methods fall back to self.llm internally.
        _llm = None
        _embeddings = self.embeddings
        if api_key:
            _llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                temperature=0,
                google_api_key=api_key,
                convert_system_message_to_human=True,
            )
            _embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=api_key,
            )

        # Pre-compute query embedding once to save API calls
        query_embedding = None
        try:
            query_embedding = _embeddings.embed_query(query)
        except Exception as e:
            if ResourceExhausted and isinstance(e, ResourceExhausted):
                return _quota_response(bool(api_key))
            print(f"⚠️ Embedding generation failed: {e}")

        # 1. Semantic Cache Check
        try:
            cached_response = self.cache.get(query, query_embedding=query_embedding)
            if cached_response:
                if stream:
                    def cache_gen():
                        class Chunk:
                            def __init__(self, c): self.content = c
                        words = cached_response["answer"].split(" ")
                        for i, word in enumerate(words):
                            yield Chunk(word + (" " if i < len(words) - 1 else ""))
                    return cache_gen(), cached_response["citations"]
                return cached_response
        except Exception as e:
            print(f"⚠️ Cache check failed: {e}")

        # 2. Multi-Query Rewrite
        try:
            queries = self.rewrite_query(query, llm=_llm) if _llm else self.rewrite_query(query)
        except Exception as e:
            if ResourceExhausted and isinstance(e, ResourceExhausted):
                return _quota_response(bool(api_key))
            print(f"⚠️ Query rewrite failed: {e}. Falling back to original query.")
            queries = [query]

        # 3. Parallel Retrieval
        all_docs = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for q in queries:
                if q == query and query_embedding:
                    futures.append(executor.submit(self.retrieve_docs, q, k=5, query_embedding=query_embedding))
                else:
                    futures.append(executor.submit(self.retrieve_docs, q, k=5))

            for future in concurrent.futures.as_completed(futures):
                try:
                    all_docs.extend(future.result())
                except Exception as exc:
                    print(f"Query retrieval generated an exception: {exc}")

        # Deduplicate docs based on content
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            if doc.page_content not in seen_content:
                unique_docs.append(doc)
                seen_content.add(doc.page_content)

        # 4. Throttled Re-ranking (Limit input to top 15 docs for speed)
        docs_to_rerank = unique_docs[:15]
        ranked_docs = self.rerank_docs(query, docs_to_rerank)

        # 5. Generate Response with Citations (top 5 re-ranked docs)
        try:
            if stream:
                gen_kwargs = {"llm": _llm} if _llm else {}
                stream_gen, citations = self.generate_response(query, ranked_docs[:5], stream=True, **gen_kwargs)

                def caching_gen():
                    full_answer = ""
                    for chunk in stream_gen:
                        full_answer += chunk.content
                        yield chunk
                    if full_answer.strip():
                        self.cache.set(query, {"answer": full_answer, "citations": citations}, query_embedding=query_embedding)
                    else:
                        print(f"⚠️ Warning: Empty response generated for query '{query}'. Not caching.")

                return caching_gen(), citations
            else:
                gen_kwargs = {"llm": _llm} if _llm else {}
                response = self.generate_response(query, ranked_docs[:5], stream=False, **gen_kwargs)
                if os.getenv("PII_REDACTION_ENABLED", "true").lower() == "true":
                    response["answer"] = self.security.redact_pii(response["answer"])
                if response.get("answer", "").strip():
                    self.cache.set(query, response, query_embedding=query_embedding)
                else:
                    print(f"⚠️ Warning: Empty response generated for query '{query}'. Not caching.")
                return response
        except Exception as e:
            if ResourceExhausted and isinstance(e, ResourceExhausted):
                return _quota_response(bool(api_key))
            raise

if __name__ == "__main__":
    # Quick testing logic
    chain = RAGChain()
    query = "What is the NSW Cyber Security Policy?"
    print(f"\n--- Testing Query: {query} ---\n")

    response = chain.run(query)

    print("ANSWER:")
    print(response["answer"])
    print("\nCITATIONS:")
    for cite in response["citations"]:
        print(f"- {cite['source']} (Page {cite['page']})")
