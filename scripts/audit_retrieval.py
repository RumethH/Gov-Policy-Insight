import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")

vectorstore = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings
)

query = "NSW Cyber Security Policy"
print(f"Searching for: {query}")
docs = vectorstore.similarity_search(query, k=5)

for i, doc in enumerate(docs):
    print(f"\n--- Result {i+1} ---")
    print(f"Source: {doc.metadata.get('source')}")
    print(f"Content Snippet: {doc.page_content[:200]}...")
