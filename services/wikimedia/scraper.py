import wikipedia
import re
import logging

logger = logging.getLogger(__name__)

class WikipediaScraper:
    """
    Uses the wikipedia library to fetch a page and extract its 'See also' section.
    """
    def fetch_page(self, title: str):
        """
        Retrieve a wikipedia page object for a given title.

        Args:
            title (str): The article title.

        Returns:
            wikipedia.WikipediaPage: The page object.
        """
        try:
            page = wikipedia.page(title)
            logger.info("Fetched page for '%s'.", title)
            return page
        except Exception as e:
            logger.error("Error fetching page for '%s': %s", title, e)
            raise

    def extract_see_also(self, page) -> list:
        """
        Extract the 'See also' section from the page's content.

        Args:
            page (wikipedia.WikipediaPage): The page object.

        Returns:
            list: A list of article titles found in the 'See also' section.
        """
        content = page.content
        # Look for a section starting with "== See also =="
        match = re.search(r'==\s*See also\s*==(.*?)(==|$)', content, re.DOTALL | re.IGNORECASE)
        if not match:
            logger.info("No 'See also' section found for '%s'.", page.title)
            return []
        see_also_section = match.group(1).strip()
        # Split the section into lines and clean each line.
        lines = see_also_section.split('\n')
        links = []
        for line in lines:
            # Remove bullet markers and extra whitespace.
            line = line.strip().lstrip("*-").strip()
            if line:
                # In many pages the section is a simple list of article titles.
                links.append(line)
        logger.info("Extracted %d 'See also' links from '%s'.", len(links), page.title)
        return links
