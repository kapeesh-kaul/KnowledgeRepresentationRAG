# Knowledge Representation RAG

A sophisticated Retrieval-Augmented Generation (RAG) system that implements two different approaches for knowledge representation and querying:
1. Graph-based approach using Neo4j
2. Text corpus-based approach using vector embeddings

## Features

### Graph-Based System
- Build knowledge graphs from Wikipedia articles
- Natural language querying with Cypher query generation
- Automatic relationship extraction and structuring
- Comprehensive graph database management

### Corpus-Based System
- Build and manage text corpora from Wikipedia
- Configurable text chunking and processing
- Semantic search capabilities
- LLM-powered response generation

### Evaluation Framework
- Comprehensive metrics for response quality
- Similarity scoring
- ROUGE-L evaluation
- Keyword-based assessment
- Detailed evaluation reports

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   conda env create -f requirements.yaml
   conda activate kg-rag
   ```
3. Set up environment variables in `.env` file
4. Configure Neo4j database connection

## Usage

### Graph Operations
```bash
# Build a knowledge graph
python main.py build_graph --search_term "Artificial Intelligence"

# Query the graph
python main.py query_graph --user_prompt "What are the main applications of AI?"

# Clear the graph database
python main.py clear_graph
```

### Corpus Operations
```bash
# Build a corpus
python main.py build_corpus --search_term "Machine Learning" --max_depth 2 --max_pages 10

# Search the corpus
python main.py query_corpus --query "What is deep learning?" --top_k 5

# Clear the corpus
python main.py clear_corpus
```

### Evaluation
```bash
# Evaluate graph-based responses
python main.py evaluate_graph --test_file test_cases.json --output_file evaluation_results.json

# Evaluate corpus-based responses
python main.py evaluate_corpus --test_file test_cases.json --output_file evaluation_results.json
```

## Configuration

The system uses several configuration files:
- `.env`: Environment variables
- `.secrets`: Sensitive credentials
- `core/settings.py`: System settings

## Project Structure

```
.
├── core/                 # Core system components
├── services/            # Service implementations
│   ├── evaluation/      # Evaluation framework
│   ├── llm_interface/   # LLM interaction
│   ├── neo4j/          # Graph database operations
│   ├── retrieval/      # Search functionality
│   └── utils/          # Utility functions
├── .data/              # Data storage
├── main.py             # Main CLI interface
└── test_cases.json     # Evaluation test cases
```