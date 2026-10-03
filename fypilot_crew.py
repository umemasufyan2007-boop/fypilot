import os
import time

# Disable CrewAI telemetry (avoids unnecessary warnings on the cloud)
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM

# Models are tried in this order. Each model has its own daily free quota,
# so if one runs out the app automatically moves to the next one.
MODELS = ["gemini/gemini-3.5-flash-lite", "gemini/gemini-3.8-flash"]

# Retries are only used when Google is temporarily overloaded (503)
MAX_RETRIES = 3
WAIT_SECONDS = 8

# Remembers plans already generated, so repeating the same idea costs no new request
_CACHE = {}


# ---------- Output structure ----------
class Module(BaseModel):
    name: str = Field(description="Module name")
    description: str = Field(description="One-line purpose of the module")


class Phase(BaseModel):
    phase: str = Field(description="Phase name, e.g. 'Phase 1: Research & Design'")
    duration: str = Field(description="e.g. '3 weeks'")
    tasks: List[str] = Field(description="Concrete tasks in this phase")


class ProjectPlan(BaseModel):
    title: str
    problem_statement: str
    objectives: List[str]
    key_features: List[str]
    tech_stack: List[str] = Field(description="Each item: 'Technology - why it is used'")
    modules: List[Module]
    roadmap: List[Phase]
    total_timeline: str
    challenges: List[str] = Field(description="Each item: 'Challenge - how to mitigate it'")


# ---------- Crew ----------
def _run_crew(model_name: str, idea: str, api_key: str, team_size: int, months: int) -> ProjectPlan:
    llm = LLM(model=model_name, api_key=api_key)

    planner = Agent(
        role="Final Year Project Planning Specialist",
        goal="Turn a student's rough FYP idea into a realistic, well-structured project plan",
        backstory=(
            "You are an experienced FYP supervisor at a university. You help students "
            "refine vague ideas into focused, achievable projects with clear scope, "
            "sensible technology choices and realistic timelines."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )

    task = Task(
        description=(
            f"A student has this Final Year Project idea:\n\n\"{idea}\"\n\n"
            f"Team size: {team_size} student(s). Available time: {months} months.\n\n"
            "Create a complete project plan with: an improved project title, problem "
            "statement, 4-6 objectives, 6-8 key features/requirements, a suggested "
            "technology stack (with reason for each), 4-6 system modules, a phase-wise "
            "development roadmap with tasks, total estimated timeline that fits the "
            "available time, and 4-5 possible challenges with mitigations. "
            "Keep it realistic and beginner-to-intermediate friendly. "
            "Write everything in clear, professional English, even if the idea "
            "is written in another language. Use plain text only (no markdown symbols)."
        ),
        expected_output="A structured FYP project plan in English matching the required schema.",
        agent=planner,
        output_pydantic=ProjectPlan,
    )

    crew = Crew(
        agents=[planner],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    return result.pydantic


def _is_overloaded(error: Exception) -> bool:
    # Only "Google is busy" errors are worth retrying on the same model.
    # A quota error (429) is NOT retried: retrying would waste more requests.
    text = str(error).lower()
    return any(k in text for k in ["503", "unavailable", "overloaded", "high demand"])


# The API key is not stored here. It is passed in from app.py.
def generate_plan(idea: str, api_key: str, team_size: int, months: int) -> ProjectPlan:
    cache_key = (idea.strip().lower(), team_size, months)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    last_error = None
    for model_name in MODELS:
        for attempt in range(MAX_RETRIES):
            try:
                plan = _run_crew(model_name, idea, api_key, team_size, months)
                _CACHE[cache_key] = plan
                return plan
            except Exception as e:
                last_error = e
                if _is_overloaded(e) and attempt < MAX_RETRIES - 1:
                    time.sleep(WAIT_SECONDS * (attempt + 1))  # wait 8s, then 16s
                    continue
                break  # quota or other error: move on to the next model
    raise last_error