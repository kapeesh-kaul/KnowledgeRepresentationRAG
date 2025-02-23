import os
import click
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password_here")

# Create a Neo4j driver instance
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ----------------------------------------
# Helper Functions for CRUD and Listing
# ----------------------------------------
def create_node(tx, label, props):
    query = f"CREATE (n:{label} $props) RETURN id(n) AS node_id"
    result = tx.run(query, props=props)
    record = result.single()
    return record["node_id"]

def read_nodes(tx, label=None):
    if label:
        query = f"MATCH (n:{label}) RETURN id(n) AS node_id, n"
    else:
        query = "MATCH (n) RETURN id(n) AS node_id, n"
    result = tx.run(query)
    return [{"id": record["node_id"], "properties": dict(record["n"])} for record in result]

def update_node(tx, node_id, props):
    query = "MATCH (n) WHERE id(n) = $node_id SET n += $props RETURN n"
    result = tx.run(query, node_id=node_id, props=props)
    record = result.single()
    return dict(record["n"]) if record else None

def delete_node(tx, node_id):
    query = "MATCH (n) WHERE id(n) = $node_id DETACH DELETE n"
    tx.run(query, node_id=node_id)

def clean_database(tx):
    query = "MATCH (n) DETACH DELETE n"
    tx.run(query)

def list_n_nodes(tx, label, limit):
    if label:
        query = f"MATCH (n:{label}) RETURN id(n) AS node_id, n LIMIT $limit"
    else:
        query = "MATCH (n) RETURN id(n) AS node_id, n LIMIT $limit"
    result = tx.run(query, limit=limit)
    return [{"id": record["node_id"], "properties": dict(record["n"])} for record in result]

def list_n_relationships(tx, limit):
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

# -------------------------
# CLI Application with Click
# -------------------------
@click.group()
def cli():
    """
    CLI tool for interacting with a Neo4j database.
    
    Provides full CRUD operations, maintenance tasks,
    and commands to list nodes and relationships.
    """
    pass

@cli.command(help="Create a new node with a label and properties.")
@click.option('--label', prompt="Node label", help="Label for the new node.")
@click.option('--property', 'properties', multiple=True, help="Properties in key=value format. Use multiple times.")
def create(label, properties):
    props = {}
    for prop in properties:
        if '=' in prop:
            key, value = prop.split('=', 1)
            props[key.strip()] = value.strip()
        else:
            click.echo(f"Invalid property format: {prop}. Use key=value.")
            return
    with driver.session() as session:
        node_id = session.execute_write(create_node, label, props)
        click.echo(f"Node created with ID: {node_id}")

@cli.command(help="Read nodes from the database. Optionally filter by label.")
@click.option('--label', default=None, help="Optional label to filter nodes.")
def read(label):
    with driver.session() as session:
        nodes = session.execute_read(read_nodes, label)
        if not nodes:
            click.echo("No nodes found.")
        else:
            for node in nodes:
                click.echo(f"ID: {node['id']}, Properties: {node['properties']}")

@cli.command(help="Update an existing node given its internal ID and new properties.")
@click.option('--id', 'node_id', prompt="Node ID", type=int, help="ID of the node to update.")
@click.option('--property', 'properties', multiple=True, help="New properties in key=value format. Use multiple times.")
def update(node_id, properties):
    props = {}
    for prop in properties:
        if '=' in prop:
            key, value = prop.split('=', 1)
            props[key.strip()] = value.strip()
        else:
            click.echo(f"Invalid property format: {prop}. Use key=value.")
            return
    with driver.session() as session:
        updated = session.execute_write(update_node, node_id, props)
        if updated:
            click.echo(f"Node updated successfully: {updated}")
        else:
            click.echo("Node not found or update failed.")

@cli.command(help="Delete a node by its internal ID.")
@click.option('--id', 'node_id', prompt="Node ID", type=int, help="ID of the node to delete.")
def delete(node_id):
    if click.confirm(f"Are you sure you want to delete node with ID {node_id}?"):
        with driver.session() as session:
            session.execute_write(delete_node, node_id)
        click.echo("Node deleted.")
    else:
        click.echo("Deletion cancelled.")

@cli.command(help="Clean the database by deleting all nodes and relationships.")
def clean():
    confirmation = click.prompt("WARNING: This will delete ALL nodes and relationships. Type 'yes' to confirm", type=str)
    if confirmation.lower() == 'yes':
        with driver.session() as session:
            session.execute_write(clean_database)
        click.echo("Database cleaned.")
    else:
        click.echo("Operation cancelled.")

@cli.command(help="List a specified number of nodes, optionally filtered by label.")
@click.option('--limit', default=25, help="Number of nodes to list.")
@click.option('--label', default=None, help="Optional label to filter nodes.")
def list_nodes(limit, label):
    with driver.session() as session:
        nodes = session.execute_read(list_n_nodes, label, limit)
        if not nodes:
            click.echo("No nodes found.")
        else:
            for node in nodes:
                click.echo(f"ID: {node['id']}, Properties: {node['properties']}")

@cli.command(help="List a specified number of relationships.")
@click.option('--limit', default=25, help="Number of relationships to list.")
def list_relationships(limit):
    with driver.session() as session:
        rels = session.execute_read(list_n_relationships, limit)
        if not rels:
            click.echo("No relationships found.")
        else:
            for rel in rels:
                click.echo(f"ID: {rel['id']}, Type: {rel['type']}, Properties: {rel['properties']}")

if __name__ == "__main__":
    try:
        cli()
    finally:
        driver.close()
