"""
Hallucination Detector — rule-based pre-filter for impossible citations.

Pure math.  No network calls.  Returns a status and reason string.
"""

from __future__ import annotations

from config import CURRENT_YEAR, MAX_SCC_VOLUME, MAX_PAGE, MIN_YEAR
from models import Citation


class HallucinationDetector:
    """Deterministic rules that flag citations as REMOVED or SUSPICIOUS."""

    def detect(self, citation: Citation) -> tuple[str, str]:
        """Apply rules in priority order.

        Returns
        -------
        (status, reason)
            status is one of 'REMOVED', 'SUSPICIOUS', or 'PASS'.
            reason is a human-readable explanation (empty string for PASS).
        """

        year = citation.year
        volume = citation.volume
        page = citation.page

        # Rule 1 — future year
        if year is not None and year > CURRENT_YEAR:
            return (
                "REMOVED",
                f"Future year {year} — citation cannot exist",
            )

        # Rule 2 — impossible SCC volume
        if (
            citation.pattern_name == "SCC"
            and volume is not None
            and volume > MAX_SCC_VOLUME
        ):
            return (
                "REMOVED",
                f"Impossible SCC volume {volume} — max ~20/year",
            )

        # Rule 3 — pre-modern year
        if year is not None and year < MIN_YEAR:
            return (
                "SUSPICIOUS",
                f"Pre-modern year {year} — Indian law reports did not exist",
            )

        # Rule 4 — unusually high page number
        if page is not None and page > MAX_PAGE:
            return (
                "SUSPICIOUS",
                f"Unusually high page number {page}",
            )

        # Default — nothing suspicious
        return ("PASS", "")
