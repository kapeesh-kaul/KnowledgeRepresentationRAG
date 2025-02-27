import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration for Neo4j from .env
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password_here")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from wikimedia.search import WikipediaSearcher
from wikimedia.scraper import WikipediaScraper
from wikimedia.neo4j_connector import Neo4jConnector

def main():
    search_term = input("Enter a search term for Wikipedia: ").strip()
    if not search_term:
        logger.error("No search term entered. Exiting.")
        return

    searcher = WikipediaSearcher()
    scraper = WikipediaScraper()
    neo4j_conn = Neo4jConnector(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Search for pages matching the search term.
        titles = searcher.search_pages(search_term, results=10)
        if not titles:
            logger.info("No pages found for '%s'.", search_term)
            return

        for title in titles:
            # Attempt to fetch the page.
            try:
                page = scraper.fetch_page(title)
            except Exception as e:
                logger.error("Skipping page '%s' due to error: %s", title, e)
                continue

            article_url = page.url
            neo4j_conn.create_article_node(page.title, article_url)

            # Extract the 'See also' links from the page content.
            see_also_titles = scraper.extract_see_also(page)
            for link_title in see_also_titles:
                try:
                    linked_page = scraper.fetch_page(link_title)
                    linked_url = linked_page.url
                except Exception as e:
                    logger.error("Skipping 'See also' link '%s' due to error: %s", link_title, e)
                    continue
                neo4j_conn.create_article_node(linked_page.title, linked_url)
                neo4j_conn.create_relationship(page.title, linked_page.title, "SEE_ALSO")

        def test_llm():
            from llm_interface import LLMHandler
            from llm_interface.prompts import Prompts
            handler = LLMHandler()
            response = handler.process_inputs(
                Prompts.summarize_article(), 
                neo4j_conn.list_nodes()
            )
            logger.info("LLM response: %s", response)
        test_llm()

    except Exception as e:
        logger.exception("An error occurred: %s", e)
    finally:
        neo4j_conn.close()

if __name__ == "__main__":
    main()
