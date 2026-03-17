# Early Planning #

High Level Architecture:

- 5 step agent loop
    - Plan (what specifically needs to be searched)
    - Search (obtain raw search results based on plan)
    - Analyze (summarize/compress search results)
        - Need this since I will implement recursive searching, and I want to manage context efficiently
    - Reflect (decide what needs to be researched further based on current knowledge)
    - Write (final structured report)

- Agent State
    - messages (user input, internal agent messages, final output)
    - search results (raw search results, cleared after each iteration)
    - research plan (plan to reference)
    - findings (continuous growing knowledge by summarizing search results and appending at each iteration)
    - iteration (iteration count to prevent infinite recursion and control research depth)

# Mid-implementation decisions #

Should I give the llm direct tool calling power or have it return queries to me and I call the tools directly?
Letting the llm do it directly gives it more flexibility. perhaps it will want to change its queries after receiving the output from one. for example, maybe it comes up with 3 things to search, but the first query results already answer the other 2 queries. it can skip them or change them.
On the other hand this gives me less control, and I want to summarize the results of each query to reduce context. 
Decision: I'll call the search tools directly instead letting the llm do it. The case where an llm wants to change its queries in real time should be pretty rare, and with good prompting i can ensure queries are not too similar to reduce this even more. It's better to have more control in this case, especially since the worst case is I just have a few redundant api calls.

# Post first version analysis #

- Seems to be a lot of information loss during compression step 
    - could implement a dynamic compression system that only summarizes context when it actually gets too large
    - could also be improved with better prompting

- Reflect node seems to always continue searching
    - could be due to over-compression in analyze step leading to gaps

- Number of iterations does not directly translate to research depth
    - could implement some sort of running confidence/comprehension score and enter write mode when it is reached
    - this could risk looping infinitely, so i'll have to set safeguards and optimize prompting to accurately approximate the confidence score

- Searches should be happening in parallel rather than in series

- Independent searches might return duplicate sources
    - could implement logic to keep track of visited urls and avoid wasting time and tokens revisiting them

- Currently using gpt-4o for each step
    - could consider trying gpt-4o-mini for lightweight steps to speed up process

# Mid - second version implementation decisions #

- Information loss during compression is likely coming from re-compression of all findings at each step. new findings should be compressed once and then appended to old findings
    - Should i implement this by prompting the llm to only compress new findings, or should I hard code it in?
        - Letting the llm do it would avoid duplicated findings since it has access to previous and new findings
        - Hard coding might produce duplicate findings
    - Decision: I'll hard code this in, I would rather have duplicate findings than lose important information. Write step will deduplicate anyways. 


