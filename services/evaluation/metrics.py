from difflib import SequenceMatcher
from rouge import Rouge
from typing import List, Dict, Any
import numpy as np

class EvaluationMetrics:
    def __init__(self):
        self.rouge = Rouge()
        
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def calculate_rouge_scores(self, generated: str, reference: str) -> Dict[str, float]:
        """Calculate ROUGE scores between generated and reference text."""
        try:
            scores = self.rouge.get_scores(generated, reference)[0]
            return {
                'rouge-1': scores['rouge-1']['f'],
                'rouge-2': scores['rouge-2']['f'],
                'rouge-l': scores['rouge-l']['f']
            }
        except Exception:
            return {'rouge-1': 0.0, 'rouge-2': 0.0, 'rouge-l': 0.0}
    
    def calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate score based on presence of keywords in text."""
        if not keywords:
            return 1.0
        text_lower = text.lower()
        return sum(1 for k in keywords if k.lower() in text_lower) / len(keywords)
    
    def evaluate_response(self, 
                         generated: str, 
                         reference: str, 
                         keywords: List[str] = None) -> Dict[str, Any]:
        """Evaluate a generated response against a reference answer."""
        if keywords is None:
            keywords = []
            
        # Calculate individual metrics
        similarity = self.calculate_text_similarity(generated, reference)
        rouge_scores = self.calculate_rouge_scores(generated, reference)
        keyword_score = self.calculate_keyword_score(generated, keywords)
        
        # Calculate weighted total score
        # Weights: 40% similarity, 30% ROUGE-L, 30% keyword score
        total_score = (
            0.4 * similarity +
            0.3 * rouge_scores['rouge-l'] +
            0.3 * keyword_score
        )
        
        return {
            'similarity_score': similarity,
            'rouge_scores': rouge_scores,
            'keyword_score': keyword_score,
            'total_score': total_score
        } 