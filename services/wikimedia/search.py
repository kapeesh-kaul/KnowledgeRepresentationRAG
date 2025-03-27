import wikipedia
import logging

logger = logging.getLogger(__name__)

class WikipediaSearcher:
    """
    Uses the wikipedia library to search for Wikipedia pages.
    """
    def search_pages(self, query: str, results: int = 10) -> list:
        """
        Search for pages matching the query.

        Args:
            query (str): The search term.
            results (int): Maximum number of search results.

        Returns:
            list: A list of page titles.
        """
        try:
            titles = wikipedia.search(query, results=results)
            logger.info("Found %d pages for query '%s'.", len(titles), query)
            return titles
        except Exception as e:
            logger.error("Error during Wikipedia search: %s", e)
            raise
