from openai import OpenAI
from app.config.settings import OPENAI_API_KEY, EMBEDDING_MODEL
import tiktoken

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------------------
# TOKENIZER
# ----------------------------------------
def tokenize(text, model="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model)
    return enc.encode(text)

def chunk_text(text: str, max_tokens=1000):
    """
    Chunk text for embeddings by token count.
    """
    tokens = tokenize(text)
    chunks = []

    # Walk in windows of max_tokens
    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(chunk)

    return chunks


def tokens_to_text(token_list, model="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model)
    return enc.decode(token_list)


# ----------------------------------------
# EMBEDDING SINGLE CHUNK
# ----------------------------------------
def embed_chunk(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


# ----------------------------------------
# FULL DOCUMENT EMBEDDING PIPELINE
# ----------------------------------------
def generate_embeddings_for_document(text: str) -> dict:
    """
    Returns:
    - full_doc_embedding (optional, truncated)
    - chunk_embeddings (list of embeddings)
    """

    # ---- 1. Chunk text into <= 1000 token blocks ----
    token_chunks = chunk_text(text, max_tokens=1000)

    chunk_embeddings = []
    for chunk_tokens in token_chunks:
        chunk_text_str = tokens_to_text(chunk_tokens)
        embedding = embed_chunk(chunk_text_str)

        chunk_embeddings.append({
            "text": chunk_text_str[:500],  # small preview
            "embedding": embedding
        })

    # ---- 2. Full doc embedding (truncate to 6000 tokens) ----
    # OPTIONAL but useful
    truncated_tokens = tokenize(text)[:6000]
    full_doc_text = tokens_to_text(truncated_tokens)
    full_doc_embedding = embed_chunk(full_doc_text)

    return {
        "full_document_embedding": full_doc_embedding,
        "chunks": chunk_embeddings
    }
