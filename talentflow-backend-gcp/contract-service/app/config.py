import os

REPUTATION_SERVICE_URL = os.getenv("REPUTATION_SERVICE_URL", "http://localhost:8002")
MILESTONE_HANDLER_URL = os.getenv("MILESTONE_HANDLER_URL", "")
ALLOW_ORIGINS = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "*").split(",") if origin.strip()]
