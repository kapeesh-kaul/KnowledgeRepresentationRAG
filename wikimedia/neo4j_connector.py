from neo4j import GraphDatabase, basic_auth
import logging

logger = logging.getLogger(__name__)

class Neo4jConnector:
    """
    Handles Neo4j operations to create article nodes and relationships.
    """
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
        logger.info("Connected to Neo4j at %s", uri)
    
    def close(self):
        self.driver.close()
        logger.info("Closed Neo4j connection.")
    
    def create_article_node(self, title: str, url: str):
        """
        Merge an article node into the graph.

        Args:
            title (str): The article title.
            url (str): The article URL.
        """
        with self.driver.session() as session:
            session.execute_write(self._create_article_node_tx, title, url)
            logger.info("Created/updated node for article: '%s'", title)
    
    @staticmethod
    def _create_article_node_tx(tx, title: str, url: str):
        query = (
            "MERGE (a:Article {title: $title}) "
            "SET a.url = $url "
            "RETURN a"
        )
        tx.run(query, title=title, url=url)
    
    def create_relationship(self, from_title: str, to_title: str, rel_type: str = "SEE_ALSO"):
        """
        Create a relationship between two article nodes.

        Args:
            from_title (str): Title of the source article.
            to_title (str): Title of the target article.
            rel_type (str): The relationship type (default: 'SEE_ALSO').
        """
        with self.driver.session() as session:
            session.execute_write(self._create_relationship_tx, from_title, to_title, rel_type)
            logger.info("Created relationship '%s' from '%s' to '%s'.", rel_type, from_title, to_title)
    
    @staticmethod
    def _create_relationship_tx(tx, from_title: str, to_title: str, rel_type: str):
        query = (
            "MATCH (a:Article {title: $from_title}) "
            "MATCH (b:Article {title: $to_title}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "RETURN r"
        )
        tx.run(query, from_title=from_title, to_title=to_title)
    
    def list_nodes(self, label: str = None, limit: int = 10):
        """
        List nodes in the
        graph with an optional label and limit.
        Args:
            label (str): The label of the nodes to list (default: None).
            limit (int): The maximum number of nodes to return (default: 10).
        Returns:
            list: A list of nodes with their properties.
        """
        with self.driver.session() as session:
            nodes = session.execute_read(self._list_nodes_tx, label, limit)
            logger.info("Listed %d nodes.", len(nodes))
            return nodes
    @staticmethod
    def _list_nodes_tx(tx, label: str, limit: int):
        if label:
            query = f"MATCH (n:{label}) RETURN id(n) AS node_id, n LIMIT $limit"
        else:
            query = "MATCH (n) RETURN id(n) AS node_id, n LIMIT $limit"
        result = tx.run(query, limit=limit)
        return [{"id": record["node_id"], "properties": dict(record["n"])} for record in result]
    def list_relationships(self, limit: int = 10):
        """
        List relationships in the graph with an optional limit.
        Args:
            limit (int): The maximum number of relationships to return (default: 10).   
        Returns:   
            list: A list of relationships with their properties.
        """
        with self.driver.session() as session:
            rels = session.execute_read(self._list_relationships_tx, limit)
            logger.info("Listed %d relationships.", len(rels))
            return rels
    @staticmethod
    def _list_relationships_tx(tx, limit: int):
        query = "MATCH ()-[r]->() RETURN id(r) AS rel_id, r LIMIT $limit"
        result = tx.run(query, limit=limit)
        rels = []
        for record in result:
            r = record["r"]
            rels.append({
                "id": record["rel_id"],
                "type": r.type,  # Relationship type
                "properties": dict(r)
            })
        return rels
