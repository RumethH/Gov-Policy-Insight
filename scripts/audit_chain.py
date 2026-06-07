import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.chains import RAGChain

load_dotenv()

chain = RAGChain()
query = "What is the NSW Cyber Security Policy?"

print(f"\n--- Testing Query: {query} ---\n")

# Manually step through to see what happens
queries = chain.rewrite_query(query)
print(f"Rewritten queries: {queries}")

all_docs = []
for q in queries:
    docs = chain.retrieve_docs(q, k=5)
    all_docs.extend(docs)

unique_docs = []
seen_content = set()
for doc in all_docs:
    if doc.page_content not in seen_content:
        unique_docs.append(doc)
        seen_content.add(doc.page_content)

print(f"Total unique docs retrieved: {len(unique_docs)}")

ranked_docs = chain.rerank_docs(query, unique_docs)
print(f"Total docs after reranking: {len(ranked_docs)}")

top_docs = ranked_docs[:5]
context_text = "\n\n".join([
    f"--- Context {i+1} ---\nSource: {doc.metadata.get('source', 'Unknown')}\nPage: {doc.metadata.get('page', 'Unknown')}\nContent: {doc.page_content}"
    for i, doc in enumerate(top_docs)
])

print("\n--- CONTEXT SENT TO LLM ---")
print(context_text)

response = chain.generate_response(query, top_docs)

print("\n--- LLM ANSWER ---")
print(response["answer"])
