"""
Data Ingestion Pipeline — Chunks, Embeds, and Upserts documents into Supabase.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure we can import from the backend directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google import genai
from supabase import create_client, Client
from data.legal_matters import LEGAL_MATTERS

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://stduhffsncmygemzdpcq.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def chunk_text(text: str) -> list[str]:
    """Paragraph layout chunker."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []
    return paragraphs

async def process_documents():
    print("\n[START] INITIALIZING DATA INGESTION PIPELINE")
    
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY environment variable not set.")
        return

    print("[NET] Connecting to Supabase PostgREST Client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("[NET] Initializing google-genai Client for text-embedding-004...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    total_chunks = 0
    
    for doc in LEGAL_MATTERS:
        doc_id = str(doc["id"])
        doc_title = doc["title"]
        
        # Build text body to embed
        text = f"{doc_title}\n\n{doc['query']}"
        chunks = chunk_text(text)
        
        for idx, chunk_text_content in enumerate(chunks):
            print(f"[PROCESS] Computing 768-dim vector for Chunk {idx} of Document '{doc_title}'...")
            
            loop = asyncio.get_running_loop()
            try:
                # 1) Use modern unified google-genai SDK for the active 768-dim embedding model
                from google.genai import types
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.embed_content(
                        model='gemini-embedding-2',
                        contents=chunk_text_content,
                        config=types.EmbedContentConfig(output_dimensionality=768)
                    )
                )
                
                # 2) Isolate the exact 768-dimensional float list
                generated_768_vector = response.embeddings[0].values
                
                chunk_metadata = {
                    "practice": doc.get("practice"),
                    "court": doc.get("court")
                }
                
                # 3) Execute a clean direct insert query using standard postgrest bindings
                supabase.table("document_chunks").insert({
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "chunk_index": idx,
                    "content": chunk_text_content,
                    "metadata": chunk_metadata,
                    "embedding": generated_768_vector
                }).execute()
                
                print(f"[SUCCESS] Committed Chunk {idx} of '{doc_title}' to Supabase successfully.")
                total_chunks += 1
            except Exception as e:
                print(f"[FAIL] Failed to process Chunk {idx} of '{doc_title}': {str(e)}")

    print(f"\n[DONE] Successfully committed {total_chunks} total chunks to Supabase document_chunks layer.\n")

if __name__ == "__main__":
    asyncio.run(process_documents())
