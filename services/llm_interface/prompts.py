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
            The query should be in the following format:
            ```
            MATCH (n:Article)
            WHERE n.title = $title
            RETURN n.title, n.content
            ```
            
            Schema and Prompt:
        '''
    
prompts = Prompts()