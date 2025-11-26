from app.config.settings import OPENAI_API_KEY
from openai import OpenAI

def summarize_text(text: str) -> str:
    """
    Summarize using OpenAI (GPT-4.1).
    """
    if not OPENAI_API_KEY:
        return "No OpenAI API key provided."

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Summarize the following document as clearly and concisely as possible."},
            {"role": "user", "content": text[:15000]}  # send safe amount
        ]
    )

    return response.choices[0].message.content
