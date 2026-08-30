"""JobPilot: an autonomous job-application agent built on Google ADK.

Given one goal ("apply to this job for me") the agent plans and executes,
without further user turns:
  1. parses the job posting into structured requirements
  2. scores the candidate's fit against those requirements
  3. drafts tailored resume bullets and a cover letter
  4. persists the application record (save_application tool)
  5. schedules a follow-up reminder (create_followup tool)
  6. returns a structured summary
"""
from __future__ import annotations

import json
import os
import uuid

from google.adk import Agent

from .tools import create_followup, list_past_applications, save_application

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")

INSTRUCTION = """\
You are JobPilot, an autonomous job-application agent. You are given a job
posting and a candidate profile. Without asking the user any follow-up
questions, plan and execute the full workflow yourself:

1. Parse the job posting into: company, title, seniority, must_have_skills
   (list), nice_to_have_skills (list).
2. Compare the candidate profile against those requirements. Produce a
   fit_score from 0-100 and a list of gaps (skills/experience the
   candidate is missing).
3. Draft 3-5 tailored resume bullet points that highlight the candidate's
   most relevant matching experience, phrased for this specific role.
4. Draft a concise, specific cover letter (150-250 words) — no generic
   filler, reference concrete details from the posting.
5. Call the save_application tool with a JSON string record containing:
   company, title, seniority, fit_score, gaps, resume_bullets,
   cover_letter.
6. Call the create_followup tool using the id returned by step 5, with a
   sensible days_from_now (5-7 for most roles) and a short note.
7. Reply to the user with a clear final summary: fit score, top gaps,
   the resume bullets, the cover letter, and the scheduled follow-up
   date. Do this all in one pass — do not wait for user confirmation
   between steps.
"""

root_agent = Agent(
    name="jobpilot_agent",
    model=MODEL,
    instruction=INSTRUCTION,
    tools=[save_application, create_followup, list_past_applications],
)


def _extract_text(event) -> str | None:
    content = getattr(event, "content", None)
    if content is None:
        return None
    parts = getattr(content, "parts", None) or []
    texts = [p.text for p in parts if getattr(p, "text", None)]
    return "\n".join(texts) if texts else None


async def run_agent(job_text: str, profile_text: str) -> dict:
    """Runs the ADK agent end-to-end and returns the final text + step log."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    user_id = "demo-user"
    session_id = str(uuid.uuid4())

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="jobpilot", user_id=user_id, session_id=session_id
    )
    runner = Runner(
        agent=root_agent, app_name="jobpilot", session_service=session_service
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    f"JOB POSTING:\n{job_text}\n\n"
                    f"CANDIDATE PROFILE:\n{profile_text}\n\n"
                    "Apply to this job for me."
                )
            )
        ],
    )

    steps: list[str] = []
    final_text = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        label = getattr(event, "author", "agent")
        text = _extract_text(event)
        if text:
            steps.append(f"[{label}] {text}")
            final_text = text

    return {"final_text": final_text, "steps": steps}
