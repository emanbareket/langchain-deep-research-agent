"""Pydantic models for structured LLM output."""

from pydantic import BaseModel, Field


class PlanOutput(BaseModel):
    """Output of the PLAN node."""

    sub_questions: list[str] = Field(description="3-5 specific sub-questions to investigate")
    search_queries: list[str] = Field(description="One focused search query per sub-question")


class ReflectOutput(BaseModel):
    """Output of the REFLECT node."""

    assessment: str = Field(description="1-2 sentence evaluation of research coverage and gaps")
    comprehension_score: int = Field(
        description="0-100 score reflecting how comprehensively the findings answer the original query",
    )
    new_search_queries: list[str] = Field(
        default_factory=list,
        description="Search queries targeting identified gaps (if score is below threshold)",
    )
