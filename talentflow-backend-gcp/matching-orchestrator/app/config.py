import os

PARSER_AGENT_URL = os.getenv("PARSER_AGENT_URL", "http://localhost:8001")
REPUTATION_SERVICE_URL = os.getenv("REPUTATION_SERVICE_URL", "http://localhost:8002")
ALLOW_ORIGINS = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "*").split(",") if origin.strip()]
