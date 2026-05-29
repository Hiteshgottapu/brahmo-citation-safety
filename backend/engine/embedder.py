"""
Embedder — Google genai text-embedding-004 wrapper.

Uses the unified google.genai SDK (genai.Client pattern).
Model: text-embedding-004 → 768-dimensional embeddings.

Two critical fixes applied:
  1. genai.Client.models.embed_content() is synchronous — wrapped in
     asyncio.get_running_loop().run_in_executor() to avoid blocking
     the asyncio event loop.
  2. embed_batch uses asyncio.gather for parallel chunk embedding with
     individual exception handling (no single-failure cascade).

Falls back to zero-vector matrices when GEMINI_API_KEY is unset.
"""

from __future__ import annotations

import asyncio
from typing import List

from google import genai

from config import GEMINI_API_KEY


# ---------------------------------------------------------------------------
# Embedding dimensions for text-embedding-004
# ---------------------------------------------------------------------------
EMBEDDING_DIMENSIONS = 768


class Embedder:
    """Async-safe wrapper around Google's synchronous genai embed_content."""

    def __init__(self) -> None:
        self.model_name: str = "gemini-embedding-2"
        self.dimensions: int = EMBEDDING_DIMENSIONS

        if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key":
            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self.active: bool = True
        else:
            self._client = None
            self.active = False
            print(
                "WARNING: Gemini API Key missing for Embedder. "
                "Reverting to zero-vector fallback matrices."
            )

    # ------------------------------------------------------------------
    # Internal: synchronous genai.Client embed call (run in executor)
    # ------------------------------------------------------------------

    def _embed_sync(self, text: str) -> List[float]:
        """Blocking genai.Client.models.embed_content() call.

        Must be dispatched via run_in_executor() to avoid blocking
        the asyncio event loop.
        """
        from google.genai import types
        result = self._client.models.embed_content(  # type: ignore[union-attr]
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
        )
        return list(result.embeddings[0].values)

    # ------------------------------------------------------------------
    # Query embedding
    # ------------------------------------------------------------------

    async def embed_query(self, text: str) -> List[float]:
        """Generate a 768-dim embedding for retrieval queries.

        Wraps the synchronous genai.Client call inside
        asyncio.get_running_loop().run_in_executor() for non-blocking
        execution on the default thread pool.
        """
        if not self.active:
            return [0.0] * self.dimensions

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._embed_sync, text)
        except Exception as e:
            print(f"Embedding query fallback triggered: {e}")
            return [0.0] * self.dimensions

    # ------------------------------------------------------------------
    # Document chunk embedding
    # ------------------------------------------------------------------

    async def embed_document_chunk(self, text: str) -> List[float]:
        """Generate a 768-dim embedding for document storage.

        Wraps the synchronous genai.Client call inside
        asyncio.get_running_loop().run_in_executor() for non-blocking
        execution on the default thread pool.
        """
        if not self.active:
            return [0.0] * self.dimensions

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._embed_sync, text)
        except Exception as e:
            print(f"Embedding document chunk fallback triggered: {e}")
            return [0.0] * self.dimensions

    # ------------------------------------------------------------------
    # Batch embedding — parallel with asyncio.gather
    # ------------------------------------------------------------------

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple chunks concurrently via asyncio.gather.

        Each chunk is embedded individually to avoid payload-size limits
        and network timeout ceilings on large batches.  Failures are
        isolated per-chunk (zero-vector fallback) — a single bad chunk
        does not cascade to the rest.
        """
        if not self.active:
            return [[0.0] * self.dimensions for _ in texts]

        tasks = [self.embed_document_chunk(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sanitized: List[List[float]] = []
        for res in results:
            if isinstance(res, Exception):
                print(f"Batch embedding exception (isolated): {res}")
                sanitized.append([0.0] * self.dimensions)
            else:
                sanitized.append(res)

        return sanitized


# Module-level singleton
embedder = Embedder()
