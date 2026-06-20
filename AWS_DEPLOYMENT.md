# AWS EC2 Free-Tier Deployment Guide 🚀

This guide explains how to deploy the **Gov-Policy-Insight** application to an Amazon EC2 instance using the AWS Free Tier. We will use Docker Compose to orchestrate both the FastAPI backend and Streamlit frontend. 

Since App Runner is in maintenance mode and ECS Fargate falls outside standard free tier usage quickly, this EC2 + Docker Compose approach is the most cost-effective method to host the app.

## 🏗️ Architecture Overview
- **Compute:** Amazon EC2 (`t2.micro` or `t3.micro` - Free Tier eligible).
- **Orchestration:** `docker-compose` running directly on the instance.
- **Persistence:** ChromaDB and cache files are stored directly on the EC2 attached EBS volume.

---

## 🚦 Prerequisites
1.  **AWS Account** with Free Tier eligibility (750 hours/month of `t2.micro`/`t3.micro`, 30 GB EBS gp3 storage).
2.  **Google AI API Key** (Gemini).

---

## 🛠️ Deployment Steps

### 1. Launch an EC2 Instance
1. Go to the [AWS EC2 Console](https://console.aws.amazon.com/ec2/).
2. Click **Launch instances**.
3. **Name:** `gov-policy-insight-server`.
4. **AMI (Amazon Machine Image):** Select **Ubuntu Server 24.04 LTS** (or 22.04 LTS). Ensure it has the "Free tier eligible" badge.
5. **Instance Type:** Select `t2.micro` (or `t3.micro` depending on your region's free tier offering).
6. **Key Pair:** Create a new key pair (e.g., `gov-policy-key`), download the `.pem` file, and keep it safe.
7. **Network Settings:**
   - Create a new Security Group.
   - **Allow SSH traffic from:** Anywhere (or specifically your IP for better security).
   - **Custom TCP Rules:** Click "Edit" network settings, add two Custom TCP rules:
     - Port Range: `8000` (Backend API) -> Source: Anywhere (0.0.0.0/0)
     - Port Range: `8501` (Frontend UI) -> Source: Anywhere (0.0.0.0/0)
8. **Storage:** Allocate up to **30 GB** of `gp3` storage (The AWS Free tier includes up to 30 GB of EBS).
9. Click **Launch instance**.

### 2. Connect to Your Instance
Open your local terminal and SSH into the instance using the downloaded `.pem` key:
```bash
# Secure the key file
chmod 400 gov-policy-key.pem

# Connect (replace with your instance's Public IPv4 address)
ssh -i "gov-policy-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### 3. Install Docker and Docker Compose
Run the following commands on your EC2 instance to set up the Docker environment:
```bash
# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io

# Add ubuntu user to the docker group to run docker without sudo
sudo usermod -aG docker $USER

# Install Docker Compose (V2)
sudo apt-get install -y docker-compose-v2
```
*Note: After running the `usermod` command, either run `newgrp docker` to apply the group changes to your current session immediately, or log out of the server (`exit`) and SSH back in for the permissions to take effect.*

### 4. Clone the Repository and Configure
Once reconnected, clone your source code onto the server:
```bash
git clone <YOUR_REPOSITORY_URL>
cd Gov-Policy-Insight

# Setup your environment variables
cp .env.example .env
nano .env 
```

**CRITICAL:** Update your `.env` file to include your Google API Key and explicitly define the Backend URL so the frontend browser can reach it.
```env
GOOGLE_API_KEY="your-gemini-api-key-here"

# The frontend runs in the user's browser, so it needs the Public IP of your EC2 instance
# Replace <YOUR_EC2_PUBLIC_IP> with your actual IP address.
CHATGPI_API_BASE_URL="http://<YOUR_EC2_PUBLIC_IP>:8000"

# Optional: Add LangChain tracing if you are using it
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY="your-langchain-key"
```

### 5. Start the Application
Start the application in detached mode using Docker Compose:
```bash
docker compose up -d --build
```
*Docker will now download the base images, build the frontend and backend containers, and start them up. This might take a few minutes on a `t2.micro` instance.*

### 6. Access the Application
- **Frontend (Streamlit UI):** `http://<YOUR_EC2_PUBLIC_IP>:8501`
- **Backend (FastAPI Docs):** `http://<YOUR_EC2_PUBLIC_IP>:8000/docs`

---
## 💡 Cost Management & Operations

- **Public IPv4 Cost:** As of 2024, AWS charges ~$3.60/month for public IPv4 addresses, which is **not** covered by the compute free tier. If your account is newly created (post-July 2025), your initial $200 credits will cover this.
- **Stop When Inactive:** If this is just a demo, stop the instance from the EC2 console when you aren't using it. (EBS storage is still continually billed against your 30GB limit, but compute hours will stop accumulating).
- **Viewing Logs:** If you need to debug issues, use:
  ```bash
  docker compose logs -f
  ```
- **Updating the App:** When you push new code to your repository, pull it down to the server and rebuild:
  ```bash
  git pull
  docker compose up -d --build
  ```
