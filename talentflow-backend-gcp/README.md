# Instructions to deploy the code to google cloud

This README contains the simple commands needed to deploy and test the TalentFlow backend on Google Cloud. Aswell calls to the endpoints are written

The implementation includes:

- `parser-agent` - Cloud Run REST service
- `reputation-service` - Cloud Run REST service using Firestore
- `matching-orchestrator` - Cloud Run REST service
- `contract-service` - Cloud Run REST service publishing Pub/Sub events
- `milestone-handler` - Cloud Function Gen 2 triggered by Pub/Sub

## 1. Set variables

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=europe-west1
export MILESTONE_TOPIC=milestone-completed
```

Check:

```bash
echo $PROJECT_ID
echo $REGION
```

## 2. Enable Google Cloud services

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  cloudfunctions.googleapis.com \
  eventarc.googleapis.com \
  logging.googleapis.com
```

## 3. Create Firestore database

```bash
gcloud firestore databases create \
  --database="(default)" \
  --location=$REGION \
  --edition=standard \
  --type=firestore-native
```

## 4. Deploy parser-agent

```bash
gcloud run deploy parser-agent \
  --source ./parser-agent \
  --region $REGION \
  --allow-unauthenticated
```

```bash
export PARSER_AGENT_URL=$(gcloud run services describe parser-agent \
  --region $REGION \
  --format='value(status.url)')
```

Test:

```bash
curl $PARSER_AGENT_URL/health
```

---

## 5. Deploy reputation-service

```bash
gcloud run deploy reputation-service \
  --source ./reputation-service \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,FREELANCER_COLLECTION=freelancer_profiles
```

```bash
export REPUTATION_SERVICE_URL=$(gcloud run services describe reputation-service \
  --region $REGION \
  --format='value(status.url)')
```

Test:

```bash
curl $REPUTATION_SERVICE_URL/health
```

## 6. Deploy matching-orchestrator

```bash
gcloud run deploy matching-orchestrator \
  --source ./matching-orchestrator \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars PARSER_AGENT_URL=$PARSER_AGENT_URL,REPUTATION_SERVICE_URL=$REPUTATION_SERVICE_URL
```

```bash
export MATCHING_ORCHESTRATOR_URL=$(gcloud run services describe matching-orchestrator \
  --region $REGION \
  --format='value(status.url)')
```

Test:

```bash
curl $MATCHING_ORCHESTRATOR_URL/health
```

## 7. Create Pub/Sub topic

```bash
gcloud pubsub topics create $MILESTONE_TOPIC
```

If it says the topic already exists, ignore the error.

Optional debug subscription:

```bash
gcloud pubsub subscriptions create milestone-debug-sub \
  --topic=$MILESTONE_TOPIC
```

## 8. Deploy contract-service

```bash
gcloud run deploy contract-service \
  --source ./contract-service \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,MILESTONE_TOPIC=$MILESTONE_TOPIC
```

```bash
export CONTRACT_SERVICE_URL=$(gcloud run services describe contract-service \
  --region $REGION \
  --format='value(status.url)')
```

Test:

```bash
curl $CONTRACT_SERVICE_URL/health
```

## 9. Deploy milestone-handler Cloud Function

```bash
gcloud functions deploy milestone-handler \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --source ./milestone-handler \
  --entry-point milestone_handler \
  --trigger-topic $MILESTONE_TOPIC \
  --set-env-vars REPUTATION_SERVICE_URL=$REPUTATION_SERVICE_URL
```

## 10. Run data ingestion

Make sure your CSV file exists at:

```bash
data/resume_dataset_1200.csv
```

Then run:

```bash
REPUTATION_SERVICE_URL=$REPUTATION_SERVICE_URL python data_ingestion.py
```

Check profiles:

```bash
curl $REPUTATION_SERVICE_URL/profiles
```

## 11. Test the matching workflow

```bash
curl -X POST $MATCHING_ORCHESTRATOR_URL/match \
  -H "Content-Type: application/json" \
  -d '{
    "description": "We need a Python and SQL freelancer for a data analytics project with a budget of 55",
    "top_k": 5
  }'
```

## 12. Test contract creation

```bash
curl -X POST $CONTRACT_SERVICE_URL/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "c-demo-1",
    "job_id": "j-demo-1",
    "freelancer_id": "f1",
    "freelancer_name": "Test Freelancer",
    "terms": "Payment released after milestone completion.",
    "milestones": [
      {
        "milestone_id": "m1",
        "title": "First delivery",
        "amount": 300,
        "status": "pending"
      }
    ]
  }'
```

Check contract:

```bash
curl $CONTRACT_SERVICE_URL/contracts/c-demo-1
```

## 13. Test milestone completion and Pub/Sub event

```bash
curl -X POST $CONTRACT_SERVICE_URL/milestones/complete \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "c-demo-1",
    "milestone_id": "m1"
  }'
```

Expected result:

```json
{
  "message": "Milestone completed and event published",
  "pubsub_message_id": "...",
  "event": {
    "event_type": "MilestoneCompleted"
  }
}
```

## 14. Check milestone-handler logs

```bash
gcloud functions logs read milestone-handler \
  --gen2 \
  --region $REGION \
  --limit 20
```

## 15. Check reputation update

```bash
curl $REPUTATION_SERVICE_URL/profiles/f1
```

The reputation score should increase after the milestone event is processed.

# Useful health checks

```bash
curl $PARSER_AGENT_URL/health
curl $REPUTATION_SERVICE_URL/health
curl $MATCHING_ORCHESTRATOR_URL/health
curl $CONTRACT_SERVICE_URL/health
```
