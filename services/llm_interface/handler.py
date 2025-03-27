import logging
from ollama import chat

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

    def run_prompt(self, prompt: str, **kwargs : dict) -> str:
        """
        Run a prompt against the LLM.

        Args:
            prompt (str): The prompt text to send to the LLM
            **kwargs: Additional keyword arguments to include in the prompt

        Returns:
            str: The LLM response text, or None if an error occurs
        """
        if not prompt:
            logger.error("Empty prompt provided")
            return None

        try:
            # Format kwargs into a string if provided
            kwargs_str = str(kwargs) if kwargs else ""

            response = chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": kwargs_str}
                ]
            )

            if not response:
                logger.warning("Empty response received from LLM")
                return None

            return response.get("message", {}).get("content")

        except Exception as e:
            logger.error(f"Error running prompt: {e}")
            return None
