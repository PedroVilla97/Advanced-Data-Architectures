Run reputation service
cd reputation-service
uvicorn app.main:app --reload --port 8082
Run contract service
cd contract-service
REPUTATION_SERVICE_URL=http://localhost:8082 uvicorn app.main:app --reload --port 8081
Run matching agent

Test profiles

GET http://localhost:8082/profiles

Test matching

POST http://localhost:8080/match

{
  "description": "We need a React and FastAPI developer with Docker and Firebase experience for a short web dashboard project. Budget 2500 and around 40 hours.",
  "top_k": 3
}
Create a contract

POST http://localhost:8081/contracts

{
  "contract_id": "c1",
  "job_id": "j1",
  "hiring_manager_id": "hm1",
  "freelancer_id": "f1",
  "freelancer_name": "Alice Johnson",
  "job_title": "Dashboard MVP",
  "hourly_rate": 40,
  "estimated_hours": 40,
  "terms": "Payment is released per milestone completion.",
  "milestones": [
    {
      "milestone_id": "m1",
      "title": "Initial API and frontend setup",
      "amount": 800,
      "status": "pending"
    },
    {
      "milestone_id": "m2",
      "title": "Dashboard delivery",
      "amount": 800,
      "status": "pending"
    }
  ]
}
Complete a milestone

POST http://localhost:8081/milestones/complete

