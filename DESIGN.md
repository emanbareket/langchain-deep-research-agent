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

