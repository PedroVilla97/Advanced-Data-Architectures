#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:-}"
REGION="${2:-europe-west1}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Usage: ./scripts/deploy_gcp.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "Using project: ${PROJECT_ID}"
echo "Using region:  ${REGION}"

gcloud config set project "${PROJECT_ID}" >/dev/null

echo "Enabling required APIs..."
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  logging.googleapis.com \
  cloudfunctions.googleapis.com

deploy_run_service () {
  local SERVICE_NAME="$1"
  local SOURCE_DIR="$2"
  shift 2
  echo ""
  echo "Deploying Cloud Run service: ${SERVICE_NAME}"
  gcloud run deploy "${SERVICE_NAME}" \
    --source "${SOURCE_DIR}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    "$@" \
    --format='value(status.url)'
}

echo ""
echo "Step 1/5 - parser-agent"
PARSER_URL=$(deploy_run_service "parser-agent" "./parser-agent")

echo ""
echo "Step 2/5 - reputation-service"
REPUTATION_URL=$(deploy_run_service "reputation-service" "./reputation-service")

echo ""
echo "Step 3/5 - milestone-handler-function"
MILESTONE_FUNCTION_URL=$(gcloud functions deploy milestone-handler \
  --gen2 \
  --runtime python311 \
  --region "${REGION}" \
  --source "./milestone-handler-function" \
  --entry-point handle_milestone_completion \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars "REPUTATION_SERVICE_URL=${REPUTATION_URL}" \
  --format='value(serviceConfig.uri)')

echo ""
echo "Step 4/5 - contract-service"
CONTRACT_URL=$(deploy_run_service "contract-service" "./contract-service" \
  --set-env-vars "REPUTATION_SERVICE_URL=${REPUTATION_URL},MILESTONE_HANDLER_URL=${MILESTONE_FUNCTION_URL}")

echo ""
echo "Step 5/5 - matching-orchestrator"
MATCHING_URL=$(deploy_run_service "matching-orchestrator" "./matching-orchestrator" \
  --set-env-vars "PARSER_AGENT_URL=${PARSER_URL},REPUTATION_SERVICE_URL=${REPUTATION_URL}")

echo ""
echo "Deployment complete."
echo "parser-agent:           ${PARSER_URL}"
echo "reputation-service:     ${REPUTATION_URL}"
echo "milestone-handler:      ${MILESTONE_FUNCTION_URL}"
echo "contract-service:       ${CONTRACT_URL}"
echo "matching-orchestrator:  ${MATCHING_URL}"
