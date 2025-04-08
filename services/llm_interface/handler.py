import logging
from ollama import chat
from core.settings import settings

logger = logging.getLogger(__name__)

class LLMHandler:
    """
    Handles sending prompts to an LLM using the Ollama Python library.
    The handler accepts a required prompt and an optional query response,
    which is formatted and appended to the prompt.
    """
    def __init__(self, model: str = None):
        """
        Initialize the handler with the model to use.
        
        Args:
            model (str): The name or identifier of the LLM model. If None, uses the model from settings.
        """
        self.model = model or settings.LLM_MODEL

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
            # Combine prompt and kwargs into a single message
            full_prompt = prompt
            if kwargs:
                full_prompt += "\n\nAdditional context:\n" + str(kwargs)

            response = chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )

            if not response:
                logger.warning("Empty response received from LLM")
                return None

            return response.get("message", {}).get("content")

        except Exception as e:
            logger.error(f"Error running prompt: {e}")
            return None
