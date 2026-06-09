# AWS App Runner Deployment Guide 🚀

This guide explains how to deploy the **Gov-Policy-Insight** application to AWS App Runner. This setup uses a unified container approach, running both the FastAPI backend and Streamlit frontend in a single App Runner service for maximum cost-efficiency.

## 🏗️ Architecture Overview
- **Service:** AWS App Runner (Serverless Containers).
- **Registry:** AWS ECR (Elastic Container Registry).
- **Process Manager:** `supervisord` (runs Backend & Frontend in one container).
- **Persistence:** ChromaDB state is "baked" into the image for the demo.

---

## 🚦 Prerequisites
1.  **AWS CLI** installed and configured (`aws configure`).
2.  **Docker** installed and running.
3.  **Google AI API Key** (Gemini).

---

## 🛠️ Deployment Steps

### 1. Create an ECR Repository
First, create a repository in AWS to host your Docker image:
```bash
aws ecr create-repository --repository-name gov-policy-insight --region your-region
```

### 2. Authenticate Docker to ECR
```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
```

### 3. Build and Tag the Production Image
```bash
docker build -t gov-policy-insight -f Dockerfile.prod .
docker tag gov-policy-insight:latest your-account-id.dkr.ecr.your-region.amazonaws.com/gov-policy-insight:latest
```

### 4. Push the Image to ECR
```bash
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/gov-policy-insight:latest
```

### 5. Create the App Runner Service
1.  Go to the [AWS App Runner Console](https://console.aws.amazon.com/apprunner/).
2.  Click **Create service**.
3.  **Source:** Container registry -> Amazon ECR.
4.  **Container image URI:** Browse and select the `gov-policy-insight` image you just pushed.
5.  **Service settings:**
    - **Port:** 8501 (This is the Streamlit port).
    - **Environment Variables:** Add `GOOGLE_API_KEY`.
6.  **Review and Create.**

---
*Note: Ensure your `chroma_db/` folder contains your ingested data before building the image if you want it to be available on launch.*
