# Physical Assessment Monitoring System - Backend

## 📌 Citation
If you use this software in your project or research, please cite it as follows:

> **Huaman Alvarado, F. A. (2025).** *Physical Assessment Scores Monitoring System - Backend (Version 1.0.0) [Software].* Zenodo. https://doi.org/10.5281/zenodo.17755545

**BibTeX:**
```bibtex
@software{app_tesis_backend,
  author       = {Huaman Alvarado, Flavio Angello},
  title        = {Physical Assessment Scores Monitoring System - Backend},
  year         = 2025,
  publisher    = {Zenodo},
  version      = {v1.0.0},
  doi          = {10.5281/zenodo.17755545}
}
```

## 📝 Description

This repository contains the server-side source code, Artificial Intelligence models, and infrastructure configuration for the thesis project: **"IMPLEMENTACIÓN DE UNA HERRAMIENTA DE MONITOREO DE CORRECCIÓN DE EVALUACIONES FÍSICAS EN UNA UNIVERSIDAD EMPLEANDO APRENDIZAJE DE MÁQUINA"**.

The system implements a RESTful architecture designed for cost-efficiency and performance on limited cloud resources.

**Key Technologies:**

  * **API Framework:** FastAPI (Python 3.11) with Uvicorn.
  * **Database:** MySQL (managed via SQLAlchemy ORM).
  * **Computer Vision Pipeline:**
      * **Detection:** YOLOv8n (Ultralytics) for locating scores.
      * **Classification:** ResNet-18 (PyTorch) for handwritten digit classification.
  * **Infrastructure:** Docker, Docker Compose, and Caddy (Reverse Proxy with automatic HTTPS).

## ⚙️ External Services Configuration

Before deploying, ensure you have the following external services provisioned:

### 1\. AWS Services

  * **S3 Bucket:** Create a bucket for storing temporary video uploads.
      * Policy: Ensure the IAM user has `PutObject`, `GetObject`, `DeleteObject` and `ListBucket` permissions.
  * **EC2 Instance:** Tested on `t3.medium` (Amazon Linux 2023). Requires 4GB Swap configuration for ML models loading.
  * **RDS:** Use an AWS RDS MySQL instance.

### 2\. Google Firebase

  * Create a project in the Firebase Console.
  * Generate a **Service Account Key** (`.json`) for backend authentication verification.
  * Rename this file to `serviceAccountKey.json` and place it in a `secrets/` folder (see Deployment).

### 3\. DNS Provider

  * A domain is required for HTTPS (Caddy).
  * Point your domain (e.g., via AWS Route 53) to the server's Elastic IP.

## 🚀 Deployment Guide

### Prerequisites

  * Docker (v25.0.13+) & Docker Compose (v2.27+).
  * Make (optional, for convenience commands).

### 1\. Installation

Clone the repository and enter the directory:

```bash
git clone https://github.com/U20212419/app_tesis_backend.git
cd app_tesis_backend
```

### 2\. File Setup

Create the required directories and configuration files that are excluded from version control:

**A. Secrets Directory**

```bash
mkdir -p secrets/
# Place your 'serviceAccountKey.json' inside this folder
```

**B. Environment Variables**
Create a `.env.production` file in the root directory:

```env
# Enable if debugging is needed
DEBUG=False

# Database configuration
DB_USER=<YOUR_USERNAME>
DB_PASSWORD=<YOUR_PASSWORD>
DB_HOST=<YOUR_HOST>
DB_PORT=<YOUR_PORT>
DB_NAME=<YOUR_DATABASE>

# Firebase authentication configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/serviceAccountKey.json

# If you change the log directory, remember to add the path in .gitignore
LOG_DIR=/app/logs

# AWS configuration
AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>
AWS_REGION=<YOUR_AWS_REGION>

# S3 Bucket configuration
S3_BUCKET_NAME=<YOUR_S3_BUCKET_NAME>
```

**C. Caddyfile (DNS)**
Update the `Caddyfile` with your actual domain:

```text
<YOUR_DOMAIN> {
    reverse_proxy api:8000
}
```

### 3\. Build and Run

Standard PyTorch installations include CUDA (GPU) support by default, which results in large image sizes (>6GB).

For CPU-only environments (like AWS t3.medium), this repository includes an optimized requirements file to prevent "No space left on device" errors.

1.  **Select your configuration:**

      * **For GPU (Default):** Do nothing. The standard `requirements.txt` is ready.
      * **For CPU (Optimized):** Overwrite the standard file with the CPU version before building:
        ```bash
        cp -f requirements.cpu requirements.txt
        ```

2.  **Start the server:**

    ```bash
    # Build the Docker image
    make docker-build

    # Start services in detached mode
    make docker-run

    # View logs
    make docker-logs
    ```

The API will be available at `https://<YOUR_DOMAIN>/docs`.