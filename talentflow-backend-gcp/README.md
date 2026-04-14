# TalentFlow backend package for Google Cloud

This package includes a deployable MVP backend for **TalentFlow** with:

- **4 HTTP microservices/agents** deployed as containers on **Cloud Run**
- **1 Gen 2 Cloud Function** for milestone handling
- a local `docker-compose.yml` for development
- shell scripts for local startup and Google Cloud deployment

## Services

1. **matching-orchestrator**
   - orchestrates matching
   - calls parser-agent and reputation-service
   - stores shortlists in memory

2. **parser-agent**
   - parses free-text job descriptions
   - exposes skill and budget extraction endpoints

3. **reputation-service**
   - owns freelancer profiles and reputation scores
   - in-memory store for MVP, easy to replace with Firestore later

4. **contract-service**
   - owns contracts and milestones
   - calls milestone-handler after milestone completion

5. **milestone-handler-function**
   - HTTP-triggered Cloud Function (Gen 2)
   - simulates payment release and updates freelancer reputation

## Why this fits your course requirements

- **At least 4 internal services/agents**: parser-agent, matching-orchestrator, reputation-service, contract-service
- **Mix of REST and FaaS**: Cloud Run services + Gen 2 Cloud Function
- **12+ operations**:
  - matching-orchestrator: `health`, `submit_job`, `get_shortlist`
  - parser-agent: `health`, `parse_job`, `extract_skills`, `extract_budget`
  - reputation-service: `health`, `list_profiles`, `get_profile`, `create_profile`, `update_score`
  - contract-service: `health`, `list_contracts`, `get_contract`, `create_contract`, `complete_milestone`
  - milestone-handler-function: `handle_milestone_completion`
- **Composition**:
  - orchestration: matching-orchestrator → parser-agent + reputation-service
  - service-to-function composition: contract-service → milestone-handler-function

## Assumptions

- This package is an **MVP** for demonstration.
- It uses **in-memory storage** so it runs immediately without provisioning databases.
- The storage layer can later be replaced with:
  - Firestore for profiles
  - Cloud SQL for contracts
  - Pub/Sub or Eventarc for milestone events
- Authentication is not enforced in this MVP.
- CORS is open to simplify frontend integration during development.

## Architecture

```text
Frontend
   |
   v
matching-orchestrator  --->  parser-agent
   |
   +------------------->  reputation-service
   |
   v
contract-service  --->  milestone-handler-function  ---> reputation-service
```

## Local development

### 1) Start all Cloud Run services locally

```bash
docker compose up --build
```

Services:
- matching-orchestrator: `http://localhost:8000`
- parser-agent: `http://localhost:8001`
- reputation-service: `http://localhost:8002`
- contract-service: `http://localhost:8003`

### 2) Start the function locally in another terminal

```bash
cd milestone-handler-function
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
functions-framework --target=handle_milestone_completion --debug --port=8084
```

Then set:

```bash
export MILESTONE_HANDLER_URL=http://localhost:8084
```

If you use `docker compose`, contract-service already exposes the env var placeholder. Replace it in `.env` or the compose file for local function testing.

## Quick tests

### Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### Match request

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Need a React and Firebase developer for a dashboard MVP with Docker knowledge and budget 45",
    "top_k": 3
  }'
```

### Create contract

```bash
curl -X POST http://localhost:8003/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "c1",
    "job_id": "j1",
    "freelancer_id": "f2",
    "freelancer_name": "Bruno Silva",
    "terms": "Payment is released after each completed milestone.",
    "milestones": [
      {"milestone_id": "m1", "title": "UI prototype", "amount": 300, "status": "pending"},
      {"milestone_id": "m2", "title": "Final dashboard", "amount": 500, "status": "pending"}
    ]
  }'
```

### Complete milestone

```bash
curl -X POST http://localhost:8003/milestones/complete \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "c1",
    "milestone_id": "m1"
  }'
```

## Deploy to Google Cloud

### Prerequisites

Install and initialize the Google Cloud CLI, choose a project, and enable the required APIs.

```bash
gcloud init
gcloud config set project YOUR_PROJECT_ID
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com logging.googleapis.com cloudfunctions.googleapis.com
```

### Deploy order

Deploy in this order so service URLs can be injected into dependent services:

1. `parser-agent`
2. `reputation-service`
3. `milestone-handler-function`
4. `contract-service`
5. `matching-orchestrator`

### One-command deploy

```bash
chmod +x scripts/deploy_gcp.sh
./scripts/deploy_gcp.sh YOUR_PROJECT_ID europe-west1
```

The script:
- deploys each Cloud Run service from source
- deploys the milestone Cloud Function Gen 2
- injects dependent service URLs as environment variables
- prints final service URLs

## Recommended next replacements

- replace reputation-service memory store with Firestore
- replace contract-service memory store with Cloud SQL
- replace direct function HTTP call with Pub/Sub + Eventarc
- add Firebase Auth token verification middleware
- add dataset ingestion jobs
