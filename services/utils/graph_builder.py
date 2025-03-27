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
            logger.error("No search term provided. Please provide a valid search term and try again.")
            raise ValueError("No search term provided")

        try:
            # Search for pages matching the search term.
            titles = self.searcher.search_pages(search_term, results=5)
            if not titles:
                logger.info("No pages found for '%s'.", search_term)
                return

            # First, create all article nodes
            article_nodes = {}
            for title in titles:
                try:
                    page = self.scraper.fetch_page(title)
                    article_url = page.url
                    self.neo4j_conn.create_article_node(page.title, article_url)
                    article_nodes[page.title] = page
                except Exception as e:
                    logger.error("Skipping page '%s' due to error: %s", title, e)
                    continue

            # Then process each article's content and relationships
            for title, page in article_nodes.items():
                # Extract and create content chunks
                chunks = self.scraper.extract_content_chunks(page)
                chunk_ids = []
                for chunk in chunks:
                    chunk_id = self.neo4j_conn.create_content_chunk(
                        chunk['content'],
                        page.title,
                        chunk['type'],
                        chunk['title']
                    )
                    if chunk_id:
                        chunk_ids.append(chunk_id)

                # Extract the 'See also' links from the page content.
                see_also_titles = self.scraper.extract_see_also(page)
                for link_title in see_also_titles:
                    try:
                        linked_page = self.scraper.fetch_page(link_title)
                        linked_url = linked_page.url
                        self.neo4j_conn.create_article_node(linked_page.title, linked_url)
                        # Create SEE_ALSO relationship between articles
                        self.neo4j_conn.create_article_relationship(page.title, linked_page.title, "SEE_ALSO")
                    except Exception as e:
                        logger.error(
                            "Skipping 'See also' link '%s' due to error: %s", link_title, e
                        )
                        continue

                # Extract the linked pages from the page content.
                linked_pages = self.scraper.extract_linked_pages(page)
                
                max_pages = min(10, len(linked_pages))
                for linked_page_title in linked_pages[:max_pages]:
                    try:
                        linked_page = self.scraper.fetch_page(linked_page_title)
                        linked_url = linked_page.url
                        self.neo4j_conn.create_article_node(linked_page.title, linked_url)

                        # Create LINKED_TO relationships from chunks to the mentioned article
                        for chunk_id in chunk_ids:
                            self.neo4j_conn.create_chunk_to_article_relationship(chunk_id, linked_page.title, "LINKED_TO")
                    except Exception as e:
                        logger.error(
                            "Skipping linked page '%s' due to error: %s", linked_page_title, e
                        )
                        continue

            # Clean up any orphaned chunks that might have been created
            orphaned_count = self.neo4j_conn.cleanup_orphaned_chunks()
            if orphaned_count > 0:
                logger.warning("Cleaned up %d orphaned chunks", orphaned_count)

        except Exception as e:
            logger.critical(f"An unexpected error occurred: {e}")
            raise
        finally:
            self.neo4j_conn.close()
