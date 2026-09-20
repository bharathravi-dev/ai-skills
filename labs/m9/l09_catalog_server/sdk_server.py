"""The same course-catalog server, written with the official MCP Python SDK.

Compare with server.py in this directory: the SDK generates inputSchema and
outputSchema from type hints, speaks both protocol eras, validates arguments,
frames messages and handles every method -- in roughly a tenth of the code.

Requires:  pip install "mcp==2.2.0"
Run by a client:  python labs/m9/l09_catalog_server/sdk_server.py
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

COURSES = {
    "mcp-101": {"title": "Model Context Protocol Fundamentals", "level": "intermediate", "hours": 24},
    "rag-201": {"title": "Retrieval-Augmented Generation", "level": "advanced", "hours": 34},
    "py-100": {"title": "Python for AI Engineers", "level": "beginner", "hours": 34},
    "gov-150": {"title": "AI Governance and Security", "level": "intermediate", "hours": 24},
    "aws-110": {"title": "AWS Foundations", "level": "beginner", "hours": 28},
}

server = MCPServer("course-catalog-sdk", version="0.9.0",
                   instructions="Read-only catalog of AI engineering courses. Use search_courses before planning.")


class Course(BaseModel):
    id: str
    title: str
    level: str
    hours: int


class SearchResult(BaseModel):
    results: list[Course]


class StudyPlan(BaseModel):
    total_hours: int
    weeks: int


@server.tool(title="Search courses")
def search_courses(query: str, level: Literal["beginner", "intermediate", "advanced"] | None = None) -> SearchResult:
    """Find courses whose title contains the query, optionally filtered by level."""
    q = query.lower()
    return SearchResult(results=[Course(id=cid, **c) for cid, c in sorted(COURSES.items())
                                 if q in c["title"].lower() and (level is None or c["level"] == level)])


@server.tool(title="Plan study time")
def plan_study_time(course_ids: list[str], hours_per_week: float) -> StudyPlan:
    """Estimate how many weeks a set of courses takes at a given number of study hours per week."""
    unknown = [cid for cid in course_ids if cid not in COURSES]
    if unknown:
        # ToolError = an anticipated failure: its message reaches the model. Any other
        # exception is treated as a crash and the model sees only "Error executing tool".
        raise ToolError(f"Unknown course id(s): {unknown}. Call search_courses to find valid ids.")
    total = sum(COURSES[cid]["hours"] for cid in course_ids)
    return StudyPlan(total_hours=total, weeks=int(-(-total // hours_per_week)))


@server.resource("catalog://courses", mime_type="application/json")
def all_courses() -> str:
    return json.dumps([{"id": cid, "title": c["title"]} for cid, c in sorted(COURSES.items())])


@server.resource("catalog://courses/{course_id}", mime_type="application/json")
def one_course(course_id: str) -> str:
    return json.dumps({"id": course_id, **COURSES[course_id]})


@server.prompt(title="Study plan")
def study_plan(course_id: str, hours_per_week: str = "5") -> str:
    """Draft a weekly study plan for one course."""
    c = COURSES[course_id]
    return (f"Create a week-by-week study plan for '{c['title']}' ({c['hours']} hours, {c['level']} level) "
            f"for a learner with {hours_per_week} hours per week. Include a checkpoint at the end of each week.")


if __name__ == "__main__":
    server.run()  # stdio
