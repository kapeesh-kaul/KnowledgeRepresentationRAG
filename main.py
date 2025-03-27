import logging
from core.settings import settings
from services.graph_builder.graph_builder import GraphBuilder
from services.llm_interface import LLMHandler
from services.llm_interface.prompts import prompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    search_term = input("Enter a search term for Wikipedia: ").strip()
    graph_builder = GraphBuilder(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)

    graph_builder.build_graph(search_term)

    def test_llm():
        handler = LLMHandler()
        response = handler.process_inputs(
            prompts.summarize_article, graph_builder.neo4j_conn.list_nodes()
        )
        logger.info("LLM response: %s", response)

    # test_llm()


if __name__ == "__main__":
    main()
