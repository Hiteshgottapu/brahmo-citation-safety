"""
Citation Repair — fixes common formatting errors in extracted citations.

Pure string manipulation; no network calls.
"""

from __future__ import annotations

import re

from models import Citation


class CitationRepair:
    """Applies deterministic formatting fixes to Citation objects."""

    # AIR court-code normalization map
    _air_court_codes: dict[str, str] = {
        "Delhi": "Del",
        "delhi": "Del",
        "Bombay": "Bom",
        "bombay": "Bom",
        "Calcutta": "Cal",
        "calcutta": "Cal",
        "Madras": "Mad",
        "madras": "Mad",
        "Allahabad": "All",
        "allahabad": "All",
        "Karnataka": "Kar",
        "karnataka": "Kar",
        "Kerala": "Ker",
        "kerala": "Ker",
        "Patna": "Pat",
        "patna": "Pat",
        "Rajasthan": "Raj",
        "rajasthan": "Raj",
        "Gujarat": "Guj",
        "gujarat": "Guj",
    }

    def repair_citation(
        self, citation: Citation
    ) -> tuple[Citation, bool, str]:
        """Return (repaired Citation, was_modified, correction_note)."""

        was_modified = False
        notes: list[str] = []
        new_text = citation.original_text

        # --- SCC repairs ---
        if citation.pattern_name == "SCC":
            # Fix missing space: "SCC123" -> "SCC 123"
            fixed, n = re.subn(r"SCC(\d)", r"SCC \1", new_text)
            if n:
                new_text = fixed
                was_modified = True
                notes.append("Fixed missing space in SCC citation")

            # Fix volume spacing: "5SCC" -> "5 SCC"
            fixed, n = re.subn(r"(\d)SCC", r"\1 SCC", new_text)
            if n:
                new_text = fixed
                was_modified = True
                notes.append("Fixed volume spacing in SCC citation")

        # --- SCC OnLine repairs ---
        elif citation.pattern_name == "SCC_OnLine":
            # Fix capitalization variants
            fixed, n = re.subn(
                r"SCC\s+Online", "SCC OnLine", new_text, flags=re.IGNORECASE
            )
            if n and fixed != new_text:
                new_text = fixed
                was_modified = True
                notes.append("Corrected SCC OnLine capitalization")

            # Also catch "scc online" fully lowercase
            fixed, n = re.subn(
                r"(?i)scc\s+online", "SCC OnLine", new_text
            )
            if n and fixed != new_text:
                new_text = fixed
                was_modified = True
                if "Corrected SCC OnLine capitalization" not in notes:
                    notes.append("Corrected SCC OnLine capitalization")

        # --- AIR repairs ---
        elif citation.pattern_name == "AIR":
            for long_name, short_code in self._air_court_codes.items():
                # Only replace the court token that appears after "AIR YYYY "
                pattern = re.compile(
                    r"(AIR\s+\d{4}\s+)" + re.escape(long_name) + r"(\s+)",
                    re.IGNORECASE,
                )
                fixed, n = pattern.subn(rf"\g<1>{short_code}\2", new_text)
                if n:
                    new_text = fixed
                    was_modified = True
                    notes.append(f"Normalized court code {long_name}→{short_code}")

        # Rebuild citation if modified
        if was_modified:
            repaired = citation.model_copy(update={"original_text": new_text})
            return repaired, True, "; ".join(notes)

        return citation, False, ""
