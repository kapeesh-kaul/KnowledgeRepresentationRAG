import logging
from core.settings import settings
from services.utils.graph_builder import GraphBuilder
import click
from services.neo4j.connector import Neo4jConnector
from services.utils.query_generator import QueryGenerator
from services.evaluation.metrics import EvaluationMetrics
import json
import time
from typing import Dict, Any


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
@click.option('--search_term', prompt="Enter a search term for Wikipedia", type=str, help="The search term to use for Wikipedia.")
def build_graph(search_term : str):
    graph_builder = GraphBuilder(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    graph_builder.build_graph(search_term)

@cli.command(
    help = "Clear the Neo4j database."
)
def clear_database():
    neo4j_conn = Neo4jConnector(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    neo4j_conn.clean_database()

@cli.command(
    help = "Get the schema of the Neo4j database."
)
@click.option('--user_prompt', prompt="Enter a user prompt", type=str, help="The user prompt to use for the query.")
def execute_query(user_prompt: str):
    query_generator = QueryGenerator()
    try:
        results = query_generator.execute_query_with_retry(user_prompt)
        if results is not None:
            print("\nAnswer:")
            print(results["interpretation"])
            # print("\nQuery used:")
            # print(results["query"])
            # print("\nRaw results:")
            # print(results["raw_results"])
        else:
            print("Failed to execute query after multiple attempts.")
    finally:
        query_generator.close()

@cli.command(
    help="Evaluate response accuracy using test cases"
)
@click.option('--test_file', type=str, default='test_cases.json', help="JSON file containing test cases")
@click.option('--output_file', type=str, default='evaluation_results.json', help="File to save evaluation results")
def evaluate_responses(test_file: str, output_file: str):
    """
    Evaluate the accuracy of query responses using predefined test cases.
    """
    try:
        with open(test_file, 'r') as f:
            test_data = json.load(f)
        
        query_generator = QueryGenerator()
        metrics = EvaluationMetrics()
        results = {
            'categories': [],
            'overall_metrics': {
                'total_cases': 0,
                'average_scores': {}
            }
        }
        
        total_scores = {
            'similarity': 0,
            'rouge_l': 0,
            'keyword': 0,
            'total': 0
        }
        
        for category in test_data['categories']:
            category_results = {
                'name': category['name'],
                'description': category['description'],
                'test_cases': []
            }
            
            for test_case in category['test_cases']:
                prompt = test_case['prompt']
                expected = test_case['expected_answer']
                keywords = test_case.get('keywords', [])
                
                logger.info(f"\nProcessing test case: {prompt}")
                
                try:
                    start_time = time.time()
                    response = query_generator.execute_query_with_retry(prompt)
                    generation_time = time.time() - start_time
                    
                    if response:
                        actual = response["interpretation"]
                        evaluation = metrics.evaluate_response(actual, expected, keywords)
                        
                        # Update total scores
                        total_scores['similarity'] += evaluation['similarity_score']
                        total_scores['rouge_l'] += evaluation['rouge_scores']['rouge-l']
                        total_scores['keyword'] += evaluation['keyword_score']
                        total_scores['total'] += evaluation['total_score']
                        
                        case_result = {
                            'prompt': prompt,
                            'expected': expected,
                            'actual': actual,
                            'metrics': evaluation,
                            'generation_time': generation_time
                        }
                        category_results['test_cases'].append(case_result)
                        
                        logger.info(f"Score: {evaluation['total_score']:.2f}")
                        logger.info(f"Generation time: {generation_time:.2f}s")
                
                except Exception as e:
                    logger.error(f"Error processing test case: {str(e)}")
            
            results['categories'].append(category_results)
        
        # Calculate overall metrics
        total_cases = sum(len(cat['test_cases']) for cat in results['categories'])
        if total_cases > 0:
            results['overall_metrics']['total_cases'] = total_cases
            results['overall_metrics']['average_scores'] = {
                'similarity': total_scores['similarity'] / total_cases,
                'rouge_l': total_scores['rouge_l'] / total_cases,
                'keyword': total_scores['keyword'] / total_cases,
                'total': total_scores['total'] / total_cases
            }
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        logger.info("\nEvaluation Summary:")
        logger.info(f"Total test cases: {total_cases}")
        logger.info(f"Average similarity score: {results['overall_metrics']['average_scores']['similarity']:.2f}")
        logger.info(f"Average ROUGE-L score: {results['overall_metrics']['average_scores']['rouge_l']:.2f}")
        logger.info(f"Average keyword score: {results['overall_metrics']['average_scores']['keyword']:.2f}")
        logger.info(f"Average total score: {results['overall_metrics']['average_scores']['total']:.2f}")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
    finally:
        query_generator.close()

if __name__ == "__main__":
    cli()
     
