"""
Citation Annotator — inserts verification badges into text and generates reports.

Two outputs per run:
  • annotated_plain  — plain-text with emoji badges
  • annotated_html   — HTML with styled <span> badges
"""

from __future__ import annotations

import html as html_mod

from models import CitationResult, CostMetrics, ProcessingReport


class CitationAnnotator:
    """Builds annotated text and summary reports from verification results."""

    # ------------------------------------------------------------------
    # Text annotation
    # ------------------------------------------------------------------

    def annotate_text(
        self, text: str, results: list[CitationResult]
    ) -> tuple[str, str]:
        """Replace each citation in *text* with a badged version.

        Returns (annotated_plain, annotated_html).
        """

        if not results:
            return text, text

        # Build a list of (start_index, end_index, result) sorted by position
        positioned: list[tuple[int, int, CitationResult]] = []
        for r in results:
            search_text = r.original_text
            idx = text.find(search_text)
            if idx != -1:
                positioned.append((idx, idx + len(search_text), r))

        # Sort by start position (earliest first)
        positioned.sort(key=lambda t: t[0])

        # Walk through the text and build both outputs simultaneously
        plain_parts: list[str] = []
        html_parts: list[str] = []
        prev_end = 0

        for start, end, r in positioned:
            # Avoid overlapping replacements
            if start < prev_end:
                continue

            # Text before this citation (unchanged)
            plain_parts.append(text[prev_end:start])
            html_parts.append(html_mod.escape(text[prev_end:start]))

            citation_text = r.original_text
            escaped = html_mod.escape(citation_text)

            if r.status == "VERIFIED":
                plain_parts.append(f"✅ {citation_text} [VERIFIED]")
                html_parts.append(
                    f'<span class="citation-verified">{escaped} '
                    f'<span class="badge badge-verified">✅ VERIFIED</span>'
                    f"</span>"
                )

            elif r.status == "CORRECTED":
                original_raw = (
                    r.citation.original_text
                    if r.citation.original_text != citation_text
                    else citation_text
                )
                note = r.correction_note or ""
                plain_parts.append(
                    f"⚠️ {citation_text} [CORRECTED from {original_raw}]"
                )
                html_parts.append(
                    f'<span class="citation-corrected">{escaped} '
                    f'<span class="badge badge-corrected">⚠️ CORRECTED</span> '
                    f'<span class="correction-note">was: {html_mod.escape(original_raw)}</span>'
                    f"</span>"
                )

            elif r.status == "UNVERIFIED":
                plain_parts.append(f"⚠️ {citation_text} [UNVERIFIED]")
                html_parts.append(
                    f'<span class="citation-unverified">{escaped} '
                    f'<span class="badge badge-unverified">⚠️ UNVERIFIED</span>'
                    f"</span>"
                )

            elif r.status == "REMOVED":
                reason = r.reason or "Hallucinated"
                plain_parts.append(
                    f"❌ {citation_text} [REMOVED — {reason}]"
                )
                html_parts.append(
                    f'<span class="citation-removed"><del>{escaped}</del> '
                    f'<span class="badge badge-removed">❌ REMOVED</span> '
                    f'<span class="removal-reason">{html_mod.escape(reason)}</span>'
                    f"</span> "
                )
            else:
                # Fallback — leave unchanged
                plain_parts.append(citation_text)
                html_parts.append(escaped)

            prev_end = end

        # Remaining text after last citation
        plain_parts.append(text[prev_end:])
        html_parts.append(html_mod.escape(text[prev_end:]))

        plain = "".join(plain_parts)
        html = "".join(html_parts)

        # -------------------------------------------------------------
        # HTML Rendering Layout Transformations
        # -------------------------------------------------------------
        if "[USER QUERY]" in html and "[LLM ANALYSIS]" in html:
            import re
            parts = html.split("[LLM ANALYSIS]")
            user_part = parts[0].replace("[USER QUERY]", "").strip()
            llm_part = parts[1].strip()

            # Format user part newlines
            user_part = user_part.replace("\n", "<br/>")

            # Typographic Cleanup for Structural Titles
            # Catch "COMPLAINT UNDER Section XXX BNS AND Section YYY BNS" that was merged into paragraph text.
            llm_part = re.sub(
                r'(COMPLAINT\s+UNDER\s+(?:.*?)(?:BNS|IPC|CrPC|BNSS|BSA|IEA)(?:\s+AND\s+(?:.*?)(?:BNS|IPC|CrPC|BNSS|BSA|IEA))?\s*)(The\s+complainant|This\s+is|It\s+is|In\s+the|1\.)', 
                r'<strong class="block text-white text-[15px] font-bold mt-2 mb-4 border-b border-slate-700/50 pb-2">\1</strong>\n\2', 
                llm_part, 
                count=1,
                flags=re.IGNORECASE
            )

            # Build Component A & B
            html = (
                f'<div class="bg-slate-900/40 rounded-lg p-3 border border-slate-800 text-slate-300 italic text-xs leading-relaxed mb-4">'
                f'<div class="font-sans text-[10px] font-bold text-slate-500 tracking-wider mb-2 uppercase not-italic">🎯 INTERCEPTED USER QUERY</div>'
                f'<div class="whitespace-pre-wrap">{user_part}</div>'
                f'</div>'
                f'<hr class="border-t border-slate-700/50 my-6" />'
                f'<h3 class="mt-6 mb-3 text-sm font-bold tracking-wide text-slate-200 uppercase flex items-center gap-2">⚖️ VERIFIED LEGAL COMPLAINT & ANALYSIS</h3>'
                f'<div class="text-slate-200 text-sm font-sans leading-7 tracking-normal whitespace-pre-wrap selection:bg-purple-500/30">'
                f'{llm_part}'
                f'</div>'
            )
        else:
            html = html.replace("\n", "<br/>")

        return plain, html

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_report(
        self,
        results: list[CitationResult],
        cost_metrics: CostMetrics,
    ) -> ProcessingReport:
        """Produce a ProcessingReport from the list of results."""

        total = len(results)
        verified = sum(1 for r in results if r.status == "VERIFIED")
        corrected = sum(1 for r in results if r.status == "CORRECTED")
        unverified = sum(1 for r in results if r.status == "UNVERIFIED")
        removed = sum(1 for r in results if r.status == "REMOVED")

        # Exclude UNVERIFIED from the denominator to measure strict pipeline efficacy
        effective_total = total - unverified

        accuracy = (
            ((verified + corrected) / effective_total * 100) if effective_total > 0 else 100.0
        )
        api_calls = cost_metrics.total_searches + cost_metrics.total_docmeta

        return ProcessingReport(
            total_citations=total,
            verified=verified,
            corrected=corrected,
            unverified=unverified,
            removed=removed,
            accuracy_pct=round(accuracy, 1),
            cost_metrics=cost_metrics,
            api_calls_made=api_calls,
        )
