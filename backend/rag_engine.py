from pypdf import PdfReader
import io
import math
import ollama

def get_embedding(text: str) -> list[float]:
    """Generates local vector embeddings using the all-minilm model."""
    response = ollama.embeddings(model="all-minilm", prompt=text)
    return response["embedding"]

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculates semantic similarity using raw mathematics (dot product over magnitudes)."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits a long document into smaller overlapping chunks to preserve context."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def process_document_and_get_context(file_bytes: bytes, query: str, k: int = 3) -> str:
    """The complete scratch-built RAG pipeline."""
    # 1. Extract Text
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    raw_text = "".join([page.extract_text() or "" for page in pdf_reader.pages])
    
    if not raw_text.strip():
        return "No readable text found in the document."

    # 2. Chunk Text
    chunks = chunk_text(raw_text)
    
    # 3. Create Embeddings (Your from-scratch Vector DB)
    print(f"\n[+] Building local vector database for {len(chunks)} chunks...")
    chunk_data = []
    for chunk in chunks:
        # Only embed meaningful chunks
        if len(chunk.strip()) > 50:
            chunk_data.append({
                "text": chunk,
                "embedding": get_embedding(chunk)
            })

    # 4. Embed the User Query
    search_query = query if query.strip() else "summarize the main concepts and definitions"
    print(f"[+] Searching for relevant context regarding: '{search_query}'")
    query_embedding = get_embedding(search_query)

    # 5. Calculate Similarities and Rank
    for item in chunk_data:
        item["score"] = cosine_similarity(query_embedding, item["embedding"])
    
    # Sort chunks by highest semantic similarity (closest to 1.0)
    chunk_data.sort(key=lambda x: x["score"], reverse=True)
    
    # 6. Return Top K Chunks
    top_chunks = [item["text"] for item in chunk_data[:k]]
    return "\n\n...\n\n".join(top_chunks)