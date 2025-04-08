from typing import List, Dict, Optional
import logging
from services.utils.corpus_builder import CorpusBuilder, TextChunk
from services.evaluation.metrics import EvaluationMetrics

logger = logging.getLogger(__name__)

class SearchEngine:
    """
    Handles search and retrieval operations on a corpus.
    """
    
    def __init__(self, corpus_builder: CorpusBuilder):
        """
        Initialize the search engine with a corpus builder.
        
        Args:
            corpus_builder (CorpusBuilder): The corpus builder instance
        """
        self.corpus_builder = corpus_builder
        self.evaluator = EvaluationMetrics()
        
    def search(self, query: str, top_k: int = 5) -> List[TextChunk]:
        """
        Search the corpus for relevant chunks.
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            List[TextChunk]: Most relevant chunks
        """
        return self.corpus_builder.hybrid_search(query, top_k=top_k)