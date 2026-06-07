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

    def rewrite_query(self, query: str) -> List[str]:
        """
        Multi-Query approach: Generate multiple versions of the user query to improve retrieval.
        """
        prompt = ChatPromptTemplate.from_template("""
        You are an AI language model assistant. Your task is to generate five 
        different versions of the given user question to retrieve relevant documents from a vector 
        database. By generating multiple perspectives on the user question, your goal is to help
        the user overcome some of the limitations of the distance-based similarity search. 

        Provide these alternative questions separated by newlines.
        Original question: {question}
        """)

        chain = prompt | self.llm
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

    def generate_response(self, query: str, context_docs: List[Any], stream: bool = False) -> Any:
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

        chain = prompt | self.llm
        
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

    def run(self, query: str, stream: bool = False) -> Any:
        """
        The main entry point for the RAG pipeline.
        Optimized with parallel retrieval, throttled reranking, and semantic caching.
        """
        import concurrent.futures

        # 0. Security Check
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
        
        # Pre-compute query embedding once to save API calls
        try:
            query_embedding = self.embeddings.embed_query(query)
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            query_embedding = None

        # 1. Semantic Cache Check
        try:
            cached_response = self.cache.get(query, query_embedding=query_embedding)
            if cached_response:
                if stream:
                    def cache_gen():
                        class Chunk:
                            def __init__(self, c): self.content = c
                        # Split into small chunks to simulate typing feel
                        words = cached_response["answer"].split(" ")
                        for i, word in enumerate(words):
                            yield Chunk(word + (" " if i < len(words) - 1 else ""))
                    return cache_gen(), cached_response["citations"]
                return cached_response
        except Exception as e:
            print(f"⚠️ Cache check failed: {e}")
        
        # 2. Multi-Query Rewrite
        try:
            queries = self.rewrite_query(query)
        except Exception as e:
            print(f"⚠️ Query rewrite failed: {e}. Falling back to original query.")
            queries = [query]
        
        # 3. Parallel Retrieval
        all_docs = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map retrieval tasks across all queries
            futures = []
            for q in queries:
                if q == query and query_embedding:
                    # Reuse pre-computed embedding for original query
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
        
        # 5. Generate Response with Citations
        # Use top 5 re-ranked docs for generation
        if stream:
            stream_gen, citations = self.generate_response(query, ranked_docs[:5], stream=True)
            
            # We'll need a wrapper to capture the full response and cache it
            def caching_gen():
                full_answer = ""
                for chunk in stream_gen:
                    full_answer += chunk.content
                    yield chunk
                # Cache the complete result after stream ends, if it's not empty
                if full_answer.strip():
                    self.cache.set(query, {"answer": full_answer, "citations": citations}, query_embedding=query_embedding)
                else:
                    print(f"⚠️ Warning: Empty response generated for query '{query}'. Not caching.")
            
            return caching_gen(), citations
        else:
            response = self.generate_response(query, ranked_docs[:5], stream=False)
            # Redact PII from response
            if os.getenv("PII_REDACTION_ENABLED", "true").lower() == "true":
                response["answer"] = self.security.redact_pii(response["answer"])
            
            # Cache the result if not empty
            if response.get("answer", "").strip():
                self.cache.set(query, response, query_embedding=query_embedding)
            else:
                print(f"⚠️ Warning: Empty response generated for query '{query}'. Not caching.")
            return response

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
