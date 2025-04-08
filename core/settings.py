import os
from pathlib import Path
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(override=True)
        
        # Configuration for Neo4j
        self.NEO4J_URI = os.getenv("NEO4J_URI")
        self.NEO4J_USER = os.getenv("NEO4J_USERNAME")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
        
        # Configuration for LLM
        self.LLM_MODEL = os.getenv("LLM_MODEL")
        
        # Configuration for Corpus Storage
        self.CORPUS_STORAGE_PATH = Path('.data/corpus')
        # Ensure the directory exists
        self.CORPUS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Create a singleton instance of Settings
settings = Settings() 