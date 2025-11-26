from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from app.models.document_metadata import DocumentMetadata
from app.storage.metadata_store import load_metadata, save_metadata
from app.file_handlers.pdf_handler import extract_text_pdf
from app.services.summarizer import summarize_text
from app.services.embedding_services import generate_embeddings_for_document
from app.services.semantic_search import search_document, search_all_documents
from app.services.qa_service import answer_question_about_document
from app.services.global_qa_service import answer_question_global
from app.storage.s3_storage import upload_file, upload_text_content

import json


app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "Docusense backend running"}

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF files are allowed"}

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save PDF
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Upload to S3
    s3_pdf_key = f"uploads/{file.filename}"
    s3_pdf_url = upload_file(file_path, s3_pdf_key, content_type="application/pdf")

    # Extract text
    extracted_text = extract_text_pdf(file_path)
    
    # Upload extracted test to S3
    s3_text_key = f"processed/text/{file.filename.replace('.pdf', '.txt')}"
    s3_text_url = upload_text_content(extracted_text, s3_text_key)

    # # Save text file
    # processed_path = os.path.join("processed", file.filename.replace(".pdf", ".txt"))
    # os.makedirs("processed", exist_ok=True)

    # with open(processed_path, "w", encoding="utf-8") as out:
    #     out.write(extracted_text)
        
    # -------SUMMARIZING TEXT---------
    summary = summarize_text(extracted_text)
    
    # Upload summary to s3
    s3_summary_key = f"processed/summaries/{file.filename.replace('.pdf', '_summary.txt')}"
    s3_summary_url = upload_text_content(summary, s3_summary_key)
    
    # # Save summary file
    # summary_path = os.path.join("processed", file.filename.replace(".pdf", "_summary.text"))
    # with open(summary_path, "w", encoding="utf-8") as s:
    #     s.write(summary)
        
    #--------Generating Embeddings---------
    embeddings = generate_embeddings_for_document(extracted_text)
    embeddings_json = json.dumps(embeddings)
    
    s3_emb_key = f"processed/embeddings/{file.filename.replace('.pdf', '_embeddings.json')}"
    s3_embeddings_url = upload_text_content(embeddings_json, s3_emb_key)
    
    # # Saving embeddings JSON files
    # embedding_path = os.path.join("processed", file.filename.replace(".pdf", "_embeddings.json"))
    # with open(embedding_path, "w", encoding="utf-8") as f:
    #     json.dump(embeddings, f)
    
    #Cleanup
    os.remove(file_path)

    # Build metadata object
    metadata = DocumentMetadata(
        filename=file.filename,
        file_size=len(extracted_text),
        uploaded_at=datetime.now(),
        processed_text_path=s3_text_url,
        extracted_text_length=len(extracted_text),
        summary=summary,
        embedding_path=s3_embeddings_url
    )

    # Save metadata to JSON
    existing = load_metadata()
    existing.append(metadata.model_dump(mode="json"))
    save_metadata(existing)

    return {
        "filename": file.filename,
        "pdf_url": s3_pdf_url,
        "text_url": s3_text_url,
        "summary_url": s3_summary_url,
        "embeddings_url": s3_embeddings_url,
        "status": "uploaded_all_to_s3"
    }

# NOT NEEDED ANYMORE, IMPLEMENTED INTERNALLY IN /ASK-DOCUMENT
# #returns top-k most similar chunks based on embedding vectors
# @app.post("/search-document")
# async def search_in_document(query: str, filename: str, top_k: int = 3):
#     try:
#         results = search_document(query, filename, top_k)
#         return {
#             "filename": filename,
#             "query": query,
#             "results": results
#         }
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Document not found or embeddings missing")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# Search all documents
# NOT NEEDED FOR NOW, AS IT IS NOW INTERNAL IN ASK_ALL_DOCUMENTS ENDPOINT
# @app.post("/search-all/")
# async def search_all(query: str, top_k: int = 5):
#     try:
#         results = search_all_documents(query, top_k)   
#         return{
#             "query": query,
#             "top_k": top_k,
#             "results": results 
#         }
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    

# GPT gives a more user-friendly and useful answer based on only one document
@app.post("/ask-document/")
async def ask_document(query: str, filename: str, top_k: int = 5):
    try:
        result = answer_question_about_document(query, filename, top_k)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document or embeddings not found. Upload it first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GPT will answer based on all documents not only one
@app.post("/ask-all-documents/")
async def ask_all_documents(query: str, top_k: int = 5):
    try:
        result = answer_question_global(query, top_k)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No documents with embeddings found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))