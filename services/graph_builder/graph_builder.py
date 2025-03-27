import logging
from services.wikimedia.search import WikipediaSearcher
from services.wikimedia.scraper import WikipediaScraper
from services.neo4j.connector import Neo4jConnector

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.neo4j_conn = Neo4jConnector(neo4j_uri, neo4j_user, neo4j_password)
        self.searcher = WikipediaSearcher()
        self.scraper = WikipediaScraper()

    def build_graph(self, search_term):
        if not search_term:
            logger.error("No search term entered. Exiting.")
            return

        try:
            # Search for pages matching the search term.
            titles = self.searcher.search_pages(search_term, results=10)
            if not titles:
                logger.info("No pages found for '%s'.", search_term)
                return

            for title in titles:
                # Attempt to fetch the page.
                try:
                    page = self.scraper.fetch_page(title)
                except Exception as e:
                    logger.error("Skipping page '%s' due to error: %s", title, e)
                    continue

                article_url = page.url
                self.neo4j_conn.create_article_node(page.title, article_url)

                # Extract the 'See also' links from the page content.
                see_also_titles = self.scraper.extract_see_also(page)
                for link_title in see_also_titles:
                    try:
                        linked_page = self.scraper.fetch_page(link_title)
                        linked_url = linked_page.url
                    except Exception as e:
                        logger.error(
                            "Skipping 'See also' link '%s' due to error: %s", link_title, e
                        )
                        continue
                    self.neo4j_conn.create_article_node(linked_page.title, linked_url)
                    self.neo4j_conn.create_relationship(
                        page.title, linked_page.title, "SEE_ALSO"
                    )

        except Exception as e:
            logger.exception("An error occurred: %s", e)
        finally:
            self.neo4j_conn.close() 