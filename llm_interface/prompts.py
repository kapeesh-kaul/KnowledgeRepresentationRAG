class Prompts:
    """
    A class to handle various prompt templates for language model interactions.

    Methods
    -------
    summarize_article():
        Returns a prompt template for summarizing an article and providing a plain text output.
    """
    @staticmethod
    def summarize_article():
        """
        Returns a prompt template for summarizing an article and providing a plain text output.
        """
        return '''
            Given the article content, 
            summarize the main ideas and provide a 
            plain text output summarizing the main ideas.
        '''