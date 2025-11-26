from app.services.semantic_search import search_all_documents
from app.config.settings import OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

# This is a global
def answer_question_global(query: str, top_k: int = 5):
    """
    Global RAQA:
    1. Retrieve top-k chunks across ALL documents.
    2. Send them to GPT to synthesize an answer.
    """
    # Retrieve chunks globally
    retrieved = search_all_documents(query, top_k)

    # Build context string (all document excerpts)
    context_blocks = []
    for r in retrieved:
        context_blocks.append(
            f"Document: {r['filename']}\nExcerpt:\n{r['text']}\n"
        )
    context = "\n\n---\n\n".join(context_blocks)

    # Prompt the LLM with instructions
    prompt = f"""
You are a document analysis assistant. 
Use ONLY the provided text excerpts from multiple documents to answer the question.

Excerpts:
{context}

Question: {query}

Rules:
- Cite which document(s) the answer came from.
- Only use information present in the excerpts.
- If the answer cannot be determined from these excerpts, say:
"The available documents do not contain enough information to answer this question."
"""

    # Run GPT
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You answer questions based on provided document excerpts only."},
            {"role": "user", "content": prompt}
        ]
    )

    final_answer = response.choices[0].message.content

    return {
        "answer": final_answer,
        "chunks_used": retrieved
    }
