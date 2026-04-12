from app.agents.parser_agent import parse_job_description
from app.agents.matching_agent import rank_candidates
from app.clients.reputation_client import fetch_profiles
from app.models import MatchResponse


async def run_matching_flow(description: str, top_k: int) -> MatchResponse:
    parsed_job = parse_job_description(description)
    profiles = await fetch_profiles()
    shortlist = rank_candidates(parsed_job, profiles, top_k)
    return MatchResponse(parsed_job=parsed_job, shortlist=shortlist)