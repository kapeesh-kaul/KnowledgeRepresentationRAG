class Prompts:
    """
    A class to handle various prompt templates for language model interactions.

    Methods
    -------
    summarize_article():
        Returns a prompt template for summarizing an article and providing a plain text output.
    """
    def __init__(self):
        """
        Returns a prompt template for summarizing an article and providing a plain text output.
        """
        
        self.summarize_article = '''
            Given the article content, 
            summarize the main ideas and provide a 
            plain text output summarizing the main ideas.
        '''
        self.generate_query = '''
You are an expert in Neo4j Cypher. Given the user's prompt and the database schema, your task is to generate a valid Cypher query to retrieve relevant information.

=== CYPHER QUERY RULES ===
1. Use only valid Cypher clauses: MATCH, WHERE, RETURN, OPTIONAL MATCH, WITH, UNION, ORDER BY, LIMIT.
2. NEVER use unsupported syntax like `LET`, `SEE_ALSO`, or label OR logic.
3. For keyword-based searches, ONLY use the `ContentChunk` node's `content` property.
4. All keyword matching must be **case-insensitive**.
   Use either of the following:
   - Using `toLower(...)`:
     ```
     MATCH (c:ContentChunk)
     WHERE toLower(c.content) CONTAINS 'gandhi'
     RETURN c
     ```
   - Or using regex:
     ```
     MATCH (c:ContentChunk)
     WHERE c.content =~ '(?i).*gandhi.*'
     RETURN c
     ```

5. Do NOT use regex inside `{}` maps.
6. Do NOT use `OR` between node labels. Use `UNION` if needed.
7. Always return relevant fields such as `c`, or `c.title, c.content`.
8. Keep the structure clean and minimal.

=== RESPONSE FORMAT ===
Return ONLY a valid Cypher query inside triple backticks, like this:

```cypher
MATCH (c:ContentChunk)
WHERE toLower(c.content) CONTAINS 'gandhi'
RETURN c
```

Do NOT include explanations or extra text.

'''

        self.interpret_results = '''
You are a helpful assistant tasked with interpreting query results from a knowledge graph about historical figures and events.

Your task is to provide a clear, well-structured response that directly answers the user's question based on the provided results.

Guidelines:
Most importantly, you must provide a clear, one sentence answer to the question.
1. Start with a clear, direct answer to the question
2. Organize information chronologically when relevant
7. If information is incomplete or contradictory, acknowledge this


Remember to:
- Focus on accuracy and clarity
- Include specific details from the source material
- Organize information logically
- Acknowledge any gaps in the information
- Use proper nouns and dates precisely as they appear in the source

Query and results:
'''
    
prompts = Prompts()