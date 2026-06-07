import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")

print(f"Loading Chroma from: {persist_directory}")
vectorstore = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings
)

# Access the collection to count documents
collection = vectorstore._collection
count = collection.count()
print(f"Number of documents in collection: {count}")

if count > 0:
    # Peek at some documents
    peek = collection.peek(limit=1)
    print("Peek at first document metadata:")
    print(peek['metadatas'])
