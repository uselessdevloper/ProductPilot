#!/usr/bin/env bash
# ProductPilot AI - Master Deployment Script for Google Cloud Platform
# Deploys Backend + All 6 Agents + Frontend to Cloud Run

set -e

# Load environment variables if .env exists
if [ -f "backend/taskpilotai/.env" ]; then
    export $(grep -v '^#' backend/taskpilotai/.env | xargs)
fi

PROJECT_ID="${GCP_PROJECT_ID:-productpilotai}"
REGION="${VERTEX_AI_LOCATION:-us-central1}"
BACKEND_SERVICE="productpilotai-backend"
FRONTEND_SERVICE="productpilotai-frontend"

echo "ProductPilot AI - Master GCP Cloud Run Deployment"
echo "Project ID: ${PROJECT_ID}"
echo "Region:     ${REGION}"

# Ensure gcloud project is set
gcloud config set project "${PROJECT_ID}" --quiet

# Enable required services
echo "Enabling GCP services..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com --project="${PROJECT_ID}"

# 1. Deploy Backend + 6 Agents
echo ""
echo "STEP 1: Deploying Backend & 6 Autonomous Agents..."
IMAGE_BACKEND="gcr.io/${PROJECT_ID}/${BACKEND_SERVICE}:latest"
(cd backend/taskpilotai && gcloud builds submit --project="${PROJECT_ID}" --tag="${IMAGE_BACKEND}" .)

gcloud run deploy "${BACKEND_SERVICE}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_BACKEND}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="NODE_ENV=production,LLM_PROVIDER=${LLM_PROVIDER:-openrouter},LLM_MODEL=${LLM_MODEL:-google/gemini-2.5-flash},OPEN_ROUTER_API_KEY=${OPEN_ROUTER_API_KEY},NVIDIA_API_KEY=${NVIDIA_API_KEY},GEMINI_API_KEY=${GEMINI_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY},SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}"

BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")
echo "Backend Live at: ${BACKEND_URL}"

# 2. Deploy Frontend App
echo ""
echo "STEP 2: Deploying Frontend Web Application..."
IMAGE_FRONTEND="gcr.io/${PROJECT_ID}/${FRONTEND_SERVICE}:latest"
(cd frontend/taskpilotai && gcloud builds submit --project="${PROJECT_ID}" --tag="${IMAGE_FRONTEND}" .)

gcloud run deploy "${FRONTEND_SERVICE}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_FRONTEND}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=256Mi \
    --cpu=1

FRONTEND_URL=$(gcloud run services describe "${FRONTEND_SERVICE}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

echo ""
echo "DEPLOYMENT COMPLETE TO GOOGLE CLOUD!"
echo "Frontend Web App:     ${FRONTEND_URL}"
echo "Backend API & Agents: ${BACKEND_URL}"
