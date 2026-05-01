"""
Chat Router — POST /api/chat and GET /api/chart-data.

Uses direct keyword-based tool routing instead of ReAct agent,
which is unreliable on small CPU models like llama3.2:3b.
The LLM is used for synthesis/explanation, tools for data retrieval.
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

from backend.config import settings
from backend.tools.sql_tools import (
    get_top_performing_titles,
    get_title_trend,
    compare_titles,
    get_city_engagement,
    get_genre_performance,
    get_audience_segments,
    get_chart_data,
)
from backend.tools.doc_tools import search_internal_docs

log = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    chart_type: Optional[str] = "genre_views"


class ChatResponse(BaseModel):
    answer: str
    sources_used: list[str]
    duration_seconds: float


class ChartResponse(BaseModel):
    labels: list
    values: list
    title: str


# ── Smart Tool Router ─────────────────────────────────────────────────────────
# Deterministic keyword routing — no LLM needed to pick tools.
# Small models fail at this; we do it in Python instead.

def route_tools(question: str) -> tuple[str, list[str]]:
    """
    Returns (combined_tool_output, list_of_tools_used).
    Calls one or more tools based on question keywords.
    """
    q = question.lower()
    results = []
    tools_used = []

    # Rule 1: Comparison query
    if any(w in q for w in ["compare", "vs", "versus", "difference between"]):
        # Try to extract two title names
        titles = _extract_comparison_titles(question)
        if titles:
            results.append(compare_titles(titles[0], titles[1]))
            tools_used.append("CompareTitles")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Rule 2: Trending / specific title question
    elif any(t.lower() in q for t in [
        "stellar run", "dark orbit", "last kingdom", "neon drift",
        "shadow protocol", "echo chamber", "iron fable", "crimson tide",
        "the hollow", "bright horizons", "comedy chaos", "laugh track",
        "funny business", "jest mode", "roast masters"
    ]):
        title = _extract_title(question)
        if title:
            results.append(get_title_trend(title))
            tools_used.append("GetTitleTrend")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Rule 3: Top / best performing titles
    elif any(w in q for w in ["best", "top", "performed", "performing", "highest"]):
        results.append(get_top_performing_titles(year=2025))
        tools_used.append("GetTopPerformingTitles")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Rule 4: City / regional engagement
    elif any(w in q for w in ["city", "cities", "region", "regional", "engagement", "location"]):
        results.append(get_city_engagement())
        tools_used.append("GetCityEngagement")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Rule 5: Genre / comedy / sci-fi
    elif any(w in q for w in ["genre", "comedy", "sci-fi", "drama", "thriller", "action"]):
        results.append(get_genre_performance())
        tools_used.append("GetGenrePerformance")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Rule 6: Audience / segment / demographic
    elif any(w in q for w in ["audience", "segment", "demographic", "age", "platform"]):
        results.append(get_audience_segments())
        tools_used.append("GetAudienceSegments")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Rule 7: Leadership / recommendation / strategy
    elif any(w in q for w in ["recommend", "leadership", "strategy", "next quarter",
                               "should", "suggest", "advice", "roadmap"]):
        results.append(get_top_performing_titles(year=2025))
        tools_used.append("GetTopPerformingTitles")
        results.append(get_genre_performance())
        tools_used.append("GetGenrePerformance")
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")

    # Default: search docs + get top titles
    else:
        results.append(search_internal_docs(question))
        tools_used.append("SearchInternalDocs")
        results.append(get_top_performing_titles(year=2025))
        tools_used.append("GetTopPerformingTitles")

    combined = "\n\n---\n\n".join(results)
    return combined, tools_used


def _extract_title(question: str) -> Optional[str]:
    """Extract a known title name from the question."""
    known = [
        "Stellar Run", "Dark Orbit", "Last Kingdom", "Neon Drift",
        "Shadow Protocol", "Echo Chamber", "Iron Fable", "Crimson Tide",
        "The Hollow", "Bright Horizons", "Comedy Chaos", "Laugh Track",
        "Funny Business", "Jest Mode", "Roast Masters"
    ]
    q_lower = question.lower()
    for title in known:
        if title.lower() in q_lower:
            return title
    return None


def _extract_comparison_titles(question: str) -> Optional[list]:
    """Extract two title names from a comparison question."""
    known = [
        "Stellar Run", "Dark Orbit", "Last Kingdom", "Neon Drift",
        "Shadow Protocol", "Echo Chamber", "Iron Fable", "Crimson Tide",
        "The Hollow", "Bright Horizons", "Comedy Chaos", "Laugh Track",
        "Funny Business", "Jest Mode", "Roast Masters"
    ]
    q_lower = question.lower()
    found = [t for t in known if t.lower() in q_lower]
    return found[:2] if len(found) >= 2 else None


# ── LLM Synthesis ─────────────────────────────────────────────────────────────

def synthesize(question: str, tool_data: str) -> str:
    """
    Pass tool results + question to Ollama for natural language synthesis.
    The LLM never sees raw data — only the tool output summaries.
    """
    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0.1,
        num_predict=512,
    )

    system = (
        "You are a concise internal analytics assistant for an entertainment company. "
        "You are given data retrieved from internal tools. "
        "Answer the user's question using ONLY the provided data. "
        "Be factual and brief. Do not make up numbers. "
        "End your answer by stating which data sources were used."
    )

    user_msg = (
        f"Question: {question}\n\n"
        f"Data from internal tools:\n{tool_data}\n\n"
        f"Provide a clear, concise answer."
    )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=user_msg),
    ]

    response = llm.invoke(messages)
    return response.content


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    log.info(f"[Chat] Question: {request.question}")
    start = time.time()

    try:
        # Step 1: Route to tools deterministically
        tool_data, tools_used = route_tools(request.question)
        log.info(f"[Chat] Tools called: {tools_used}")

        # Step 2: LLM synthesizes a natural language answer
        answer = synthesize(request.question, tool_data)

        duration = round(time.time() - start, 2)
        log.info(f"[Chat] Done in {duration}s")

        return ChatResponse(
            answer=answer,
            sources_used=tools_used,
            duration_seconds=duration,
        )

    except Exception as e:
        log.error(f"[Chat Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart-data", response_model=ChartResponse)
async def chart_data(chart_type: str = "genre_views"):
    log.info(f"[Chart] chart_type={chart_type}")
    data = get_chart_data(chart_type)
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return ChartResponse(**data)
