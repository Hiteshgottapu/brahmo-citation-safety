"""
Citation Annotator — inserts verification badges into text and generates reports.

Two outputs per run:
  • annotated_plain  — plain-text with emoji badges
  • annotated_html   — HTML with styled <span> badges
"""

from __future__ import annotations

import html as html_mod

from models import CitationResult, CostMetrics, ProcessingReport, ResponseNode


class CitationAnnotator:
    """Builds annotated text and summary reports from verification results."""

    # ------------------------------------------------------------------
    # Text annotation
    # ------------------------------------------------------------------

    def annotate_text(
        self, text: str, results: list[CitationResult]
    ) -> tuple[str, list[ResponseNode]]:
        """Replace each citation in *text* with a badged version and emit structured tokens.

        Returns (annotated_plain, annotated_nodes).
        """
        import re

        if not results:
            return text, [ResponseNode(type="text", content=html_mod.escape(text))]

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
        initial_nodes: list[ResponseNode] = []
        prev_end = 0

        for start, end, r in positioned:
            # Avoid overlapping replacements
            if start < prev_end:
                continue

            # Text before this citation (unchanged)
            text_before = text[prev_end:start]
            plain_parts.append(text_before)
            if text_before:
                initial_nodes.append(ResponseNode(type="text", content=html_mod.escape(text_before)))

            citation_text = r.original_text
            escaped = html_mod.escape(citation_text)

            if r.status == "VERIFIED":
                plain_parts.append(f"✅ {citation_text} [VERIFIED]")
                initial_nodes.append(ResponseNode(type="badge", content=escaped, variant="verified"))

            elif r.status == "CORRECTED":
                original_raw = (
                    r.citation.original_text
                    if r.citation.original_text != citation_text
                    else citation_text
                )
                note = r.correction_note or ""
                plain_parts.append(f"⚠️ {citation_text} [CORRECTED from {original_raw}]")
                initial_nodes.append(ResponseNode(type="badge", content=escaped, variant="corrected", correction_note=note))

            elif r.status == "UNVERIFIED":
                plain_parts.append(f"⚠️ {citation_text} [UNVERIFIED]")
                initial_nodes.append(ResponseNode(type="badge", content=escaped, variant="unverified"))

            elif r.status == "REMOVED":
                reason = r.reason or "Hallucinated"
                plain_parts.append(f"❌ {citation_text} [REMOVED — {reason}]")
                initial_nodes.append(ResponseNode(type="badge", content=escaped, variant="removed", removal_reason=reason))
                
            else:
                # Fallback — leave unchanged
                plain_parts.append(citation_text)
                initial_nodes.append(ResponseNode(type="text", content=escaped))

            prev_end = end

        # Remaining text after last citation
        text_after = text[prev_end:]
        plain_parts.append(text_after)
        if text_after:
            initial_nodes.append(ResponseNode(type="text", content=html_mod.escape(text_after)))

        plain = "".join(plain_parts)

        # -------------------------------------------------------------
        # HTML Rendering Layout Transformations via Token Post-Processing
        # -------------------------------------------------------------
        annotated_nodes: list[ResponseNode] = []
        
        # Regex for structural formatting
        strong_pattern = re.compile(
            r'(COMPLAINT\s+UNDER\s+(?:.*?)(?:BNS|IPC|CrPC|BNSS|BSA|IEA)(?:\s+AND\s+(?:.*?)(?:BNS|IPC|CrPC|BNSS|BSA|IEA))?\s*)(The\s+complainant|This\s+is|It\s+is|In\s+the|1\.)',
            re.IGNORECASE
        )

        for node in initial_nodes:
            if node.type != "text":
                annotated_nodes.append(node)
                continue
                
            content = node.content
            
            # Split by [USER QUERY]
            if "[USER QUERY]" in content:
                parts = content.split("[USER QUERY]")
                if parts[0].strip():
                    annotated_nodes.append(ResponseNode(type="text", content=parts[0]))
                annotated_nodes.append(ResponseNode(type="heading", content="INTERCEPTED USER QUERY", variant="user_query"))
                content = parts[1].lstrip() # Strip leading newlines after the marker
                
            # Split by [LLM ANALYSIS]
            if "[LLM ANALYSIS]" in content:
                parts = content.split("[LLM ANALYSIS]")
                if parts[0].strip():
                    annotated_nodes.append(ResponseNode(type="text", content=parts[0]))
                annotated_nodes.append(ResponseNode(type="heading", content="VERIFIED LEGAL COMPLAINT & ANALYSIS", variant="analysis"))
                content = parts[1].lstrip()
                
            # Apply strong typographic titles via regex finding
            last_idx = 0
            for match in strong_pattern.finditer(content):
                start, end = match.span()
                text_before = content[last_idx:start]
                if text_before:
                    annotated_nodes.append(ResponseNode(type="text", content=text_before))
                
                strong_title = match.group(1).strip()
                following_text = match.group(2)
                
                annotated_nodes.append(ResponseNode(type="strong", content=strong_title))
                annotated_nodes.append(ResponseNode(type="text", content="\n" + following_text))
                last_idx = end
                
            if last_idx < len(content):
                remaining_text = content[last_idx:]
                if remaining_text:
                    annotated_nodes.append(ResponseNode(type="text", content=remaining_text))

        return plain, annotated_nodes

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
