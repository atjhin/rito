# Rito - AI Story Generator

An AI-powered story generation platform using League of Legends champions. Built with Flask, LangGraph, and multiple AI providers (Google Gemini, OpenAI, xAI).

## Architecture

This project uses a **microservices architecture** optimized for Google Cloud Run:

```
┌─────────────────────┐         HTTP          ┌─────────────────────┐
│     Flask API       │ ──────────────────►   │   LangGraph         │
│   (Cloud Run)       │                       │   (Cloud Run)       │
│                     │ ◄──────────────────   │                     │
│  • Frontend UI      │      JSON Response    │  • Story Generation │
│  • Input Validation │                       │  • AI Agents        │
│  • User Requests    │                       │  • Checkpoints      │
└─────────────────────┘                       └─────────────────────┘
         ▲                                              │
         │                                              │
         │                                              ▼
    ┌─────────┐                                  ┌─────────────┐
    │  User   │                                  │  AWS S3     │
    │ Browser │                                  │  (Storage)  │
    └─────────┘                                  └─────────────┘
```

### Why Microservices?

1. **Independent Scaling** - LangGraph is compute-intensive, Flask is lightweight
2. **Cost Optimization** - Scale LangGraph only when processing stories
3. **Deployment Flexibility** - Update frontend without redeploying AI backend
4. **Fault Isolation** - Issues in one service don't crash the other

## Project Structure

```
rito/
├── services/
│   ├── api/                    # Flask API Service
│   │   ├── src/
│   │   │   ├── app.py          # Flask application factory
│   │   │   ├── routes.py       # API routes
│   │   │   └── config.py       # Configuration
│   │   ├── static/             # CSS, JS assets
│   │   ├── templates/          # HTML templates
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── wsgi.py
│   │
│   └── langgraph/              # LangGraph Service
│       ├── src/
│       │   ├── main.py         # FastAPI application
│       │   ├── agents/         # AI agents
│       │   ├── core/           # Story orchestration
│       │   ├── config/         # LLM configuration
│       │   ├── schemas/        # Data models
│       │   └── services/       # S3 integration
│       ├── data/               # Champions data
│       ├── Dockerfile
│       └── requirements.txt
│
├── docker-compose.yml          # Local development
├── cloudbuild.yaml             # GCP Cloud Build CI/CD
├── deploy.sh                   # Manual deployment script
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud SDK (for deployment)
- API Keys: Google AI, OpenAI, xAI (optional)

### 1. Local Development with Docker Compose

```bash
# Clone the repository
git clone https://github.com/yourusername/rito.git
cd rito

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Start both services
docker-compose up --build

# Access the application
open http://localhost:5000
```

### 2. Local Development without Docker

**Terminal 1 - LangGraph Service:**
```bash
cd services/langgraph
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8080
```

**Terminal 2 - Flask API:**
```bash
cd services/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export LANGGRAPH_SERVICE_URL=http://localhost:8080
flask run --port 5000
```

## Deployment to Google Cloud Run

### Option 1: Using the Deploy Script

```bash
# Set environment variables
export GOOGLE_API_KEY=your_key
export OPENAI_API_KEY=your_key
export XAI_API_KEY=your_key
export S3_ACCESS_KEY=your_key
export S3_SECRET_KEY=your_key
export S3_REGION=us-east-1
export S3_BUCKET=your_bucket

# Deploy
./deploy.sh your-project-id us-central1
```

### Option 2: Using Cloud Build (CI/CD)

1. **Set up Cloud Build trigger:**
   - Go to Cloud Build > Triggers > Create Trigger
   - Connect your repository
   - Use `cloudbuild.yaml` as the configuration file

2. **Configure substitution variables:**
   ```
   _GOOGLE_API_KEY: your_key
   _OPENAI_API_KEY: your_key
   _XAI_API_KEY: your_key
   _S3_ACCESS_KEY: your_key
   _S3_SECRET_KEY: your_key
   _S3_REGION: us-east-1
   _S3_BUCKET: your_bucket
   _REGION: us-central1
   ```

3. **Push to trigger deployment:**
   ```bash
   git push origin main
   ```

### Option 3: Manual Deployment

**Step 1: Deploy LangGraph Service**
```bash
cd services/langgraph

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rito-langgraph

# Deploy to Cloud Run (internal only)
gcloud run deploy rito-langgraph \
  --image gcr.io/YOUR_PROJECT_ID/rito-langgraph \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --no-allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=$GOOGLE_API_KEY,XAI_API_KEY=$XAI_API_KEY"

# Get the service URL
LANGGRAPH_URL=$(gcloud run services describe rito-langgraph \
  --region us-central1 --format 'value(status.url)')
```

**Step 2: Deploy API Service**
```bash
cd services/api

# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rito-api

# Deploy to Cloud Run (public)
gcloud run deploy rito-api \
  --image gcr.io/YOUR_PROJECT_ID/rito-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "LANGGRAPH_SERVICE_URL=$LANGGRAPH_URL,GOOGLE_API_KEY=$GOOGLE_API_KEY"
```

**Step 3: Set up Service-to-Service Authentication**
```bash
# Get the API service account
API_SA=$(gcloud run services describe rito-api \
  --region us-central1 \
  --format 'value(spec.template.spec.serviceAccountName)')

# Grant API permission to invoke LangGraph
gcloud run services add-iam-policy-binding rito-langgraph \
  --region us-central1 \
  --member "serviceAccount:$API_SA" \
  --role "roles/run.invoker"
```

## API Endpoints

### Flask API Service (Port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/health` | GET | Health check |
| `/submit-data` | POST | Submit story generation request |

### LangGraph Service (Port 8080)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/generate` | POST | Generate story |

## Environment Variables

### API Service
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key | Yes |
| `LANGGRAPH_SERVICE_URL` | URL of LangGraph service | Yes |
| `LANGGRAPH_TIMEOUT` | Request timeout (seconds) | No (default: 300) |

### LangGraph Service
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | No |
| `XAI_API_KEY` | xAI (Grok) API key | No |
| `S3_ACCESS_KEY` | AWS S3 access key | Yes |
| `S3_SECRET_KEY` | AWS S3 secret key | Yes |
| `S3_REGION` | AWS region | Yes |
| `S3_BUCKET` | S3 bucket name | Yes |

## Cloud Run Configuration

### LangGraph Service (Compute-Intensive)
- **Memory:** 2Gi
- **CPU:** 2
- **Timeout:** 600s (10 minutes)
- **Concurrency:** 10
- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 5
- **Authentication:** Internal only

### API Service (Lightweight)
- **Memory:** 512Mi
- **CPU:** 1
- **Timeout:** 120s
- **Concurrency:** 80
- **Min Instances:** 0
- **Max Instances:** 10
- **Authentication:** Public

## Cost Optimization Tips

1. **Use Cloud Run min-instances=0** - Scale to zero when not in use
2. **Configure appropriate concurrency** - LangGraph handles fewer concurrent requests
3. **Use committed use discounts** for sustained workloads
4. **Monitor with Cloud Monitoring** to right-size resources

## Troubleshooting

### "Connection refused" to LangGraph service
- Ensure LangGraph service is running
- Check `LANGGRAPH_SERVICE_URL` is correct
- Verify service-to-service authentication is set up

### Story generation timeout
- Increase `LANGGRAPH_TIMEOUT` environment variable
- Check Cloud Run timeout settings
- Consider using async/streaming for long operations

### Service not scaling
- Check Cloud Run logs for errors
- Verify health check endpoints are responding
- Review min/max instance settings

## License

MIT License
