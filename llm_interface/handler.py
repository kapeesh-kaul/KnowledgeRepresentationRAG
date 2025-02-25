import logging
from ollama import chat  # Ensure you have installed ollama via pip

logger = logging.getLogger(__name__)

class LLMHandler:
    """
    Handles sending prompts to an LLM using the Ollama Python library.
    The handler accepts a required prompt and an optional query response,
    which is formatted and appended to the prompt.
    """
    def __init__(self, model: str = "llama3.2:3b-instruct-fp16"):
        """
        Initialize the handler with the model to use.
        
        Args:
            model (str): The name or identifier of the LLM model.
        """
        self.model = model

    def process_inputs(self, prompt_input: str, query_response=None) -> str:
        """
        Process two inputs: a required prompt string and an optional query response.
        The query response is formatted and appended to the prompt before being sent
        to the LLM.

        Args:
            prompt_input (str): The main prompt text.
            query_response (dict or list, optional): Structured query response data
                (for example, from a Neo4j query) to be formatted and included.
        
        Returns:
            str: The generated LLM response.
        """
        if query_response:
            formatted_data = self.format_data(query_response)
            full_prompt = f"{prompt_input}\n{formatted_data}"
        else:
            full_prompt = prompt_input

        logger.info("Sending prompt to LLM:\n%s", full_prompt)
        try:
            response = chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': full_prompt,
                }]
            )
            # Access the generated content from the response.
            result = response.message.content
            logger.info("Received LLM response.")
            return result
        except Exception as e:
            logger.error("Error querying LLM: %s", e)
            raise

    def format_data(self, data) -> str:
        """
        Convert structured query data (dict or list) into a formatted string.
        
        Args:
            data (dict or list): The data to format.
        
        Returns:
            str: A formatted string representation of the data.
        """
        if isinstance(data, dict):
            # Format as key: value pairs.
            return "\n".join([f"{key}: {value}" for key, value in data.items()])
        elif isinstance(data, list):
            # Format each element on a new line.
            return "\n".join(map(str, data))
        else:
            return str(data)
