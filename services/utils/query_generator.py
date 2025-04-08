from typing import Optional, Dict, Any, List
import logging
from services.llm_interface.handler import LLMHandler
from services.llm_interface.prompts import prompts
from services.neo4j.connector import Neo4jConnector
from core.settings import settings

logger = logging.getLogger(__name__)

class QueryGenerator:
    """
    A class to generate Cypher queries using an LLM based on user prompts and database schema.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the query generator with the specified LLM model and Neo4j connection.
        
        Args:
            model (str): The name or identifier of the LLM model to use. If None, uses the model from settings.
        """
        self.llm_handler = LLMHandler(model=model)
        self.neo4j_conn = Neo4jConnector(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        
    def generate_query(self, user_prompt: str, schema: str) -> Optional[str]:
        """
        Generate a Cypher query based on the user prompt and database schema.
        
        Args:
            user_prompt (str): The user's natural language query
            schema (str): The database schema in a readable format
            
        Returns:
            Optional[str]: The generated Cypher query, or None if generation fails
        """
        try:
            # Format the prompt with schema and user query
            full_prompt = f"{prompts.generate_query}\nSchema:\n{schema}\n\nUser Query:\n{user_prompt}"
            
            # Log the full prompt being sent to LLM
            logger.info(f"Sending prompt to LLM:\n{full_prompt}")
            
            # Get the response from the LLM
            response = self.llm_handler.run_prompt(full_prompt)
            
            # Log the raw response from LLM
            logger.info(f"Raw LLM response:\n{response}")
            
            if not response:
                logger.error("Failed to generate query: Empty response from LLM")
                return None
                
            # Extract the query from the response
            # The response should contain a Cypher query between triple backticks
            if "```" in response:
                # Split by triple backticks and get the content between them
                parts = response.split("```")
                for i in range(len(parts)):
                    if i % 2 == 1:  # This is content between backticks
                        content = parts[i].strip()
                        if content.startswith("cypher"):
                            content = content.split("\n", 1)[1]  # Remove the cypher keyword
                        content = content.strip()
                        if content:  # If we found non-empty content
                            logger.info(f"Extracted query:\n{content}")
                            return content
            
            logger.warning("No valid query found in LLM response")
            return None
                
        except Exception as e:
            logger.error(f"Error generating query: {e}")
            return None

    def execute_query_with_retry(self, user_prompt: str, max_retries: int = 5) -> Optional[Dict[str, Any]]:
        """
        Execute a query with retry logic and error feedback to the LLM.
        
        Args:
            user_prompt (str): The user's natural language query
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing query results and interpretation
        """
        schema = self.neo4j_conn.get_schema()
        current_retry = 0
        last_error = None
        
        while current_retry < max_retries:
            try:
                # If this is a retry, include the error message in the prompt
                if last_error:
                    error_prompt = f"Previous query failed with error: {last_error}\nPlease fix the query based on this error message.\nOriginal prompt: {user_prompt}"
                    query = self.generate_query(error_prompt, schema)
                else:
                    query = self.generate_query(user_prompt, schema)
                
                if not query:
                    logger.error("Failed to generate query")
                    break
                    
                results = self.neo4j_conn.execute_query(query)
                interpretation = self.interpret_results(user_prompt, results)
                
                return {
                    "raw_results": results,
                    "interpretation": interpretation,
                    "query": query
                }
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {current_retry + 1} failed: {last_error}")
                current_retry += 1
                
        if current_retry >= max_retries:
            logger.error(f"Failed to execute query after {max_retries} attempts. Last error: {last_error}")
            return None

    def interpret_results(self, user_prompt: str, results: List[Dict[str, Any]]) -> str:
        """
        Interpret the query results using the LLM to provide a natural language response.
        
        Args:
            user_prompt (str): The original user query
            results (List[Dict[str, Any]]): The query results from Neo4j
            
        Returns:
            str: Natural language interpretation of the results
        """
        try:
            # Format results into a more readable string
            formatted_results = []
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    formatted_result = []
                    for key, value in result.items():
                        if isinstance(value, dict):
                            formatted_result.append(f"{key}: {value.get('properties', {}).get('title', 'N/A')}")
                        else:
                            formatted_result.append(f"{key}: {value}")
                    formatted_results.append(f"Result {i}: " + ", ".join(formatted_result))
                else:
                    formatted_results.append(f"Result {i}: {str(result)}")
            
            # Format the prompt with the original question and formatted results
            full_prompt = f"{prompts.interpret_results}\n\nQuestion: {user_prompt}\n\nQuery Results:\n" + "\n".join(formatted_results)
            
            logger.info(f"Interpreting results for prompt: {full_prompt}")

            # Get the interpretation from the LLM
            interpretation = self.llm_handler.run_prompt(full_prompt)
            
            logger.info(f"Raw interpretation from LLM: {interpretation}")
            
            if not interpretation:
                logger.error("Failed to interpret results: Empty response from LLM")
                return "I apologize, but I was unable to interpret the results."
                
            return interpretation.strip()
                
        except Exception as e:
            logger.error(f"Error interpreting results: {e}")
            return f"I apologize, but I encountered an error while interpreting the results: {str(e)}"

    def close(self):
        """Close the Neo4j connection."""
        self.neo4j_conn.close()
