from typing import List, Dict, Optional, Set
import logging
from dataclasses import dataclass
from pathlib import Path
import json
import time
import numpy as np
import hnswlib
from sklearn.feature_extraction.text import TfidfVectorizer
from services.wikimedia.scraper import WikipediaScraper
from core.settings import settings
from ollama import embed

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    chunk_id: str
    source: str
    start_index: int
    end_index: int
    metadata: Dict[str, any] = None
    embedding: Optional[np.ndarray] = None

    def __str__(self):
        return f"Chunk(content={self.content}, source={self.source}, metadata={self.metadata})"

class CorpusBuilder:
    """
    A class to build and manage a scalable text corpus with content chunks.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        storage_path: Optional[str] = None,
        max_depth: int = 2,
        max_pages: int = 10,
        delay: float = 1.0,
        model: str = None
    ):
        """
        Initialize the corpus builder with chunking parameters.
        
        Args:
            chunk_size (int): Maximum number of characters per chunk
            chunk_overlap (int): Number of characters to overlap between chunks
            storage_path (str): Path to store the corpus data
            max_depth (int): Maximum depth to follow links
            max_pages (int): Maximum number of pages to process
            delay (float): Delay between requests in seconds
            model (str): LLM model to use for embeddings
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.storage_path = Path(storage_path) if storage_path else Path(settings.CORPUS_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.chunks: Dict[str, TextChunk] = {}
        self.scraper = WikipediaScraper()
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.visited_pages: Set[str] = set()
        self.model = model or settings.LLM_MODEL
        self.embedding_index = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text using Ollama."""
        logger.info(f"Getting embedding for text: {text[:min(10, len(text))]} ...")
        response = embed(model=self.model, input=[text])
        return np.array(response.embeddings[0])
        
    def _build_indexes(self) -> None:
        """Build HNSW and TF-IDF indexes for the corpus."""
        if not self.chunks:
            return
            
        # Get all chunk contents and embeddings
        chunk_contents = [chunk.content for chunk in self.chunks.values()]
        embeddings = []
        
        logger.info("Generating embeddings for chunks...")
        for chunk in self.chunks.values():
            if chunk.embedding is None:
                chunk.embedding = self._get_embedding(chunk.content)
            embeddings.append(chunk.embedding)
            
        embeddings = np.array(embeddings)
        
        # Build HNSW index
        logger.info("Building HNSW index...")
        dim = embeddings.shape[1]
        self.embedding_index = hnswlib.Index(space='cosine', dim=dim)
        self.embedding_index.init_index(max_elements=len(embeddings), ef_construction=100, M=16)
        self.embedding_index.add_items(embeddings)
        self.embedding_index.set_ef(50)
        
        # Build TF-IDF index
        logger.info("Building TF-IDF index...")
        self.tfidf_vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(chunk_contents)
        
    def hybrid_search(self, query: str, top_k: int = 5) -> List[TextChunk]:
        """
        Perform hybrid search using both embeddings and TF-IDF.
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            List[TextChunk]: Most relevant chunks
        """
        if not self.embedding_index or not self.tfidf_vectorizer:
            self._build_indexes()
            
        # Get query embedding
        query_embedding = self._get_embedding(query).reshape(1, -1)
        
        # Get embedding-based results
        k = min(top_k * 2, len(self.chunks))
        chunk_ids, _ = self.embedding_index.knn_query(query_embedding, k=k)
        
        # Get TF-IDF scores
        tfidf_query = self.tfidf_vectorizer.transform([query])
        tfidf_scores = (self.tfidf_matrix @ tfidf_query.T).toarray().flatten()
        
        # Combine and rank results
        chunk_list = list(self.chunks.values())
        candidates = [(chunk_list[i], tfidf_scores[i]) for i in chunk_ids[0]]
        ranked = sorted(candidates, key=lambda x: -x[1])[:top_k]
        
        return [chunk for chunk, _ in ranked]
        
    def build_corpus(self, search_term: str) -> None:
        """
        Build a corpus starting from a search term by following links.
        
        Args:
            search_term (str): The term to search for
        """
        if not search_term:
            raise ValueError("Search term cannot be empty")
            
        self.visited_pages.clear()
        self._process_page(search_term, depth=0)
        self._build_indexes()  # Build indexes after corpus is built
        
    def _process_page(self, title: str, depth: int) -> None:
        """
        Process a single page and its links recursively.
        
        Args:
            title (str): Page title to process
            depth (int): Current recursion depth
        """
        if depth > self.max_depth or len(self.visited_pages) >= self.max_pages:
            return
            
        if title in self.visited_pages:
            return
            
        self.visited_pages.add(title)
        logger.info(f"Processing page: {title} (depth: {depth})")
        
        try:
            # Fetch and process the page
            page = self.scraper.fetch_page(title)
            
            # Extract and add content chunks
            logger.info(f"Extracting content chunks from page: {title}")
            chunks = self.scraper.extract_content_chunks(page)
            for chunk in chunks:
                logger.info(f"Adding content chunk to corpus: {chunk['content'][:min(10, len(chunk['content']))]} ...")
                self.add_text(
                    text=chunk['content'],
                    source=page.url,
                    metadata={
                        'title': page.title,
                        'depth': depth,
                        'url': page.url,
                        'section': chunk['section'],
                        'chunk_type': chunk['type']
                    }
                )
            
            # Process "See also" links
            logger.info(f"Extracting see also links from page: {title}")
            see_also_links = self.scraper.extract_see_also(page)
            for link in see_also_links:
                if len(self.visited_pages) >= self.max_pages:
                    break
                    
                time.sleep(self.delay)  # Respect rate limiting
                self._process_page(link, depth + 1)
                
            # Process regular links
            linked_pages = self.scraper.extract_linked_pages(page)
            for link in linked_pages[:5]:  # Limit to first 5 links to avoid too many pages
                if len(self.visited_pages) >= self.max_pages:
                    break
                    
                time.sleep(self.delay)
                self._process_page(link, depth + 1)
                
        except Exception as e:
            logger.error(f"Error processing page {title}: {e}")
            return
            
    def add_text(self, text: str, source: str, metadata: Optional[Dict[str, any]] = None) -> List[TextChunk]:
        """
        Add text to the corpus, splitting it into chunks.
        
        Args:
            text (str): The text to add
            source (str): Source identifier for the text
            metadata (Dict): Optional metadata to associate with the chunks
            
        Returns:
            List[TextChunk]: List of created chunks
        """
        chunks = []
        start_idx = 0
        
        while start_idx < len(text):
            # Calculate the end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(text))
            
            # Adjust end_idx to end at a sentence boundary if possible
            if end_idx < len(text):
                sentence_end = text.rfind('.', start_idx, end_idx)
                if sentence_end > start_idx + self.chunk_size // 2:
                    end_idx = sentence_end + 1
            
            chunk_content = text[start_idx:end_idx].strip()
            chunk_id = f"{source}_{start_idx}_{end_idx}"
            
            chunk = TextChunk(
                content=chunk_content,
                chunk_id=chunk_id,
                source=source,
                start_index=start_idx,
                end_index=end_idx,
                metadata=metadata
            )
            
            chunks.append(chunk)
            self.chunks[chunk_id] = chunk
            
            # Move start_idx forward, ensuring we don't get stuck
            next_start = end_idx - self.chunk_overlap
            if next_start <= start_idx:  # Prevent infinite loop
                next_start = end_idx
            start_idx = next_start
            
        return chunks
    
    def save_corpus(self) -> None:
        """Save the current corpus to disk."""
        corpus_data = {
            chunk_id: {
                'content': chunk.content,
                'source': chunk.source,
                'start_index': chunk.start_index,
                'end_index': chunk.end_index,
                'metadata': chunk.metadata,
                'embedding': chunk.embedding.tolist() if chunk.embedding is not None else None
            }
            for chunk_id, chunk in self.chunks.items()
        }
        
        with open(self.storage_path / 'corpus.json', 'w', encoding='utf-8') as f:
            json.dump(corpus_data, f, ensure_ascii=False, indent=2)
            
    def load_corpus(self) -> None:
        """Load the corpus from disk."""
        corpus_file = self.storage_path / 'corpus.json'
        if not corpus_file.exists():
            return
            
        with open(corpus_file, 'r', encoding='utf-8') as f:
            corpus_data = json.load(f)
            
        self.chunks = {
            chunk_id: TextChunk(
                content=data['content'],
                chunk_id=chunk_id,
                source=data['source'],
                start_index=data['start_index'],
                end_index=data['end_index'],
                metadata=data['metadata'],
                embedding=np.array(data['embedding']) if data['embedding'] is not None else None
            )
            for chunk_id, data in corpus_data.items()
        }
        
        # Rebuild indexes after loading
        self._build_indexes()
        
    def get_chunks_by_source(self, source: str) -> List[TextChunk]:
        """
        Get all chunks from a specific source.
        
        Args:
            source (str): Source identifier
            
        Returns:
            List[TextChunk]: Chunks from the specified source
        """
        return [chunk for chunk in self.chunks.values() if chunk.source == source]
        
    def clear_corpus(self) -> None:
        """Clear all chunks from the corpus."""
        self.chunks.clear()
        self.embedding_index = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None 