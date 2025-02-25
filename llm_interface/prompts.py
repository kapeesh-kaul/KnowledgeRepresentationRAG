class Prompts:
    """
    A class to handle various prompt templates for language model interactions.

    Methods
    -------
    summarize_article():
        Returns a prompt template for summarizing an article and providing a structured JSON output.
    """
    @staticmethod
    def summarize_article():
        """
        Returns a prompt template for summarizing an article and providing a structured JSON output.
        """
        return '''
            Given the article content, 
            summarize the main ideas and provide a 
            structured JSON output summarizing the main ideas.
        '''