
-- ============================================================
-- BRAHMO Citation Safety Engine — RAG Pipeline Schema Migration
-- ============================================================
-- Run this in Supabase SQL Editor AFTER schema.sql + seed.sql
-- Uses text-embedding-004 → 768-dimensional vectors
-- ============================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS document_chunks CASCADE;
DROP FUNCTION IF EXISTS match_chunks;

-- 2. Document chunks with 768-dimensional embeddings (text-embedding-004)
CREATE TABLE IF NOT EXISTS document_chunks (
    id              SERIAL PRIMARY KEY,
    doc_id          VARCHAR(100)  NOT NULL,       -- e.g. "anticipatory_bail_sc"
    doc_title       TEXT          NOT NULL,        -- e.g. "SC Precedents on Anticipatory Bail"
    chunk_index     INT           NOT NULL,        -- position within document
    content         TEXT          NOT NULL,        -- raw chunk text
    metadata        JSONB         DEFAULT '{}',    -- section_title, act_name, topic, etc.
    embedding       VECTOR(768),                   -- text-embedding-004 output
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id
    ON document_chunks (doc_id);

-- Note: IVFFlat index requires at least (lists * 10) rows to build.
-- For small datasets (<200 rows), we skip it and rely on exact search.
-- Uncomment this after ingesting a larger knowledge base:
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
--     ON document_chunks USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 20);

-- 3. RPC function for cosine similarity search
-- Uses cosine distance operator <=> and returns 1 - distance as similarity
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

-- 4. RLS policies for document_chunks
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'document_chunks' AND policyname = 'Allow public read on document_chunks'
    ) THEN
        CREATE POLICY "Allow public read on document_chunks"
            ON document_chunks FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'document_chunks' AND policyname = 'Allow public insert on document_chunks'
    ) THEN
        CREATE POLICY "Allow public insert on document_chunks"
            ON document_chunks FOR INSERT WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'document_chunks' AND policyname = 'Allow public update on document_chunks'
    ) THEN
        CREATE POLICY "Allow public update on document_chunks"
            ON document_chunks FOR UPDATE USING (true) WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'document_chunks' AND policyname = 'Allow public delete on document_chunks'
    ) THEN
        CREATE POLICY "Allow public delete on document_chunks"
            ON document_chunks FOR DELETE USING (true);
    END IF;
END$$;
