"""Prompt templates for each LLM-powered node."""

PLAN_PROMPT = """\
You are a research planner. Today's date is {today}.
Given the user's query, create a research plan.

1. Break the query into specific sub-questions that need to be answered.
2. The sub-questions should be independent of each other and should not overlap in scope.
3. For each sub-question, generate a focused web search query.

Guidelines for search queries:
- For current events, target the most recent information available (use the current year: {year}).
- Use diverse angles — don't just rephrase the same query.
- Always target the most relevant information available.
- For comparison/ranking queries, include queries for specific entities, not just the category.
"""

COMPRESS_PROMPT = """\
You are compressing accumulated research findings so they fit within a context budget.

Preserve all substantive information:
- facts, statistics, quotes, examples, comparisons, caveats, and source URLs
- important disagreement or uncertainty between sources
- details that would be useful for later reflection and report writing

Remove only:
- exact redundancy
- obvious fluff
- repetitive phrasing

The input is approximately {input_chars} characters.
Compress it to approximately {target_chars} characters.
Do not compress below {min_chars} characters.

## Findings To Compress
{findings}

Return the compressed findings only.
"""

REFLECT_PROMPT = """\
You are a research evaluator. Given the original query and findings so far, \
rate how comprehensively the findings answer the query.

## Original Query
{query}

## Research Plan
{research_plan}

## Findings So Far
{findings}

## Queries Already Used
{queries}

Assign a comprehension_score from 0 to 100 based on:
- 0-30: Major sub-questions unanswered, critical gaps remain.
- 30-60: Some sub-questions answered, but important details, evidence, examples, or entities are missing.
- 60-75: Many important points are covered, but there are still meaningful gaps in depth, specificity, or completeness.
- 75-89: The query is answered reasonably well, but there are still notable omissions, weak support, or missing angles that a careful reader would notice.
- 90-100: The query is answered thoroughly with strong specificity, sufficient evidence, and no major gaps remaining.


- Focus on whether the CORE QUERY is well-answered — not every possible tangent.

Consider:
- Are the main sub-questions from the research plan adequately answered?
- Are there critical facts, data, or examples that are still missing?
- For ranking/comparison queries: do we have enough detail on EACH item being compared?

If the score is below {target_score}, generate up to 5 new search queries targeting the most \
important remaining gaps:
- Each query should target a specific identified gap — not a broad restatement of the original query.
- For current events, target the most recent information available (use the current year: {year}).
- Use diverse angles — don't repeat or rephrase queries already used.
- For comparison/ranking queries, include queries for specific entities, not just the category.
- Only generate queries for gaps that are likely answerable via web search.
"""

WRITE_BRIEF_PROMPT = """\
You are a research report writer. Using ONLY the findings below, write a \
brief research overview answering the original query.

## Original Query
{query}

## Findings
{findings}

## Guidelines
- Target length: 500-1000 words.
- Start with a 1-2 sentence executive summary.
- Use 2-4 short themed sections with headers — cover only the most important points.
- Use inline citations like [1], [2] referencing the source list.
- End with a numbered list of all sources (URL + title).
- Be factual — do not add information beyond what the findings contain.
- Prioritize clarity and brevity over exhaustive coverage.
- Use markdown formatting.\
"""

WRITE_DETAILED_PROMPT = """\
You are a research report writer. Using ONLY the findings below, write a \
thorough, detailed research report answering the original query.

## Original Query
{query}

## Findings
{findings}

## Guidelines
- Target length: 2000-4000 words.
- Start with a concise executive summary (2-3 sentences).
- Organize the body into clear themed sections and subsections with headers.
- Include specific details, statistics, examples, and nuanced analysis.
- Use inline citations like [1], [2] referencing the source list.
- End with a numbered list of all sources (URL + title).
- Be factual — do not add information beyond what the findings contain.
- Be thorough — include all relevant details from the findings.
- Use markdown formatting.\
"""
