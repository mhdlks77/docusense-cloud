import json
import os
from app.services.embedding_services import embed_chunk
from app.services.vector_utils import cosine_similarity

# Function that searches only one document at a time
def search_document(query: str, filename: str, top_k: int = 3):
    
    #Search inside a single doc
    embeddings_file = os.path.join("processed", filename.replace(".pdf", "_embeddings.json"))

    if not os.path.exists(embeddings_file):
        raise FileNotFoundError("Embeddings not found for this document. Process it first.")
    
    # Load document embeddings
    with open(embeddings_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data["chunks"]

    # Embed the query
    query_embedding = embed_chunk(query)

    # Compute similarity with each chunk
    scored_chunks = []
    for c in chunks:
        score = cosine_similarity(query_embedding, c["embedding"])
        scored_chunks.append({
            "text": c["text"],
            "score": float(score)
        })
    
    #Sort top-k resilts
    top_results = sorted(scored_chunks, key=lambda x: x["score"], reverse=True)[:top_k]

    return top_results

#Function that searches in all documents instead of only 1
def search_all_documents(query: str, top_k: int = 5):
    """
    Global semantic search across ALL documents with embeddings.
    Looks through all *_embeddings.json files in 'processed/'.
    """
    processed_dir = "processed"
    if not os.path.exists(processed_dir):
        raise FileNotFoundError("No processed directory found. Upload and process some PDFs first.")

    # Embed query once
    query_embedding = embed_chunk(query)

    global_results = []

    # Loop through all embeddings files
    for filename in os.listdir(processed_dir):
        if not filename.endswith("_embeddings.json"):
            continue

        embeddings_path = os.path.join(processed_dir, filename)

        with open(embeddings_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = data.get("chunks", [])
        # Derive original PDF name
        original_pdf = filename.replace("_embeddings.json", ".pdf")

        for c in chunks:
            score = cosine_similarity(query_embedding, c["embedding"])
            global_results.append({
                "filename": original_pdf,
                "text": c["text"],
                "score": float(score)
            })

    if not global_results:
        raise FileNotFoundError("No embeddings found for any document. Make sure PDFs were processed successfully.")

    # Sort globally and take top_k
    top_results = sorted(global_results, key=lambda x: x["score"], reverse=True)[:top_k]
    return top_results