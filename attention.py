from ollama import embed
import hnswlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from core.settings import settings

# -------------------------------
# 1. Chunking the Corpus
# -------------------------------
def chunk_text_corpus(text):
    return [i.strip() for i in text.split(sep='\n') if i.strip() != '']

# -------------------------------
# 2. Get Embeddings via Ollama (updated)
# -------------------------------
def get_ollama_embedding(text, model=None):
    model = model or settings.LLM_MODEL
    response = embed(model=model, input=[text])
    return np.array(response.embeddings[0])

def get_embeddings_for_chunks(chunks, model=None):
    model = model or settings.LLM_MODEL
    response = embed(model=model, input=chunks)
    return np.array(response['embeddings'])

# -------------------------------
# 3. Build HNSW Vector Index
# -------------------------------
def build_hnsw_index(embeddings):
    dim = embeddings.shape[1]
    index = hnswlib.Index(space='cosine', dim=dim)
    index.init_index(max_elements=len(embeddings), ef_construction=100, M=16)
    index.add_items(embeddings)
    index.set_ef(50)
    return index

# -------------------------------
# 4. TF-IDF Index
# -------------------------------
def build_tfidf_index(chunks):
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(chunks)
    return vectorizer, matrix

# -------------------------------
# 5. Hybrid Query with Ollama
# -------------------------------
def hybrid_query(query, model, chunks, embedding_index, tfidf_vectorizer, tfidf_matrix, top_k=5):
    query_embedding = get_ollama_embedding(query, model=model).reshape(1, -1)
    k = min(top_k * 2, len(chunks))  # prevent hnswlib crash
    ids, _ = embedding_index.knn_query(query_embedding, k=k)

    tfidf_query = tfidf_vectorizer.transform([query])
    tfidf_scores = (tfidf_matrix @ tfidf_query.T).toarray().flatten()

    candidates = [(chunks[i], tfidf_scores[i]) for i in ids[0]]
    ranked = sorted(candidates, key=lambda x: -x[1])[:top_k]
    return [text for text, _ in ranked]


# -------------------------------
# 6. Main Demo
# -------------------------------
def main():
    corpus = """
    Solar energy can be stored using lithium-ion batteries. Wind energy complements solar in hybrid grids. 
    Energy storage is vital for consistent power delivery, especially during peak hours or low production periods.
    Geothermal and hydro power are stable renewable sources.
    """

    print("🔧 Chunking corpus...")
    chunks = chunk_text_corpus(corpus)
    print(chunks)

    print("📥 Getting embeddings via Ollama...")
    embeddings = get_embeddings_for_chunks(chunks)

    print("📚 Building indexes...")
    embedding_index = build_hnsw_index(embeddings)
    tfidf_vectorizer, tfidf_matrix = build_tfidf_index(chunks)

    query = "hydro power"
    print(f"🔎 Query: {query}")
    results = hybrid_query(query, model=settings.LLM_MODEL, chunks=chunks, embedding_index=embedding_index,
                           tfidf_vectorizer=tfidf_vectorizer, tfidf_matrix=tfidf_matrix)

    print("\n📄 Top Relevant Chunks:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r}\n")

if __name__ == "__main__":
    main()
