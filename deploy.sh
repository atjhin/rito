#!/bin/bash
# Cloud Run Deployment Script
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-us-central1}

echo "=========================================="
echo "Deploying Rito to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "=========================================="

# Check if required environment variables are set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable is not set"
    exit 1
fi

# ==========================================
# Step 1: Build and Deploy LangGraph Service
# ==========================================
echo ""
echo "Step 1: Building and deploying LangGraph service..."

cd services/langgraph

# Build the Docker image
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/rito-langgraph \
    --project $PROJECT_ID

# Deploy to Cloud Run (internal service, not publicly accessible)
gcloud run deploy rito-langgraph \
    --image gcr.io/$PROJECT_ID/rito-langgraph \
    --platform managed \
    --region $REGION \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --concurrency 10 \
    --min-instances 0 \
    --max-instances 5 \
    --no-allow-unauthenticated \
    --set-env-vars "GOOGLE_API_KEY=$GOOGLE_API_KEY" \
    --set-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY" \
    --set-env-vars "XAI_API_KEY=$XAI_API_KEY" \
    --set-env-vars "S3_ACCESS_KEY=$S3_ACCESS_KEY" \
    --set-env-vars "S3_SECRET_KEY=$S3_SECRET_KEY" \
    --set-env-vars "S3_REGION=$S3_REGION" \
    --set-env-vars "S3_BUCKET=$S3_BUCKET" \
    --project $PROJECT_ID

# Get the LangGraph service URL
LANGGRAPH_URL=$(gcloud run services describe rito-langgraph \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' \
    --project $PROJECT_ID)

echo "LangGraph service deployed at: $LANGGRAPH_URL"

cd ../..

# ==========================================
# Step 2: Build and Deploy API Service
# ==========================================
echo ""
echo "Step 2: Building and deploying API service..."

cd services/api

# Build the Docker image
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/rito-api \
    --project $PROJECT_ID

# Deploy to Cloud Run (publicly accessible)
gcloud run deploy rito-api \
    --image gcr.io/$PROJECT_ID/rito-api \
    --platform managed \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --timeout 120 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_API_KEY=$GOOGLE_API_KEY" \
    --set-env-vars "LANGGRAPH_SERVICE_URL=$LANGGRAPH_URL" \
    --set-env-vars "LANGGRAPH_TIMEOUT=300" \
    --project $PROJECT_ID

# Get the API service URL
API_URL=$(gcloud run services describe rito-api \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' \
    --project $PROJECT_ID)

cd ../..

# ==========================================
# Step 3: Set up service-to-service auth
# ==========================================
echo ""
echo "Step 3: Setting up service-to-service authentication..."

# Get the API service account
API_SERVICE_ACCOUNT=$(gcloud run services describe rito-api \
    --platform managed \
    --region $REGION \
    --format 'value(spec.template.spec.serviceAccountName)' \
    --project $PROJECT_ID)

# Grant the API service permission to invoke the LangGraph service
gcloud run services add-iam-policy-binding rito-langgraph \
    --region $REGION \
    --member "serviceAccount:$API_SERVICE_ACCOUNT" \
    --role "roles/run.invoker" \
    --project $PROJECT_ID

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "API Service URL: $API_URL"
echo "LangGraph Service URL: $LANGGRAPH_URL (internal)"
echo ""
echo "Your application is now live at: $API_URL"

