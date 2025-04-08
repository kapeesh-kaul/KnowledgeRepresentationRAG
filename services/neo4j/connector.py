from neo4j import GraphDatabase, basic_auth
import logging
from typing import Dict, List, Any, Optional

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
    
    def create_article_relationship(self, from_title: str, to_title: str, rel_type: str = "SEE_ALSO"):
        """
        Create a relationship between two article nodes.

        Args:
            from_title (str): Title of the source article
            to_title (str): Title of the target article
            rel_type (str): The relationship type (default: 'SEE_ALSO')
        """
        with self.driver.session() as session:
            session.execute_write(self._create_article_relationship_tx, from_title, to_title, rel_type)
            logger.info("Created relationship '%s' from '%s' to '%s'", rel_type, from_title, to_title)

    @staticmethod
    def _create_article_relationship_tx(tx, from_title: str, to_title: str, rel_type: str):
        query = (
            "MATCH (a1:Article {title: $from_title}) "
            "MATCH (a2:Article {title: $to_title}) "
            f"CREATE (a1)-[r:{rel_type}]->(a2) "
            "RETURN r"
        )
        tx.run(query, from_title=from_title, to_title=to_title)
    
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
    
    def list_nodes(self, label: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List nodes in the graph with an optional label and limit.
        
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
    def _list_nodes_tx(tx, label: Optional[str], limit: int) -> List[Dict[str, Any]]:
        if label:
            query = f"MATCH (n:{label}) RETURN id(n) AS node_id, n LIMIT $limit"
        else:
            query = "MATCH (n) RETURN id(n) AS node_id, n LIMIT $limit"
        result = tx.run(query, limit=limit)
        return [{"id": record["node_id"], "properties": dict(record["n"])} for record in result]

    def list_relationships(self, limit: int = 10) -> List[Dict[str, Any]]:
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
    def _list_relationships_tx(tx, limit: int) -> List[Dict[str, Any]]:
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
    
    def execute_query(self, query: str, **params) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query on the Neo4j database.

        Args:
            query (str): The Cypher query to execute.
            **params: Parameters to be passed to the query.
            
        Returns:
            list: A list of results from the query.
        """
        # Determine if this is a write operation by checking for write keywords
        is_write = any(keyword in query.upper() for keyword in ['CREATE', 'DELETE', 'SET', 'REMOVE', 'MERGE'])
        
        with self.driver.session() as session:
            if is_write:
                results = session.execute_write(self._execute_query_tx, query, params)
            else:
                results = session.execute_read(self._execute_query_tx, query, params)
            logger.info("Executed query: %s with params: %s", query, params)
            return results
        
    @staticmethod
    def _execute_query_tx(tx, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = tx.run(query, **params)
        return [dict(record) for record in result] 
            
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema and instance information of the Neo4j database.
        
        Returns:
            dict: A dictionary containing database schema and instance information including:
                - labels: List of node labels
                - relationship_types: List of relationship types
                - property_keys: List of property keys
                - database_name: Name of the current database
                - version: Neo4j version
                - edition: Database edition (Community/Enterprise)
        """
        with self.driver.session() as session:
            schema = session.execute_read(self._get_schema_tx)
            return schema

    @staticmethod
    def _get_schema_tx(tx) -> Dict[str, Any]:
        """
        Get the database schema including node labels, relationship types, property keys,
        and instance information.
        """
        # Get all node labels and their properties
        node_schema_query = """
        CALL apoc.meta.schema()
        YIELD value 
        RETURN value
        """
        schema_result = tx.run(node_schema_query).single()["value"]
        
        # Extract node labels and their properties
        node_types = {}
        for label, info in schema_result.items():
            if info["type"] == "node":
                node_types[label] = {
                    "properties": info["properties"],
                    "count": info["count"],
                    "relationships": {}
                }
        
        # Get relationship information
        rel_query = """
        MATCH (a)-[r]->(b)
        WITH type(r) as rel_type, 
             labels(a) as start_labels,
             labels(b) as end_labels,
             properties(r) as props
        RETURN DISTINCT rel_type, start_labels, end_labels, props
        """
        rel_results = tx.run(rel_query)
        
        # Add relationship information to node types
        for record in rel_results:
            rel_type = record["rel_type"]
            start_labels = record["start_labels"]
            end_labels = record["end_labels"]
            props = record["props"]
            
            for start_label in start_labels:
                if start_label in node_types:
                    if rel_type not in node_types[start_label]["relationships"]:
                        node_types[start_label]["relationships"][rel_type] = {
                            "direction": "out",
                            "target_labels": end_labels,
                            "properties": props
                        }
                        
            for end_label in end_labels:
                if end_label in node_types:
                    if rel_type not in node_types[end_label]["relationships"]:
                        node_types[end_label]["relationships"][rel_type] = {
                            "direction": "in", 
                            "target_labels": start_labels,
                            "properties": props
                        }
        
        # Get database instance information
        db_info_query = "CALL db.info()"
        db_info = next(tx.run(db_info_query))
        
        return {
            "node_types": node_types,
            "database_name": db_info.get("name", "unknown"),
            "version": db_info.get("version", "unknown"),
            "edition": db_info.get("edition", "unknown")
        }

    def create_content_chunk(self, content: str, article_title: str, chunk_type: str = "TEXT", chunk_title: str = None):
        """
        Create a content chunk node and link it to its source article.

        Args:
            content (str): The actual content of the chunk
            article_title (str): The title of the source article
            chunk_type (str): The type of chunk (e.g., "TEXT", "LIST", "TABLE")
            chunk_title (str): The title/heading of the chunk

        Returns:
            str: The elementId of the created chunk, or None if article doesn't exist
        """
        with self.driver.session() as session:
            # First check if article exists
            article_exists = session.execute_read(self._check_article_exists_tx, article_title)
            if not article_exists:
                logger.error("Cannot create chunk for non-existent article: '%s'", article_title)
                return None
                
            chunk_id = session.execute_write(self._create_content_chunk_tx, content, article_title, chunk_type, chunk_title)
            logger.info("Created content chunk '%s' for article: '%s'", chunk_title or "untitled", article_title)
            return chunk_id

    @staticmethod
    def _check_article_exists_tx(tx, article_title: str) -> bool:
        query = "MATCH (a:Article {title: $article_title}) RETURN count(a) > 0 as exists"
        result = tx.run(query, article_title=article_title)
        return result.single()["exists"]

    @staticmethod
    def _create_content_chunk_tx(tx, content: str, article_title: str, chunk_type: str, chunk_title: str) -> str:
        query = (
            "MATCH (a:Article {title: $article_title}) "
            "CREATE (c:ContentChunk {content: $content, type: $chunk_type, title: $chunk_title}) "
            "CREATE (a)-[:HAS_CHUNK]->(c) "
            "RETURN elementId(c) as chunk_id"
        )
        result = tx.run(query, content=content, article_title=article_title, chunk_type=chunk_type, chunk_title=chunk_title)
        return result.single()["chunk_id"]

    def create_chunk_relationship(self, from_chunk_id: str, to_chunk_id: str, rel_type: str = "RELATED_TO"):
        """
        Create a relationship between two content chunks.

        Args:
            from_chunk_id (str): elementId of the source chunk
            to_chunk_id (str): elementId of the target chunk
            rel_type (str): The relationship type (default: 'RELATED_TO')
        """
        with self.driver.session() as session:
            session.execute_write(self._create_chunk_relationship_tx, from_chunk_id, to_chunk_id, rel_type)
            logger.info("Created relationship '%s' between chunks %s and %s", rel_type, from_chunk_id, to_chunk_id)

    @staticmethod
    def _create_chunk_relationship_tx(tx, from_chunk_id: str, to_chunk_id: str, rel_type: str):
        query = (
            "MATCH (c1:ContentChunk) WHERE elementId(c1) = $from_chunk_id "
            "MATCH (c2:ContentChunk) WHERE elementId(c2) = $to_chunk_id "
            f"CREATE (c1)-[r:{rel_type}]->(c2) "
            "RETURN r"
        )
        tx.run(query, from_chunk_id=from_chunk_id, to_chunk_id=to_chunk_id)

    def get_chunk_by_title(self, title: str) -> List[Dict[str, Any]]:
        """
        Get content chunks by their title.

        Args:
            title (str): The title to search for

        Returns:
            List[Dict[str, Any]]: List of matching chunks with their elementIds
        """
        with self.driver.session() as session:
            chunks = session.execute_read(self._get_chunk_by_title_tx, title)
            return chunks

    @staticmethod
    def _get_chunk_by_title_tx(tx, title: str) -> List[Dict[str, Any]]:
        query = (
            "MATCH (c:ContentChunk) "
            "WHERE c.title CONTAINS $title "
            "RETURN elementId(c) as id, c"
        )
        result = tx.run(query, title=title)
        return [{"id": record["id"], "properties": dict(record["c"])} for record in result]

    def create_chunk_to_article_relationship(self, chunk_id: str, article_title: str, rel_type: str = "LINKED_TO"):
        """
        Create a relationship between a content chunk and an article it mentions.

        Args:
            chunk_id (str): elementId of the source chunk
            article_title (str): Title of the target article
            rel_type (str): The relationship type (default: 'LINKED_TO')
        """
        with self.driver.session() as session:
            session.execute_write(self._create_chunk_to_article_relationship_tx, chunk_id, article_title, rel_type)
            logger.info("Created relationship '%s' from chunk %s to article '%s'", rel_type, chunk_id, article_title)

    @staticmethod
    def _create_chunk_to_article_relationship_tx(tx, chunk_id: str, article_title: str, rel_type: str):
        query = (
            "MATCH (c:ContentChunk) WHERE elementId(c) = $chunk_id "
            "MATCH (a:Article {title: $article_title}) "
            f"CREATE (c)-[r:{rel_type}]->(a) "
            "RETURN r"
        )
        tx.run(query, chunk_id=chunk_id, article_title=article_title)

    def cleanup_orphaned_chunks(self):
        """
        Remove any content chunks that are not connected to an article.
        """
        with self.driver.session() as session:
            deleted_count = session.execute_write(self._cleanup_orphaned_chunks_tx)
            logger.info("Cleaned up %d orphaned chunks", deleted_count)
            return deleted_count

    @staticmethod
    def _cleanup_orphaned_chunks_tx(tx) -> int:
        query = (
            "MATCH (c:ContentChunk) "
            "WHERE NOT (c)<-[:HAS_CHUNK]-() "
            "DETACH DELETE c "
            "RETURN count(c) as deleted_count"
        )
        result = tx.run(query)
        return result.single()["deleted_count"]

    def clean_database(self):
        """
        Clean the database by deleting all nodes and relationships.
        
        Returns:
            tuple: A tuple containing (nodes_deleted, relationships_deleted)
        """
        with self.driver.session() as session:
            counts = session.execute_write(self._clean_database_tx)
            logger.info("Database cleaned. Deleted %d nodes and %d relationships.", 
                       counts["nodes"], counts["relationships"])
            return counts["nodes"], counts["relationships"]

    @staticmethod
    def _clean_database_tx(tx) -> Dict[str, int]:
        # First count existing nodes and relationships
        count_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->()
        RETURN count(DISTINCT n) as nodes, count(DISTINCT r) as relationships
        """
        counts = tx.run(count_query).single()
        
        # Then delete everything
        delete_query = "MATCH (n) DETACH DELETE n"
        tx.run(delete_query)
        
        return {
            "nodes": counts["nodes"],
            "relationships": counts["relationships"]
        }

    