"""
Citation Extractor — finds all Indian legal citations in free text.

Patterns are loaded from the Supabase `citation_patterns` table on first use
(singleton).  Each regex is compiled once with re.IGNORECASE for flexible
matching.  Matches are deduplicated by start position so overlapping patterns
don't produce duplicate Citation objects.
"""

from __future__ import annotations

import re
from typing import Optional

from database import get_supabase
from models import Citation


class CitationExtractor:
    """Singleton that extracts Citation objects from text using DB-driven regex."""

    _instance: Optional["CitationExtractor"] = None
    _patterns: list[dict] = []
    _compiled: list[tuple[str, re.Pattern]] = []
    _loaded: bool = False

    def __new__(cls) -> "CitationExtractor":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    async def _load_patterns(self) -> None:
        """Fetch all 6 regex rules from citation_patterns and compile them."""
        if self._loaded:
            return

        supabase = await get_supabase()
        response = await supabase.table("citation_patterns").select("*").execute()
        rows = response.data or []

        self._patterns = rows
        self._compiled = []
        for row in rows:
            pattern_name = row["pattern_name"]
            regex_str = row["regex_pattern"]
            try:
                compiled = re.compile(regex_str, re.IGNORECASE)
                self._compiled.append((pattern_name, compiled))
            except re.error:
                # Skip malformed patterns — log in production
                pass

        self._loaded = True

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_citation(
        pattern_name: str,
        matched_text: str,
        groups: tuple,
    ) -> Citation:
        """Create a Citation with the right component mapping per format."""

        year: Optional[int] = None
        volume: Optional[int] = None
        page: Optional[int] = None
        court: Optional[str] = None
        components: dict = {}

        if pattern_name == "SCC":
            # groups: (year, volume, page)
            year = int(groups[0])
            volume = int(groups[1])
            page = int(groups[2])
            components = {"year": year, "volume": volume, "page": page}

        elif pattern_name == "SCC_OnLine":
            # groups: (year, court, number)
            year = int(groups[0])
            court = groups[1]
            number = int(groups[2])
            page = number
            components = {"year": year, "court": court, "number": number}

        elif pattern_name == "AIR":
            # groups: (year, court, page)
            year = int(groups[0])
            court = groups[1]
            page = int(groups[2])
            components = {"year": year, "court": court, "page": page}

        elif pattern_name == "Cri_LJ":
            # groups: (year, page)
            year = int(groups[0])
            page = int(groups[1])
            components = {"year": year, "page": page}

        elif pattern_name == "SCR":
            # groups: (year, volume, page)
            year = int(groups[0])
            volume = int(groups[1])
            page = int(groups[2])
            components = {"year": year, "volume": volume, "page": page}

        elif pattern_name == "MANU":
            # groups: (court, year, number) — but the seed regex may only
            # have a single capturing group for court; handle both layouts.
            if len(groups) >= 3:
                court = groups[0]
                year = int(groups[1])
                number = int(groups[2])
                components = {"court": court, "year": year, "number": number}
            elif len(groups) >= 1:
                court = groups[0]
                # Try to parse year from the matched text itself
                manu_parts = matched_text.split("/")
                if len(manu_parts) >= 4:
                    try:
                        year = int(manu_parts[2])
                    except ValueError:
                        pass
                    try:
                        number_val = int(manu_parts[3])
                        page = number_val
                        components = {"court": court, "year": year, "number": number_val}
                    except ValueError:
                        components = {"court": court, "year": year}
                else:
                    components = {"court": court}
        else:
            # Unknown / future pattern — store raw groups
            components = {f"group_{i}": g for i, g in enumerate(groups)}

        return Citation(
            original_text=matched_text,
            pattern_name=pattern_name,
            year=year,
            volume=volume,
            page=page,
            court=court,
            components=components,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_citations(self, text: str) -> list[Citation]:
        """Return all Citations found in *text*, deduplicated by start index."""
        await self._load_patterns()

        # Collect (start_index, Citation) tuples
        found: dict[int, Citation] = {}

        for pattern_name, compiled in self._compiled:
            for m in compiled.finditer(text):
                start = m.start()
                if start not in found:
                    citation = self._build_citation(
                        pattern_name, m.group(0), m.groups()
                    )
                    found[start] = citation

        # Sort by position and return
        return [found[k] for k in sorted(found.keys())]
