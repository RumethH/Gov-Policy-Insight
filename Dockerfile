# Use a slim Python image for a smaller footprint
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - build-essential: required for some python packages
# - curl: for healthchecks
# - libmagic1: for file type detection
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create directory for ChromaDB if it doesn't exist
RUN mkdir -p chroma_db

# Default environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROMA_DB_PATH=/app/chroma_db

# The specific command (FastAPI or Streamlit) should be provided 
# via the container orchestration (Docker Compose or k8s)
EXPOSE 8000 8501

# No fixed ENTRYPOINT so we can override it easily for backend vs frontend
CMD ["python", "backend/main.py"]
