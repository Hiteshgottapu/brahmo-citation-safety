"""
Document Chunker — structure-aware legal text splitter.

Splits legal documents by paragraph boundaries while respecting
section headers.  Produces chunks of ~400 tokens with ~80 token
overlap so no information is lost at clause boundaries.
"""

from __future__ import annotations

import re
from typing import List


class DocumentChunker:
    """Splits legal text into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 400,
        overlap: int = 80,
    ) -> None:
        self.chunk_size = chunk_size   # target tokens per chunk
        self.overlap = overlap         # overlap tokens between consecutive chunks

        # Regex for section headers in legal documents
        self._header_re = re.compile(
            r"^(?:"
            r"#{1,4}\s+.+"                         # Markdown headers
            r"|Section\s+\d+[A-Za-z]*.*"            # "Section 420 …"
            r"|\d+\.\s+[A-Z].*"                     # "1. Introduction"
            r"|[IVXLC]+\.\s+.*"                     # "IV. Analysis"
            r"|CHAPTER\s+[IVXLC\d]+.*"              # "CHAPTER IV …"
            r"|PART\s+[IVXLC\d]+.*"                 # "PART II …"
            r")$",
            re.MULTILINE,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        doc_id: str = "",
        doc_title: str = "",
    ) -> List[dict]:
        """Split *text* into chunks.

        Returns a list of dicts, each with:
            content      — chunk text
            chunk_index  — zero-based position
            metadata     — { section_title, doc_id, doc_title }
        """
        if not text.strip():
            return []

        paragraphs = self._split_paragraphs(text)
        raw_chunks = self._merge_paragraphs(paragraphs)

        results: List[dict] = []
        for idx, chunk in enumerate(raw_chunks):
            section_title = self._detect_section_title(chunk)
            results.append(
                {
                    "content": chunk.strip(),
                    "chunk_index": idx,
                    "metadata": {
                        "section_title": section_title,
                        "doc_id": doc_id,
                        "doc_title": doc_title,
                    },
                }
            )

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split on double newlines, keeping non-empty paragraphs."""
        raw = re.split(r"\n{2,}", text)
        return [p.strip() for p in raw if p.strip()]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token count — 1 token ≈ 4 characters for English/legal text."""
        return max(1, len(text) // 4)

    def _merge_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Merge consecutive paragraphs into chunks of ~chunk_size tokens
        with ~overlap token carry-over between consecutive chunks."""
        if not paragraphs:
            return []

        chunks: List[str] = []
        current_parts: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)

            # If a single paragraph exceeds chunk_size, split it by sentences
            if para_tokens > self.chunk_size:
                # Flush current buffer first
                if current_parts:
                    chunks.append("\n\n".join(current_parts))
                    current_parts = []
                    current_tokens = 0

                # Split the oversized paragraph into sentence-level sub-chunks
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sub_parts: List[str] = []
                sub_tokens = 0
                for sentence in sentences:
                    s_tokens = self._estimate_tokens(sentence)
                    if sub_tokens + s_tokens > self.chunk_size and sub_parts:
                        chunks.append(" ".join(sub_parts))
                        # Overlap: keep the last portion
                        overlap_text = " ".join(sub_parts[-2:]) if len(sub_parts) >= 2 else sub_parts[-1]
                        sub_parts = [overlap_text]
                        sub_tokens = self._estimate_tokens(overlap_text)
                    sub_parts.append(sentence)
                    sub_tokens += s_tokens
                if sub_parts:
                    chunks.append(" ".join(sub_parts))
                continue

            # Normal merge: add paragraph to current chunk
            if current_tokens + para_tokens > self.chunk_size and current_parts:
                chunks.append("\n\n".join(current_parts))
                # Overlap: carry forward last paragraph(s) worth of ~overlap tokens
                overlap_parts: List[str] = []
                overlap_tokens = 0
                for p in reversed(current_parts):
                    p_tok = self._estimate_tokens(p)
                    if overlap_tokens + p_tok > self.overlap:
                        break
                    overlap_parts.insert(0, p)
                    overlap_tokens += p_tok
                current_parts = overlap_parts
                current_tokens = overlap_tokens

            current_parts.append(para)
            current_tokens += para_tokens

        # Flush remaining
        if current_parts:
            chunks.append("\n\n".join(current_parts))

        return chunks

    def _detect_section_title(self, chunk: str) -> str:
        """Extract the first section header found in a chunk, if any."""
        match = self._header_re.search(chunk)
        if match:
            return match.group(0).strip().lstrip("#").strip()
        return ""
