"""
Ingestion Router — Phase 1 pipeline endpoints.

  POST /api/ingest-document         → Ingest a single document
  POST /api/ingest-seed-documents   → Bulk-ingest 12 pre-written legal docs
  GET  /api/knowledge-base/stats    → Chunk count + embedding coverage
"""

from __future__ import annotations

from fastapi import APIRouter

from database import get_supabase
from engine.chunker import DocumentChunker
from engine.embedder import embedder
from models import IngestDocumentRequest

router = APIRouter()

# ======================================================================
# 12 seed legal knowledge documents
# ======================================================================

SEED_DOCUMENTS: list[dict] = [
    {
        "doc_id": "anticipatory_bail_sc",
        "doc_title": "SC Precedents on Anticipatory Bail",
        "content": """## Anticipatory Bail — Supreme Court Framework

The Supreme Court has established comprehensive principles governing anticipatory bail under Section 438 of the Code of Criminal Procedure (now Section 482 BNSS).

In Siddharth v. State of UP (2021) 10 SCC 1, the Supreme Court laid down exhaustive guidelines clarifying that anticipatory bail should not be denied merely because the accusation involves economic offences. The Court emphasized that personal liberty under Article 21 is paramount and that the nature of the accusation alone cannot be a ground for refusal.

The landmark Constitution Bench decision in Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1 settled the long-standing controversy by holding that anticipatory bail can be granted without any time limit. The Court overruled the earlier view that anticipatory bail must be of limited duration.

In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, the Court issued comprehensive guidelines to prevent unnecessary arrests, particularly in cases punishable with imprisonment up to seven years. The guidelines mandate that the police officer must be satisfied that the arrest is necessary based on specific parameters before effecting arrest.

The decision in Satender Kumar Antil v. CBI (2022) 10 SCC 51 further categorized offences into different categories for the purpose of bail, establishing that for offences carrying up to 7 years imprisonment, bail should generally be granted. The Court specifically addressed economic offences and noted that severity of punishment alone should not dictate bail decisions.""",
        "metadata": {"topic": "anticipatory_bail", "jurisdiction": "Supreme Court", "practice": "Criminal"},
    },
    {
        "doc_id": "anticipatory_bail_economic",
        "doc_title": "Anticipatory Bail in Economic Offences — Recent Developments",
        "content": """## Economic Offences and Anticipatory Bail

The intersection of economic offences and anticipatory bail has been a contentious area. The Delhi High Court in 2024 SCC OnLine Del 3456 granted anticipatory bail in a case involving Section 318 BNS (formerly Section 420 IPC — cheating), where the accused demonstrated full cooperation with the investigation and no flight risk.

The Supreme Court in P. Chidambaram v. Directorate of Enforcement (2019) 9 SCC 24 held that economic offences constitute a class apart and noted that while the gravity of the offence is relevant, it cannot be the sole criterion for denying bail.

In Vijay Madanlal Choudhary v. Union of India (2022) 10 SCC 1, the Court upheld the constitutional validity of stringent bail provisions under PMLA while acknowledging that the twin conditions under Section 45 PMLA must be strictly complied with.

The Enforcement Directorate's power of arrest was examined in V. Senthil Balaji v. State (2024) 3 SCC 51, where the Court reiterated that arrest under PMLA must satisfy the requirements of necessity and must not be mechanical.

Key principles emerging from recent jurisprudence:
1. Personal liberty remains the paramount consideration
2. Economic offence alone does not justify denial of bail
3. Flight risk and evidence tampering must be specifically demonstrated
4. Cooperation with investigation weighs in favour of bail
5. Duration of incarceration is a relevant factor""",
        "metadata": {"topic": "anticipatory_bail", "jurisdiction": "Supreme Court", "practice": "Criminal"},
    },
    {
        "doc_id": "cheating_ipc_420",
        "doc_title": "Criminal Complaint Framework — Cheating Under IPC/BNS",
        "content": """## Complaint for Cheating and Criminal Breach of Trust

The offence of cheating is defined under Section 420 of the Indian Penal Code (now Section 318 of the Bharatiya Nyaya Sanhita). Criminal breach of trust is covered under Section 406 IPC (now Section 316 BNS).

A complaint under Sections 420, 406, 120B and 34 of the Indian Penal Code must establish:

1. CHEATING (Section 420 IPC / Section 318 BNS): The accused deceived the complainant by making a false representation or by concealing facts, and thereby dishonestly induced the complainant to deliver property or valuable security.

2. CRIMINAL BREACH OF TRUST (Section 406 IPC / Section 316 BNS): The accused was entrusted with property or dominion over property and dishonestly misappropriated or converted it to their own use.

3. CRIMINAL CONSPIRACY (Section 120B IPC / Section 61 BNS): Two or more persons agreed to commit an illegal act or a legal act by illegal means.

4. COMMON INTENTION (Section 34 IPC / Section 3(5) BNS): The criminal act was done by several persons in furtherance of common intention.

In Iridium India Telecom Ltd v. Motorola Inc (2011) 1 SCC 74, the Supreme Court held that for Section 420 IPC to apply, there must be an initial fraudulent intention at the time of making the promise.

The Supreme Court in Hridaya Ranjan Prasad Verma v. State of Bihar (2000) 4 SCC 168 clarified the distinction between a mere breach of contract and cheating, holding that subsequent breach of promise is not necessarily cheating unless the intention to cheat existed from the inception.

For filing a complaint under Section 156(3) CrPC (now Section 175(3) BNSS), the Magistrate must apply judicial mind to the complaint and the documents before ordering investigation. In Priyanka Srivastava v. State of UP (2015) 6 SCC 287, the Court held that an affidavit is mandatory when invoking Section 156(3) CrPC.

The complainant should include:
- Specific dates and amounts involved
- Documentary evidence of the false representation
- Proof of delivery of property based on the false promise
- Evidence of the accused's fraudulent intent ab initio
- Witness statements supporting the complaint allegations""",
        "metadata": {"topic": "cheating", "jurisdiction": "Magistrate Court", "practice": "Criminal"},
    },
    {
        "doc_id": "ndps_bail_overview",
        "doc_title": "NDPS Act — Bail Jurisprudence (2020-2025)",
        "content": """## Supreme Court Approach to Bail in NDPS Cases

The Narcotic Drugs and Psychotropic Substances Act, 1985 imposes stringent conditions for bail under Section 37, which creates a dual requirement: (a) reasonable grounds for believing the accused is not guilty, and (b) that the accused is not likely to commit any offence while on bail.

In Union of India v. Mohanlal (2016) 3 SCC 379, the Supreme Court strictly interpreted Section 37 and held that the twin conditions are mandatory and must be satisfied before bail can be granted in cases involving commercial quantity.

The watershed judgment in Tofan Singh v. State of Tamil Nadu (2021) 4 SCC 1 held that statements recorded under Section 67 of the NDPS Act are inadmissible as confessions under Section 25 of the Indian Evidence Act (now Section 23 BSA). This significantly impacted prosecution cases built primarily on confessional statements.

In Mohd. Muslim v. State (NCT of Delhi) (2023) 4 SCC 789, the Court addressed whether possession of commercial quantity mandates automatic denial of bail, holding that each case must be examined on its own merits.

In Arvind Kumar v. State of UP AIR 2024 SC 567, the Court reiterated that prolonged incarceration without trial is a valid ground for bail even in NDPS cases, invoking Article 21 of the Constitution.

The interplay between Section 37 NDPS Act and Article 21 was extensively discussed in Pradeep Kumar v. State of Haryana (2023) 19 SCC 456, where the Court held that unreasonable delay in trial tilts the balance in favour of the accused.

In Narcotics Control Bureau v. Mohit Aggarwal 2024 SCC OnLine SC 2345, the Court provided clarity on the meaning of "reasonable grounds" under Section 37, holding that the court must look at the totality of circumstances including the quality of evidence.""",
        "metadata": {"topic": "ndps_bail", "jurisdiction": "Supreme Court", "practice": "Criminal"},
    },
    {
        "doc_id": "ndps_hallucination_test",
        "doc_title": "NDPS Extended Research — Test Scenarios",
        "content": """## NDPS Extended Case Analysis with Edge Cases

Building on the NDPS bail framework, additional cases provide further guidance:

In State of Kerala v. Rajesh (2028) 3 SCC 45, the Court set out a comprehensive framework for bail in NDPS cases, establishing a multi-factor test that considers the quantity seized, the accused's antecedents, the likelihood of tampering with evidence, and the progress of investigation.

In Satish Sharma v. NCB (2024) 47 SCC 123, the Court addressed the role of electronic evidence in NDPS prosecutions and held that call detail records and GPS data must be independently verified before relying upon them.

The above decisions should be contrasted with the settled position in Narayan Mandal v. State of Bihar AIR 2025 SC 789 where the Court applied the established principles to grant bail in a case involving intermediate quantity.

In NCB v. Sameer Wankhede 2024 SCC OnLine SC 5678, the Court examined the procedural safeguards required during search and seizure operations under the NDPS Act.

The Delhi High Court in State v. Mohd. Irfan (2024) 6 SCC 234 provided guidance on the application of Section 37 when multiple accused are involved in the same transaction.

Key takeaway: Courts have increasingly moved towards a more nuanced approach, balancing the statutory mandate of Section 37 with constitutional protections under Article 21.""",
        "metadata": {"topic": "ndps_bail", "jurisdiction": "Supreme Court", "practice": "Criminal"},
    },
    {
        "doc_id": "section_482_bnss",
        "doc_title": "Section 482 BNSS — Inherent Powers of High Court",
        "content": """## Inherent Powers Under Section 482 BNSS (Formerly Section 482 CrPC)

The inherent powers of the High Court under Section 482 of the Bharatiya Nagarik Suraksha Sanhita (formerly Section 482 of the Code of Criminal Procedure) are preserved to prevent abuse of process and to secure the ends of justice.

In Rajiv Gupta v. State of NCT of Delhi 2024 SCC OnLine Del 3456, the Delhi High Court discussed the scope of inherent powers and held that the power under Section 482 BNSS is wider than the power of revision and can be exercised to quash proceedings at any stage.

In Smt. Kavita v. State AIR 2024 Delhi 234, the Court held that Section 482 powers should be exercised sparingly and with circumspection, particularly when factual disputes are involved.

In Mohd. Salim v. State of NCT of Delhi (2023) 5 SCC 123, the Court addressed quashing of FIRs in matrimonial disputes and held that the High Court should consider the object and purpose of the legislation while exercising inherent powers.

In Priya Sharma v. State 2024 SCC OnLine Del 7890, the Court reiterated the seven categories laid down in State of Haryana v. Bhajan Lal 1992 Supp (1) SCC 335 for quashing of FIRs.

In Ashok Kumar v. State of NCT of Delhi (2024) 3 SCC 456, the Court discussed the parameters for exercising inherent jurisdiction, emphasizing that the allegations in the FIR must be taken at face value.

In State v. Harish Chand MANU/DE/4567/2024, the Delhi High Court provided guidance on quashing proceedings at the charge stage, holding that the court must examine whether the charge sheet discloses sufficient material to constitute the alleged offence.

The Bhajan Lal guidelines remain the cornerstone:
1. Where the allegations do not prima facie constitute any offence
2. Where the allegations are absurd and improbable
3. Where there is a legal bar to prosecution
4. Where the criminal proceeding is manifestly attended with mala fide
5. Where there is prevention of abuse of process
6. Where there is a non-compoundable offence settled between parties
7. Where the dispute is essentially civil in nature""",
        "metadata": {"topic": "section_482", "jurisdiction": "Delhi High Court", "practice": "Criminal"},
    },
    {
        "doc_id": "nda_indian_law",
        "doc_title": "NDA Review Framework — Indian Law Requirements",
        "content": """## Non-Disclosure Agreement Review Under Indian Law

When reviewing a Non-Disclosure Agreement (NDA) under Indian law, the following provisions of the Indian Contract Act, 1872 and related statutes must be considered:

1. VALIDITY AND ENFORCEABILITY: Under Section 10 of the Indian Contract Act, an NDA must satisfy the basic requirements of a valid contract — free consent, lawful consideration, lawful object, and competent parties.

2. DEFINITION OF CONFIDENTIAL INFORMATION: The NDA must clearly define what constitutes confidential information. Overly broad definitions may be struck down as unreasonable restraint of trade under Section 27 of the Indian Contract Act.

3. TERM AND SURVIVAL: Indian courts have upheld reasonable time-limited confidentiality obligations. In Niranjan Shankar Golikari v. Century Spinning Co AIR 1967 SC 1098, the Supreme Court held that reasonable restrictions during the term of employment are valid.

4. REMEDIES AND INJUNCTIVE RELIEF: The Specific Relief Act, 1963 (Sections 36-42) governs injunctive relief. In Dalpat Kumar v. Prahlad Singh (1992) 1 SCC 719, the Court discussed the principles governing grant of temporary injunctions.

5. GOVERNING LAW AND JURISDICTION: For international NDAs, the Indian Arbitration and Conciliation Act, 1996 provides the framework for dispute resolution.

6. DATA PROTECTION: With the Digital Personal Data Protection Act, 2023 coming into force, NDAs must address data protection obligations and breach notification requirements.

Missing clauses commonly flagged:
- Return or destruction of confidential materials
- Carve-outs for legally compelled disclosures
- Non-solicitation provisions (must be reasonable)
- Assignment and sub-licensing restrictions
- Intellectual property ownership clarification""",
        "metadata": {"topic": "nda_review", "jurisdiction": "N/A", "practice": "Corporate"},
    },
    {
        "doc_id": "oppression_nclt",
        "doc_title": "Oppression and Mismanagement — NCLT Proceedings",
        "content": """## Grounds for NCLT Petition — Oppression and Mismanagement

Sections 241-246 of the Companies Act, 2013 provide the framework for relief against oppression and mismanagement before the National Company Law Tribunal (NCLT).

LOCUS STANDI (Section 244): A petition may be filed by:
- Members holding not less than 1/10th of the issued share capital (or 100 members, whichever is less) for a company having share capital
- Not less than 1/5th of the total members for a company without share capital

GROUNDS FOR PETITION (Section 241):
1. The affairs of the company are being conducted in a manner prejudicial to public interest or oppressive to any member
2. A material change has taken place in the management or control which is likely to result in the affairs being conducted prejudicially

In Cyrus Investments Pvt Ltd v. Tata Sons Pvt Ltd (2021) 2 SCC 1, the Supreme Court extensively discussed the concept of oppression and mismanagement, holding that mere dissatisfaction with management decisions does not constitute oppression. The majority held that the NCLT/NCLAT exceeded its jurisdiction in reinstating a removed director.

In Rajeev Saumitra v. Neetu Singh (2016) 1 SCC 724, the Court held that the test for oppression is whether a reasonable objective bystander would consider the conduct as being oppressive to the minority shareholders.

In Shanti Prasad Jain v. Kalinga Tubes Ltd AIR 1965 SC 1535, the Court established that oppression implies a visible departure from fair dealing and a violation of conditions of fair play on which every shareholder is entitled to rely.

KEY RELIEFS AVAILABLE (Section 242):
- Regulation of company affairs
- Purchase of shares by other members or the company
- Restriction on transfer of shares
- Removal of managing director or manager
- Appointment of additional directors
- Setting aside of agreements or modifications thereof""",
        "metadata": {"topic": "oppression_mismanagement", "jurisdiction": "NCLT", "practice": "Corporate"},
    },
    {
        "doc_id": "specific_performance",
        "doc_title": "Specific Performance of Immovable Property Sale Agreement",
        "content": """## Specific Performance — Sale of Immovable Property

The Specific Relief Act, 1963 (as amended in 2018) governs suits for specific performance of contracts relating to immovable property.

POST-2018 AMENDMENT: Section 10 now provides that specific performance shall be enforced by the court as a general rule, subject to Section 11(2), Section 14 and Section 16. The erstwhile position that specific performance was discretionary has been fundamentally altered.

In Chand Rani v. Kamal Rani (1993) 1 SCC 519, the Supreme Court held that in a suit for specific performance, the plaintiff must prove:
1. Existence of a valid and enforceable contract
2. Readiness and willingness to perform the contract
3. That the plaintiff has performed or has always been ready to perform the essential terms

In Indian Oil Corporation v. Amritsar Gas Service (1991) 1 SCC 533, the Court held that time is not ordinarily of the essence in contracts for sale of immovable property unless specifically made so.

READINESS AND WILLINGNESS (Section 16(c)): In Saradamani Kandappan v. S. Rajalakshmi (2011) 12 SCC 18, the Court held that readiness and willingness must be averred and proved throughout — from the date of contract to the date of hearing.

LIMITATION: Under Article 54 of the Limitation Act, 1963, a suit for specific performance must be filed within 3 years from the date fixed for performance, or if no date is fixed, within 3 years from when the plaintiff has notice of refusal.

RECENT DEVELOPMENTS: The Supreme Court in Kamal Kumar v. Premlata Joshi (2020) 14 SCC 440 held that partial performance or acts in furtherance of the contract, such as payment of substantial sale consideration, strengthens the case for specific performance.""",
        "metadata": {"topic": "specific_performance", "jurisdiction": "Civil Court", "practice": "Property"},
    },
    {
        "doc_id": "divorce_hma_s13",
        "doc_title": "Contested Divorce Under Hindu Marriage Act — Section 13",
        "content": """## Grounds for Contested Divorce Under Hindu Marriage Act Section 13

Section 13 of the Hindu Marriage Act, 1955 provides the grounds on which a decree of divorce may be granted:

SECTION 13(1) — GROUNDS AVAILABLE TO BOTH HUSBAND AND WIFE:
(i) ADULTERY: The respondent has had voluntary sexual intercourse with any person other than the spouse.
(ii) CRUELTY: The respondent has treated the petitioner with cruelty. In Shobha Rani v. Madhukar Reddi (1988) 1 SCC 105, the Court held that cruelty includes both physical and mental cruelty.
(iii) DESERTION: The respondent has deserted the petitioner for a continuous period of not less than two years. In Bipin Chander Jaisinghbhai Shah v. Prabhawati (1957) 1 SCR 838, the Court defined desertion as the withdrawal from cohabitation without reasonable cause and without consent.
(iv) CONVERSION: The respondent has ceased to be a Hindu by conversion to another religion.
(v) UNSOUNDNESS OF MIND: The respondent has been incurably of unsound mind for a continuous period of not less than three years.
(vi) LEPROSY: Virulent and incurable leprosy (now read down).
(vii) VENEREAL DISEASE: Not cured for at least three years.
(viii) RENUNCIATION: The respondent has renounced the world.
(ix) NOT HEARD ALIVE: The respondent has not been heard of as being alive for at least seven years.

SECTION 13(1A) — ADDITIONAL GROUNDS:
Either party may present a petition on the ground that there has been no resumption of cohabitation for one year after a decree of judicial separation, or no restitution of conjugal rights for one year after a decree.

In Naveen Kohli v. Neelu Kohli (2006) 4 SCC 558, the Supreme Court held that where the marriage has irretrievably broken down, the Court may grant divorce under Article 142, even if none of the grounds under Section 13 are technically proved.

In Samar Ghosh v. Jaya Ghosh (2007) 4 SCC 511, the Court laid down illustrative instances of mental cruelty, establishing that mental cruelty is necessarily a question of fact and must be judged based on the totality of circumstances.""",
        "metadata": {"topic": "divorce", "jurisdiction": "Family Court", "practice": "Family"},
    },
    {
        "doc_id": "fundamental_rights_art21",
        "doc_title": "Article 21 — Right to Life and Personal Liberty",
        "content": """## Article 21 — Foundational Jurisprudence

Article 21 of the Constitution of India provides: "No person shall be deprived of his life or personal liberty except according to procedure established by law."

In Maneka Gandhi v. Union of India (1978) 1 SCC 248, the Supreme Court revolutionized constitutional jurisprudence by holding that the procedure established by law must be right, just, and fair — not arbitrary, fanciful, or oppressive. This case expanded the scope of Article 21 far beyond mere animal existence to include the right to live with dignity.

The right to privacy was recognized as a fundamental right under Article 21 in K.S. Puttaswamy v. Union of India (2017) 10 SCC 1 (Privacy-9). The nine-judge Constitution Bench unanimously held that privacy is an intrinsic part of the right to life and personal liberty.

In Vishaka v. State of Rajasthan (1997) 6 SCC 241, the Supreme Court laid down guidelines for prevention of sexual harassment at the workplace, deriving the right from Articles 14, 15, 19(1)(g), and 21.

The right to a speedy trial was recognized as part of Article 21 in Hussainara Khatoon v. Home Secretary, State of Bihar (1980) 1 SCC 81.

In Francis Coralie Mullin v. Administrator, Union Territory of Delhi (1981) 1 SCC 608, the Court held that the right to life includes the right to live with basic human dignity and all that goes along with it.

These foundational cases continue to shape contemporary legal discourse across all areas of Indian law, from criminal justice to environmental protection to digital rights.""",
        "metadata": {"topic": "fundamental_rights", "jurisdiction": "Supreme Court", "practice": "Constitutional"},
    },
    {
        "doc_id": "evidence_admissibility",
        "doc_title": "Digital Evidence Admissibility — IEA to BSA Transition",
        "content": """## Admissibility of Digital Evidence

The transition from the Indian Evidence Act, 1872 to the Bharatiya Sakshya Adhiniyam (BSA), 2023 has significant implications for the admissibility of electronic evidence.

Under the old regime, Section 65B of the Indian Evidence Act (now Section 63 BSA) governs the admissibility of electronic records. The Supreme Court in Anvar P.V. v. P.K. Basheer (2014) 10 SCC 473 held that electronic evidence is admissible only if accompanied by a certificate under Section 65B(4) IEA.

However, in Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal (2020) 7 SCC 1, a three-judge bench clarified that the requirement of certificate under Section 65B(4) is mandatory and cannot be dispensed with.

KEY CHANGES UNDER BSA:
1. Section 63 BSA replaces Section 65B IEA with substantively similar provisions
2. The certificate requirement is retained under Section 63(4) BSA
3. The definition of "electronic record" now explicitly includes data stored in cloud computing, IoT devices, and social media platforms

In Shafhi Mohammad v. State of HP (2018) 2 SCC 801, the Court held that the requirement of certificate can be relaxed when the electronic evidence is produced by a person who is not in possession of the device.

PRACTICAL CONSIDERATIONS:
- WhatsApp messages, emails, CCTV footage, and call records all require Section 63 BSA certification
- Hash values and metadata should be preserved to establish authenticity
- Chain of custody documentation is essential
- Expert opinion under Section 45 IEA (Section 39 BSA) may be required for complex digital forensics""",
        "metadata": {"topic": "digital_evidence", "jurisdiction": "All Courts", "practice": "Criminal"},
    },
]


# ======================================================================
# Endpoints
# ======================================================================

@router.post("/api/ingest-document")
async def ingest_document(request: IngestDocumentRequest):
    """Phase 1 pipeline: Parse → Chunk → Embed → Store in pgvector."""
    chunker = DocumentChunker(chunk_size=400, overlap=80)

    # Step 1: Chunk the document
    chunks = chunker.chunk_text(
        text=request.content,
        doc_id=request.doc_id,
        doc_title=request.doc_title,
    )

    if not chunks:
        return {"status": "error", "message": "No chunks produced from document"}

    # Step 2: Embed all chunks in parallel
    texts = [c["content"] for c in chunks]
    embeddings = await embedder.embed_batch(texts)

    # Step 3: Store in Supabase pgvector
    supabase = await get_supabase()
    inserted_count = 0

    for chunk, emb in zip(chunks, embeddings):
        # FIX: Serialize embedding list to pgvector-safe string format
        embedding_str = f"[{','.join(map(str, emb))}]"

        row = {
            "doc_id": request.doc_id,
            "doc_title": request.doc_title,
            "chunk_index": chunk["chunk_index"],
            "content": chunk["content"],
            "metadata": {**chunk["metadata"], **request.metadata},
            "embedding": embedding_str,
        }

        try:
            await supabase.table("document_chunks").insert(row).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Failed to insert chunk {chunk['chunk_index']}: {e}")

    return {
        "status": "ok",
        "doc_id": request.doc_id,
        "chunks_created": inserted_count,
        "total_chunks": len(chunks),
    }


@router.post("/api/ingest-seed-documents")
async def ingest_seed_documents():
    """Bulk-ingest all 12 pre-written legal knowledge documents.

    This is the Phase 1 one-time setup: Parse → Chunk → Embed → pgvector.
    """
    results = []

    for doc in SEED_DOCUMENTS:
        req = IngestDocumentRequest(
            doc_id=doc["doc_id"],
            doc_title=doc["doc_title"],
            content=doc["content"],
            metadata=doc.get("metadata", {}),
        )

        try:
            result = await ingest_document(req)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "doc_id": doc["doc_id"],
                "message": str(e),
            })

    total_docs = len(results)
    total_chunks = sum(r.get("chunks_created", 0) for r in results)
    errors = sum(1 for r in results if r.get("status") == "error")

    return {
        "status": "ok",
        "total_documents": total_docs,
        "total_chunks_created": total_chunks,
        "errors": errors,
        "details": results,
    }


@router.get("/api/knowledge-base/stats")
async def knowledge_base_stats():
    """Return knowledge base statistics."""
    supabase = await get_supabase()

    try:
        # Total chunks
        response = await supabase.table("document_chunks").select("id", count="exact").execute()
        total_chunks = response.count or 0

        # Distinct documents
        response = await supabase.table("document_chunks").select("doc_id").execute()
        doc_ids = set(r["doc_id"] for r in (response.data or []))
        total_docs = len(doc_ids)

        return {
            "status": "ok",
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "documents": sorted(doc_ids),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total_documents": 0,
            "total_chunks": 0,
        }
