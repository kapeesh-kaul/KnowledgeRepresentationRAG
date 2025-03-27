import logging
from core.settings import settings
from services.graph_builder.graph_builder import GraphBuilder
from services.llm_interface import LLMHandler
from services.llm_interface.prompts import prompts
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """
    CLI tool for interacting with a Neo4j database.
    
    """

@cli.command(
    help="Build a graph in the Neo4j database from Wikipedia articles."
)
@click.option('--search_term', prompt="Enter a search term for Wikipedia: ", type=str, help="The search term to use for Wikipedia.")
def build_graph(search_term):
    graph_builder = GraphBuilder(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    graph_builder.build_graph(search_term)

if __name__ == "__main__":
    cli()
