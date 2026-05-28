import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

all_docs = []

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"

# Get all PDFs in the data folder 
pdf_files = data_dir.glob("*.pdf")

for pdf in pdf_files:
    print(f"Loading {pdf.name}...")
    loader = PyPDFLoader(str(pdf))
    docs = loader.load()
    all_docs.extend(docs)

print(f"Loaded {len(all_docs)} pages")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(all_docs)
print(f"Split into {len(chunks)} chunks")

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Initialize ChromaDB
persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")

print(f"Initializing vector store in {persist_directory}...")
# Create an empty vector store first
vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory=persist_directory
)

# Ingest in batches to avoid rate limits
batch_size = 50
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    print(f"Ingesting batch {i//batch_size + 1} ({len(batch)} chunks)...")
    vectorstore.add_documents(batch)
    if i + batch_size < len(chunks):
        print("Sleeping for 65 seconds to respect rate limits...")
        time.sleep(65)

print("Ingestion complete. Vector store saved.")
