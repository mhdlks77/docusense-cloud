import pdfplumber
import re

def extract_text_pdf(file_path: str) -> str:
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

    # clean weird PDF operators, non-text artifacts
    text = re.sub(r"/[A-Za-z0-9]+", "", text)  # remove PDF operators like /P1
    text = re.sub(r"\s+", " ", text)  # normalize whitespace

    return text.strip()
