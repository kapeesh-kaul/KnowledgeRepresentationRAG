import os
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

# Create a singleton instance of Settings
settings = Settings() 