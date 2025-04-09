import json
import logging
import re
from typing import Any
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

    def _remove_think_tags(self, text: str) -> str:
        """
        Remove <think> tags and their contents from the text.
        
        Args:
            text (str): The text to process
            
        Returns:
            str: Text with think tags removed
        """
        if not text:
            return text
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

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

            content = response.get("message", {}).get("content")
            return self._remove_think_tags(content)

        except Exception as e:
            logger.error(f"Error running prompt: {e}")
            return None
        
    def run_prompt_with_data(self, prompt: str, data: dict | list | str) -> str:
        """
        Run a prompt against the LLM with additional data.
        """
        if not prompt or not data:
            logger.error("Empty prompt or data provided")
            return None
        
        try:
            # Combine prompt and data into a single message
            full_prompt = prompt
            if data:
                full_prompt += "\n\nData:\n" + str(data)

            response = chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )

            if not response:
                logger.warning("Empty response received from LLM")
                return None

            content = response.get("message", {}).get("content")
            return self._remove_think_tags(content)
        
        except Exception as e:
            logger.error(f"Error running prompt with data: {e}")
            return None
            