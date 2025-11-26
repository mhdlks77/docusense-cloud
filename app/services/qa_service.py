from app.services.semantic_search import search_document
from app.config.settings import OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def answer_question_about_document(query: str, filename: str, top_k: int = 5):
    
    """"
    I added this feature because when relying only on vector search, the user
    only gets the top-k results based on similarity, but that may not be very helpful for
    the user to get a satisfying answer based on his query in semantic search (/search-document endpoint)
    """
    
    # Retrieving relevant chunks
    retrieved_chunks = search_document(query, filename, top_k)
    
    context = "\n\n---\n\n".join([c["text"] for c in retrieved_chunks])
    
    # Ask GPT to answer based on the context only
    prompt = f"""
You are a document analysis assistant. 
Use ONLY the following document excerpts to answer the question.

Document excerpts:
{context}

Question: {query}

Rules:
- Base your answer ONLY on the provided text.
- If the answer is not present, say: "The document does not contain enough information."
- Be concise but informative.
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",   # fast + cheap, upgradeable to gpt-4.1
        messages=[
            {"role": "system", "content": "You analyze documents and answer questions accurately."},
            {"role": "user", "content": prompt}
        ]
    )

    final_answer = response.choices[0].message.content

    return {
        "answer": final_answer,
        "chunks_used": retrieved_chunks
    }
    