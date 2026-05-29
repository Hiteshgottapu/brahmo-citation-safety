"""
RAG Retriever — semantic search against pgvector + context assembly.

Two critical fixes from code review:
  1. pgvector serialization: Python list[float] is explicitly cast to the
     string format "[0.123,0.456,...]" before passing to the RPC, avoiding
     the 42883 / string-serialization crash.
  2. Retrieved context chunks are pre-normalized through the Section
     Normalizer to block old statutory injections (IPC→BNS) from leaking
     into the LLM prompt.
"""

from __future__ import annotations

import time
from typing import Any

from database import get_supabase
from engine.embedder import embedder
from engine.section_normalizer import SectionNormalizer
from models import DocumentChunk, RAGContext


class RAGRetriever:
    """Retrieves relevant knowledge-base chunks and assembles the RAG prompt."""

    _SYSTEM_PROMPT = (
        "You are an elite expert Indian legal research assistant. "
        "Analyze the following request and return a comprehensive legal "
        "memo referencing specific cases using standardized Indian legal "
        "citation formats (SCC, AIR, SCC OnLine, Cri LJ, SCR, MANU). "
        "Include specific case citations with proper formatting."
    )

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> RAGContext:
        """Embed the query, run cosine similarity search, return ranked chunks."""
        start_time = time.time()

        # 1. Generate 768-dim query embedding
        query_vector = await embedder.embed_query(query)

        # 2. FIX: Explicitly serialize float list to pgvector-safe string
        #    to avoid 42883 / serialization crash on the Supabase RPC wire
        vector_string = f"[{','.join(map(str, query_vector))}]"

        chunks: list[DocumentChunk] = []

        try:
            supabase = await get_supabase()
            
            if not embedder.active:
                # Fallback demonstration mode when GEMINI_API_KEY is missing
                response = await (
                    supabase.table("document_chunks")
                    .select("*")
                    .limit(top_k)
                    .execute()
                )
                records = response.data or []
                # Assign mock similarities for demonstration
                for idx, r in enumerate(records):
                    r["similarity"] = 0.85 - (idx * 0.05)
            else:
                response = await (
                    supabase.rpc(
                        "match_chunks",
                        {
                            "query_embedding": vector_string,
                            "match_threshold": 0.4,
                            "match_count": top_k,
                        },
                    ).execute()
                )
                records = response.data or []

            for r in records:
                chunks.append(
                    DocumentChunk(
                        id=r["id"],
                        doc_id=r["doc_id"],
                        doc_title=r["doc_title"],
                        chunk_index=r["chunk_index"],
                        content=r["content"],
                        metadata=r.get("metadata") or {},
                        similarity=round(r.get("similarity", 0.0), 4),
                    )
                )
        except Exception as e:
            print(f"RAG retrieval failed (degraded mode): {e}")

        duration_ms = round((time.time() - start_time) * 1000, 2)

        return RAGContext(
            chunks=chunks,
            total_chunks_searched=len(chunks),
            retrieval_time_ms=duration_ms,
        )

    # ------------------------------------------------------------------
    # Prompt assembly
    # ------------------------------------------------------------------

    async def assemble_prompt(
        self,
        query: str,
        context: RAGContext,
    ) -> str:
        """Build the RAG-augmented LLM prompt.

        The retrieved context chunks are pre-normalized through the
        Section Normalizer to prevent old IPC/CrPC/IEA references from
        leaking into the LLM prompt as-is.
        """
        if not context.chunks:
            # No RAG context available — fall back to vanilla prompt
            return (
                f"{self._SYSTEM_PROMPT}\n\n"
                f"USER QUERY REQUEST:\n{query}"
            )

        # Build raw context from retrieved chunks
        raw_context_parts: list[str] = []
        for c in context.chunks:
            source_line = f"Source: {c.doc_title} (relevance: {c.similarity:.0%})"
            raw_context_parts.append(f"{source_line}\n{c.content}")

        raw_context_text = "\n\n---\n\n".join(raw_context_parts)

        # FIX: Pre-normalize the retrieved context to block old statutory
        # section references from being injected into the LLM prompt.
        normalizer = SectionNormalizer()
        norm_result = await normalizer.normalize_text(raw_context_text)
        clean_context = norm_result.normalized_text

        augmented_prompt = (
            f"{self._SYSTEM_PROMPT}\n\n"
            f"CRITICAL DISCOVERY CONTEXT PRECEDENTS:\n"
            f"{clean_context}\n\n"
            f"USER QUERY REQUEST:\n{query}\n\n"
            f"INSTRUCTIONS: Use the above context precedents as your primary "
            f"source of case citations. You may supplement with additional "
            f"well-known cases, but prioritise the provided precedents. "
            f"Use standard Indian citation formats."
        )

        return augmented_prompt
