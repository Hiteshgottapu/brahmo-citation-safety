# Brahmo Legal Safety Engine: Database Schema Ledger & Ingestion Strategy

---

## 1. SCHEMA ARCHITECTURE & DESIGN DECISIONS

### Migration Rationale
To maximize spatial indexing performance and minimize cloud latency, the Brahmo database architecture was explicitly shifted from an open-ended vector footprint to a tightly clamped, high-speed **768-dimensional float embedding array constraint**. By standardizing entirely on Google's `text-embedding-004` model footprint, we achieve deterministic query execution times and eliminate vector dimensionality mismatches during cosine distance comparisons.

### Supabase PostgreSQL DDL Migrations
The following exact schema migrations were executed in the Supabase SQL Editor to establish the production environment.

#### Document Chunks Table
Houses the parsed legal corpus text blocks linked directly to a vector column restricted strictly to 768 dimensions.
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id              SERIAL PRIMARY KEY,
    doc_id          VARCHAR(100)  NOT NULL,       
    doc_title       TEXT          NOT NULL,        
    chunk_index     INT           NOT NULL,        
    content         TEXT          NOT NULL,        
    metadata        JSONB         DEFAULT '{}',    
    embedding       VECTOR(768),                   
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id
    ON document_chunks (doc_id);
```

#### Session History Telemetry Table
Permanently stores recent verification history sessions with JSONB payload blobs for badge counts, section alerts, cost reports, and a chronological index tracking descending timestamps.
```sql
CREATE TABLE IF NOT EXISTS session_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_area   VARCHAR(255) NOT NULL,
    query_snippet   TEXT NOT NULL,
    cached_query    TEXT NOT NULL,
    cached_raw_text TEXT,
    cached_html     TEXT,
    badge_counts    JSONB DEFAULT '{}',
    section_alerts  JSONB DEFAULT '[]',
    cached_report   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_history_created_at
    ON session_history (created_at DESC);
```

#### Match Chunks Remote Procedure Call (RPC)
The database search handler executing rapid cosine distance computations natively in PostgreSQL.
```sql
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.4,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id          INT,
    doc_id      VARCHAR(100),
    doc_title   TEXT,
    chunk_index INT,
    content     TEXT,
    metadata    JSONB,
    similarity  FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.doc_id,
        document_chunks.doc_title,
        document_chunks.chunk_index,
        document_chunks.content,
        document_chunks.metadata,
        (1 - (document_chunks.embedding <=> query_embedding))::FLOAT AS similarity
    FROM document_chunks
    WHERE document_chunks.embedding IS NOT NULL
      AND (1 - (document_chunks.embedding <=> query_embedding)) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;
```

#### Row Level Security (RLS) Enforcement
```sql
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_history ENABLE ROW LEVEL SECURITY;

-- Attached public access policies
CREATE POLICY "Allow public read on document_chunks"
    ON document_chunks FOR SELECT USING (true);
CREATE POLICY "Allow public insert on document_chunks"
    ON document_chunks FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on document_chunks"
    ON document_chunks FOR UPDATE USING (true) WITH CHECK (true);
CREATE POLICY "Allow public delete on document_chunks"
    ON document_chunks FOR DELETE USING (true);

CREATE POLICY "Allow public read on session_history"
    ON session_history FOR SELECT USING (true);
CREATE POLICY "Allow public insert on session_history"
    ON session_history FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update on session_history"
    ON session_history FOR UPDATE USING (true) WITH CHECK (true);
CREATE POLICY "Allow public delete on session_history"
    ON session_history FOR DELETE USING (true);
```

---

## 2. SYSTEM VECTOR SEEDING PIPELINE

The production database is hydrated through a highly parallelized automated data streaming pipeline orchestrated by `backend/setup_db.py`. 

### Background Seeding Engine Operations
1. **Source Processing**: The engine reads the source legal files and legal dictionaries pre-configured in the ingestion map.
2. **Layout Fragmentation**: It processes paragraph-level layout chunks using a local chunking module (`DocumentChunker`), ensuring legal context remains cohesive across boundaries.
3. **Async Vector Generation**: The script invokes the async-wrapped `google-genai` SDK (`gemini-embedding-2` / `text-embedding-004`) to generate precise 768-dimensional float embedding matrices.
4. **Remote Commit**: Bypassing error-prone manual DB connections, the orchestrator streams and commits the structural payloads directly to the remote Supabase PostgreSQL cluster using robust PostgREST API calls.
