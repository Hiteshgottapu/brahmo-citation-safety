"""
Section Normalizer — converts old IPC / CrPC / IEA references to BNS / BNSS / BSA.

Uses a hash-map of (section_number, act_abbreviation) loaded from Supabase
on first use (singleton pattern).
"""

from __future__ import annotations

import re
from typing import Optional

from database import get_supabase
from models import NormalizationResult, SectionAlert


class SectionNormalizer:
    """Singleton that normalizes repealed-statute section references in text."""

    _instance: Optional["SectionNormalizer"] = None
    _mappings: dict[tuple[str, str], dict] = {}
    _loaded: bool = False

    # Full-name → abbreviation reverse lookup
    _act_abbreviations: dict[str, str] = {
        "Indian Penal Code": "IPC",
        "Code of Criminal Procedure": "CrPC",
        "Indian Evidence Act": "IEA",
    }

    # Abbreviation → new-act abbreviation (for quick reference)
    _new_act_abbr: dict[str, str] = {
        "IPC": "BNS",
        "CrPC": "BNSS",
        "IEA": "BSA",
    }

    def __new__(cls) -> "SectionNormalizer":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    async def _load_mappings(self) -> None:
        """Fetch ALL rows from section_mappings and build the hash map."""
        if self._loaded:
            return

        supabase = await get_supabase()
        response = await supabase.table("section_mappings").select("*").execute()
        rows = response.data or []

        for row in rows:
            old_section: str = row["old_section"]   # e.g. "Section 420 IPC"
            new_section: str = row["new_section"]    # e.g. "Section 318 BNS"
            old_act: str = row["old_act"]            # e.g. "IPC" or full name
            new_act: str = row["new_act"]            # e.g. "BNS" or full name

            # Extract the section number from old_section string
            # Handles patterns like "Section 420 IPC", "Section 156(3) CrPC",
            # "Section 65B IEA", "Section 3(5) BNS", "Section 304A IPC"
            sec_match = re.match(
                r"Section\s+(\d+[A-Za-z]*(?:\(\d+\))?)\s+(\S+)", old_section
            )
            if sec_match:
                section_num = sec_match.group(1)   # e.g. "420", "156(3)", "65B"
                act_abbr = sec_match.group(2)       # e.g. "IPC", "CrPC", "IEA"
            else:
                # Fallback: try to parse best-effort
                parts = old_section.replace("Section ", "").rsplit(" ", 1)
                section_num = parts[0].strip()
                act_abbr = parts[1].strip() if len(parts) > 1 else old_act

            # Store under the abbreviation form
            key = (section_num.upper(), act_abbr.upper())
            self._mappings[key] = {
                "old_section": old_section,
                "new_section": new_section,
                "old_act": old_act,
                "new_act": new_act,
            }

            # Also store under any full-name alias
            for full_name, abbr in self._act_abbreviations.items():
                if abbr.upper() == act_abbr.upper():
                    full_key = (section_num.upper(), full_name.upper())
                    self._mappings[full_key] = {
                        "old_section": old_section,
                        "new_section": new_section,
                        "old_act": old_act,
                        "new_act": new_act,
                    }

        self._loaded = True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_act_abbr(self, raw_act: str) -> str:
        """Collapse full act names to their abbreviation (case-insensitive)."""
        for full_name, abbr in self._act_abbreviations.items():
            if raw_act.strip().lower() == full_name.lower():
                return abbr
        return raw_act.strip()

    def _lookup(self, section_num: str, act_text: str) -> Optional[dict]:
        """Look up the mapping for a given section+act combination."""
        act_abbr = self._resolve_act_abbr(act_text)
        key = (section_num.upper(), act_abbr.upper())
        return self._mappings.get(key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def normalize_text(self, text: str) -> NormalizationResult:
        """Scan *text* for old section references and replace them.

        Returns a NormalizationResult with the modified text and a list of
        SectionAlert objects for every replacement made.
        """
        await self._load_mappings()

        alerts: list[SectionAlert] = []
        result_text = text

        # ---- Pattern 2: plural "Sections 420, 406, 120B and 34 IPC" ----
        # Must run BEFORE singular so that "Sections …" is consumed first.
        plural_re = re.compile(
            r"Sections\s+"
            r"([\d+A-Za-z(),\s]+?(?:\s+and\s+\d+[A-Za-z]*(?:\(\d+\))?)?)"
            r"\s+(?:of\s+the\s+)?"
            r"(IPC|Indian Penal Code|CrPC|Code of Criminal Procedure|IEA|Indian Evidence Act)",
            re.IGNORECASE,
        )

        def _replace_plural(m: re.Match) -> str:
            raw_sections = m.group(1)
            act_text = m.group(2)

            # Split on commas and "and"
            parts = re.split(r",|\band\b", raw_sections)
            new_parts: list[str] = []
            local_alerts: list[SectionAlert] = []
            act_abbr = self._resolve_act_abbr(act_text)

            for part in parts:
                sec = part.strip()
                if not sec:
                    continue
                mapping = self._lookup(sec, act_text)
                if mapping:
                    # Extract just the number portion from the new section
                    new_sec_match = re.match(
                        r"Section\s+(.+?)\s+\S+", mapping["new_section"]
                    )
                    new_num = new_sec_match.group(1) if new_sec_match else mapping["new_section"]
                    new_parts.append(new_num)

                    new_act_abbr = self._new_act_abbr.get(act_abbr.upper(), mapping["new_act"])
                    local_alerts.append(
                        SectionAlert(
                            old_text=f"Section {sec} {act_abbr}",
                            new_text=f"Section {new_num} {new_act_abbr}",
                            old_act=mapping["old_act"],
                            new_act=mapping["new_act"],
                        )
                    )
                else:
                    new_parts.append(sec)

            if local_alerts:
                alerts.extend(local_alerts)
                new_act_abbr = self._new_act_abbr.get(
                    self._resolve_act_abbr(act_text).upper(), act_text
                )
                joined = ", ".join(new_parts[:-1]) + " and " + new_parts[-1] if len(new_parts) > 1 else new_parts[0]
                return f"Sections {joined} {new_act_abbr}"
            return m.group(0)

        result_text = plural_re.sub(_replace_plural, result_text)

        # ---- Pattern 1: singular "Section 420 IPC" / "Section 420 of the Indian Penal Code" ----
        singular_re = re.compile(
            r"Section\s+"
            r"(\d+[A-Za-z]*(?:\(\d+\))?)"
            r"\s+(?:of\s+the\s+)?"
            r"(IPC|Indian Penal Code|CrPC|Code of Criminal Procedure|IEA|Indian Evidence Act)",
            re.IGNORECASE,
        )

        def _replace_singular(m: re.Match) -> str:
            sec_num = m.group(1)
            act_text_local = m.group(2)
            mapping = self._lookup(sec_num, act_text_local)
            if mapping:
                act_abbr = self._resolve_act_abbr(act_text_local)
                new_sec_match = re.match(
                    r"Section\s+(.+?)\s+\S+", mapping["new_section"]
                )
                new_num = new_sec_match.group(1) if new_sec_match else mapping["new_section"]
                new_act_abbr = self._new_act_abbr.get(act_abbr.upper(), mapping["new_act"])
                replacement = f"Section {new_num} {new_act_abbr}"
                alerts.append(
                    SectionAlert(
                        old_text=m.group(0),
                        new_text=replacement,
                        old_act=mapping["old_act"],
                        new_act=mapping["new_act"],
                    )
                )
                return replacement
            return m.group(0)

        result_text = singular_re.sub(_replace_singular, result_text)

        return NormalizationResult(normalized_text=result_text, alerts=alerts)
