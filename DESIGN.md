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

# Post final version explanations #

- I wanted the agent to be able to continue researching without limitations, so it could actually conduct proper deep research.

- To do this, I implemented dynamic context compression. 
    - It keeps track of all search results until they surpass a certain context length limit that I defined.
    - At each reflect score, it goes over all findings and gives a comprehension score out of 100
    - When the findings surpass the threshold, it calculates a compression ratio based on the target comprehension score inputted at the start of the search by the user (default 90)
    - It then compresses the current context to size that is that ratio of the context limit
    - The idea is that if it is at 60%, and target is 90%, we have about 2/3 of the total data we are going to have for the final report, so it should take up 2/3 of the max context window.
    - I found this to maintain high quality reports, without any information loss, while also managing context perfectly

- I also included an option for a brief report that uses a mini model for improved speed. 

# Future improvements I didn't have time for #

- with more time, I would definitely implement human in the loop both at the beginning of the research and at the end. 
    - during the plan phase, I could have the agent present its research plan to the user, and the user can give feedback to perfect it before  deep research starts
    - I can also save all of the data from the research process at the end, and after generating the final report, ask the user if there are any areas that require further research. If so, I can have the agent continue researching with all of the current data already in place, so it doesn't have to start from scratch

- Another thing I wanted to add but did not have time was image generation in the report. would have been really cool, but I just didn't get to it and wanted to focus on how deep I can have the agent efficiently research.
