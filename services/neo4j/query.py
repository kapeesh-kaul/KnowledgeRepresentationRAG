import click
from core.settings import settings
from typing import Dict, Any, List
from .connector import Neo4jConnector

connector = Neo4jConnector(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)


def create_node(label: str, props: Dict[str, Any]) -> int:
    """Create a new node with the given label and properties."""
    query = f"CREATE (n:{label} $props) RETURN id(n) AS node_id"
    result = connector.execute_query(query, props=props)
    return result[0]["node_id"] if result else None

def read_nodes(label: str = None) -> List[Dict[str, Any]]:
    """Read nodes from the database, optionally filtered by label."""
    if label:
        query = f"MATCH (n:{label}) RETURN id(n) AS node_id, n"
    else:
        query = "MATCH (n) RETURN id(n) AS node_id, n"
    result = connector.execute_query(query)
    return [{"id": record["node_id"], "properties": dict(record["n"])} for record in result]

def update_node(node_id: int, props: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing node with new properties."""
    query = "MATCH (n) WHERE id(n) = $node_id SET n += $props RETURN n"
    result = connector.execute_query(query)
    return dict(result[0]["n"]) if result else None

def delete_node(node_id: int):
    """Delete a node by its ID."""
    query = "MATCH (n) WHERE id(n) = $node_id DETACH DELETE n"
    connector.execute_query(query)

def clean_database():
    """Delete all nodes and relationships from the database."""
    query = "MATCH (n) DETACH DELETE n"
    connector.execute_query(query)


# CLI Application with Click
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
    node_id = create_node(label, props)
    if node_id is not None:
        click.echo(f"Node created with ID: {node_id}")
    else:
        click.echo("Failed to create node.")

@cli.command(help="Read nodes from the database. Optionally filter by label.")
@click.option('--label', default=None, help="Optional label to filter nodes.")
def read(label):
    nodes = read_nodes(label)
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
    updated = update_node(node_id, props)
    if updated:
        click.echo(f"Node updated successfully: {updated}")
    else:
        click.echo("Node not found or update failed.")

@cli.command(help="Delete a node by its internal ID.")
@click.option('--id', 'node_id', prompt="Node ID", type=int, help="ID of the node to delete.")
def delete(node_id):
    if click.confirm(f"Are you sure you want to delete node with ID {node_id}?"):
        delete_node(node_id)
        click.echo("Node deleted.")
    else:
        click.echo("Deletion cancelled.")

@cli.command(help="Clean the database by deleting all nodes and relationships.")
def clean():
    confirmation = click.prompt("WARNING: This will delete ALL nodes and relationships. Type 'yes' to confirm", type=str)
    if confirmation.lower() == 'yes':
        clean_database()
        click.echo("Database cleaned.")
    else:
        click.echo("Operation cancelled.")

@cli.command(help="List a specified number of nodes, optionally filtered by label.")
@click.option('--limit', default=25, help="Number of nodes to list.")
@click.option('--label', default=None, help="Optional label to filter nodes.")
def list_nodes(limit, label):
    nodes = connector.list_nodes(label, limit)
    if not nodes:
        click.echo("No nodes found.")
    else:
        for node in nodes:
            click.echo(f"ID: {node['id']}, Properties: {node['properties']}")

@cli.command(help="List a specified number of relationships.")
@click.option('--limit', default=25, help="Number of relationships to list.")
def list_relationships(limit):
    rels = connector.list_relationships(limit)
    if not rels:
        click.echo("No relationships found.")
    else:
        for rel in rels:
            click.echo(f"ID: {rel['id']}, Type: {rel['type']}, Properties: {rel['properties']}")

@cli.command(help="Get the database schema information.")
def schema():
    schema_info = connector.get_schema()
    click.echo("Database Schema Information:")
    click.echo(f"Database Name: {schema_info['database_name']}")
    click.echo(f"Version: {schema_info['version']}")
    click.echo(f"Edition: {schema_info['edition']}")
    click.echo("\nLabels:")
    for label in schema_info['labels']:
        click.echo(f"  - {label}")
    click.echo("\nRelationship Types:")
    for rel_type in schema_info['relationship_types']:
        click.echo(f"  - {rel_type}")
    click.echo("\nProperty Keys:")
    for prop_key in schema_info['property_keys']:
        click.echo(f"  - {prop_key}")

if __name__ == "__main__":
    try:
        cli()
    finally:
        connector.close() 