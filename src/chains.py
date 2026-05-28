import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add project root to sys.path to allow absolute imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary LangChain and other components
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from flashrank import Ranker, RerankRequest

try:
    from src.security import SecurityManager
except ImportError:
    from security import SecurityManager

load_dotenv()

class RAGChain:
    def __init__(self):
        """
        Initialize the RAG components:
        1. LLM (Gemini)
        2. Vector Store (ChromaDB)
        3. Re-ranker (FlashRank)
        4. Security Manager
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
            model="gemini-3.5-flash",
            temperature=0,
            convert_system_message_to_human=True
        )

        # 4. Initialize FlashRank Ranker
        self.ranker = Ranker()

        # 5. Initialize Security Manager
        self.security = SecurityManager()

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

    def retrieve_docs(self, query: str, k: int = 10) -> List[Any]:
        """
        Retrieve relevant documents from the vector store.
        """
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

    def generate_response(self, query: str, context_docs: List[Any]) -> Dict[str, Any]:
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
        response = chain.invoke({"context": context_text, "query": query})

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

        return {
            "answer": response.content,
            "citations": citations
        }

    def run(self, query: str) -> Dict[str, Any]:
        """
        The main entry point for the RAG pipeline.
        """
        # 0. Security Check
        if self.security.check_injection(query):
            return {
                "answer": "Potential prompt injection detected. Request denied.",
                "citations": []
            }
        
        # 1. Multi-Query Rewrite
        queries = self.rewrite_query(query)
        
        # 2. Retrieve Documents for all queries
        all_docs = []
        for q in queries:
            all_docs.extend(self.retrieve_docs(q, k=5))
            
        # Deduplicate docs based on content
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            if doc.page_content not in seen_content:
                unique_docs.append(doc)
                seen_content.add(doc.page_content)
        
        # 3. Re-rank Documents (using original query)
        ranked_docs = self.rerank_docs(query, unique_docs)
        
        # 4. Generate Response with Citations
        # Use top 5 re-ranked docs for generation
        response = self.generate_response(query, ranked_docs[:5])
        
        # 5. Redact PII from response
        if os.getenv("PII_REDACTION_ENABLED", "true").lower() == "true":
            response["answer"] = self.security.redact_pii(response["answer"])
        
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
