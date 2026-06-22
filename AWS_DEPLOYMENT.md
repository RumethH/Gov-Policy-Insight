# AWS EC2 Production Deployment Guide 🚀

This guide explains how to deploy the **Gov-Policy-Insight** application to an Amazon EC2 instance, secure it behind an **Nginx Reverse Proxy**, configure **SSL/TLS certificates with Certbot**, and restrict public network access for enterprise-grade security.

## 🏗️ Architecture Overview
- **Compute:** Amazon EC2 (`t2.micro` or `t3.micro` - Free Tier eligible).
- **Domain:** `chat-gpi.com`
- **Reverse Proxy:** Nginx (running on the host) serving SSL termination.
- **SSL Certificates:** Certbot (Let's Encrypt) with automated renewal.
- **Orchestration:** `docker-compose` running on an isolated virtual bridge network.
- **Persistence:** ChromaDB and SQLite cache files are stored on persistent host volumes.

---

## 🚦 Prerequisites
1. **AWS Account** with Free Tier eligibility.
2. **Custom Domain:** (e.g., `chat-gpi.com`) configured with DNS `A` records pointing to your EC2 instance's public IP address (both `@` and `www`).
3. **Google AI API Key** (Gemini).

---

## 🛠️ Deployment Steps

### 1. Launch an EC2 Instance & Configure Security Group
1. Go to the [EC2 Console](https://console.aws.amazon.com/ec2/).
2. Click **Launch instances**.
3. **AMI (Amazon Machine Image):** Select **Ubuntu Server 24.04 LTS** (Free tier eligible).
4. **Instance Type:** `t2.micro` or `t3.micro`.
5. **Key Pair:** Select or create your SSH key pair.
6. **Network Settings (Security Group):**
   Create a new Security Group and configure the following rules:
   - **SSH (Port 22):** Source: My IP (highly recommended) or Anywhere.
   - **HTTP (Port 80):** Source: Anywhere (`0.0.0.0/0`) — used for HTTP traffic and Certbot verification.
   - **HTTPS (Port 443):** Source: Anywhere (`0.0.0.0/0`) — used for secure user traffic.
   *(Note: Do NOT open ports 8000 or 8501 to the public. These will remain internal and completely isolated from the internet.)*
7. **Storage:** Allocate up to **30 GB** of `gp3` storage (Free Tier eligible).
8. Launch the instance.

### 2. Connect to Your Instance & Install Docker
SSH into your instance:
```bash
chmod 400 gov-policy-key.pem
ssh -i "gov-policy-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>
```

Update system packages and install Docker:
```bash
# Update packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker & Docker Compose V2
sudo apt-get install -y docker.io docker-compose-v2

# Grant ubuntu user Docker permissions (requires shell reconnect)
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Clone Repository & Setup Environments
Clone the codebase and navigate to the directory:
```bash
git clone <YOUR_REPOSITORY_URL>
cd Gov-Policy-Insight

# Setup your environment variables
cp .env.example .env
nano .env
```

Configure your `.env` file with the following production values:
```env
GOOGLE_API_KEY="your-gemini-api-key-here"

# Since Streamlit runs on the server and communicates with FastAPI internally via Docker Compose,
# we use the internal service hostname rather than the public IP.
CHATGPI_API_BASE_URL="http://backend:8000"

# Production analytics and tracing (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY="your-langchain-key"
```

### 4. Start the Application Containers
Run the Docker Compose containers in detached mode:
```bash
docker compose up -d --build
```
*At this point, Streamlit is running internally on port `8501` and FastAPI on port `8000`. Neither is accessible from the internet yet.*

### 5. Install Nginx & Provision Let's Encrypt SSL with Certbot
Install Nginx and the Certbot plugin on the host OS:
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Obtain the SSL certificate (replace `chat-gpi.com` with your actual domain):
```bash
sudo certbot --nginx -d chat-gpi.com -d www.chat-gpi.com
```
*Follow the interactive prompts to enter your email and accept the terms. Certbot will automatically verify ownership via port 80 and generate valid TLS certificates.*

### 6. Configure Nginx as a Secure Reverse Proxy
Open the Nginx default configuration file:
```bash
sudo nano /etc/nginx/sites-available/default
```

Replace the file contents with the following production-hardened configuration. This proxies traffic to Streamlit (port `8501`) and sets up required WebSocket header variables:

```nginx
server {
    listen 80;
    server_name chat-gpi.com www.chat-gpi.com;
    
    # Force HTTP to HTTPS redirection
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name chat-gpi.com www.chat-gpi.com;

    # SSL Certificates managed by Certbot
    ssl_certificate /etc/letsencrypt/live/chat-gpi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat-gpi.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security Headers
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval';";

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (Required for Streamlit live state-sync)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

Verify the Nginx configuration and reload the service:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Verify Deployment & Automated Renewal
- **Access the Secure Site:** Visit `https://chat-gpi.com` in your browser. You should see a lock icon showing a secure HTTPS connection.
- **API Isolation:** Try to visit `http://chat-gpi.com:8000/docs` or `http://chat-gpi.com:8501`. They should time out because those ports are completely blocked at the AWS Security Group layer.
- **SSL Auto-Renewal Test:** Let's Encrypt certificates are valid for 90 days. Certbot installs a systemd timer that automatically checks and renews certificates. Verify it works with a dry run:
  ```bash
  sudo certbot renew --dry-run
  ```

---

## 💡 Operational & Maintenance Commands

- **Check Logs:**
  ```bash
  # Docker container logs
  docker compose logs -f
  
  # Host Nginx logs
  sudo tail -f /var/log/nginx/error.log
  ```
- **App Updates:**
  When pushing new code, log in to the server and rebuild the containers:
  ```bash
  git pull
  docker compose up -d --build
  ```
