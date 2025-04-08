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
            Given schema of the database, and the prompt,
            generate a Cypher query to retrieve the most relevant information from the database.
            You may need to access all components of the database, so make sure to return all the results.
            Feel free to use multiple MATCH clauses to access different components of the database.
            
            Important rules for Cypher queries:
            1. If using ORDER BY with aggregation functions (like count, sum, etc.), 
               the same aggregation must be present in the RETURN clause
            2. When using ORDER BY, ensure the sorted field is included in the RETURN clause
            3. Use proper variable naming and consistent aliases
            4. NEVER use LET clauses - they are not supported in Neo4j
            5. For parameters, use $paramName directly in the query
            6. For text search, use:
               - CONTAINS: property CONTAINS searchTerm
               - STARTS WITH: property STARTS WITH searchTerm
               - ENDS WITH: property ENDS WITH searchTerm
            7. To match multiple node types, use UNION or separate MATCH clauses - NEVER use OR between labels
            8. When using UNION, all queries must return the same column names
            9. For boolean operations in WHERE clauses:
               - Use AND/OR between complete conditions
               - Each condition must evaluate to a boolean
               - Never compare nodes directly, compare their properties
            10. To match nodes with multiple possible labels, use UNION or multiple matches:
                INCORRECT: MATCH (n:Article OR n:ContentChunk)
                CORRECT:
                ```
                MATCH (n:Article)
                RETURN n.title, n.content
                UNION
                MATCH (n:ContentChunk)
                RETURN n.title, n.content
                ```
            
            Based on the user's prompt, analyze their intent and generate an appropriate Cypher query.
            The query should search relevant nodes and relationships to find the information they're looking for.
            
            For example, if they ask "What articles mention neural networks?", you might generate:
            ```
            MATCH (n:Article)
            WHERE n.title CONTAINS 'neural networks' OR n.content CONTAINS 'neural networks'
            RETURN n.title AS title, n.content AS content, 'Article' AS source
            
            UNION
            
            MATCH (n:ContentChunk)
            WHERE n.content CONTAINS 'neural networks'
            RETURN n.title AS title, n.content AS content, 'ContentChunk' AS source
            ```
            
            But adapt the query based on what they're actually asking about - don't just copy this example.
            Use the schema to understand what nodes and relationships are available.
            
            Schema and Prompt:
        '''

        self.interpret_results = '''
            Given the user's original question and the query results from the database,
            provide a clear, natural language response that answers their question.
            
            Guidelines:
            1. Focus on directly answering the user's question
            2. If the results are empty, explain that no matching data was found
            3. If there are multiple results, summarize them appropriately
            4. Include relevant details but avoid overwhelming the user
            5. Use a conversational tone while maintaining professionalism
            6. If the results suggest partial or incomplete information, acknowledge this
            7. Format any lists, numbers, or structured data in a readable way
            
            Original Question and Results:
        '''
    
prompts = Prompts()