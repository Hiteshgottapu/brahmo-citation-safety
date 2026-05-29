DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS section_mappings CASCADE;
DROP TABLE IF EXISTS citation_patterns CASCADE;

-- Confirm table columns are mapped to the text-embedding-004 footprint
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'document_chunks';

-- ================================================
-- COMBINED SETUP: Run this entire block in Supabase SQL Editor
-- ================================================

-- ============================================================
-- BRAHMO Citation Safety Engine â€” Database Schema
-- ============================================================
-- Run this in Supabase SQL Editor BEFORE seed.sql
-- ============================================================

-- 1. Citation Patterns: 6 Indian legal citation regex configs
-- Loaded at runtime by the citation extractor engine
CREATE TABLE IF NOT EXISTS citation_patterns (
    id              SERIAL PRIMARY KEY,
    pattern_name    VARCHAR(50)  NOT NULL,
    regex_pattern   TEXT         NOT NULL,
    format_template TEXT,
    jurisdiction    VARCHAR(50)  DEFAULT 'IN',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_citation_patterns_name
    ON citation_patterns (pattern_name);

-- 2. Section Mappings: IPC â†’ BNS, CrPC â†’ BNSS, IEA â†’ BSA
-- 30 statutory transformation rows loaded into hash map at startup
CREATE TABLE IF NOT EXISTS section_mappings (
    id              SERIAL PRIMARY KEY,
    old_section     VARCHAR(50)  NOT NULL,   -- e.g. "302", "304A", "120B", "156(3)", "65B"
    new_section     VARCHAR(50)  NOT NULL,   -- e.g. "101", "105", "61",   "175(3)", "63"
    old_act         VARCHAR(100) NOT NULL,   -- e.g. "IPC", "CrPC", "IEA"
    new_act         VARCHAR(100) NOT NULL,   -- e.g. "BNS", "BNSS", "BSA"
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_section_mappings_composite
    ON section_mappings (old_section, old_act);

-- Enable Row Level Security (Supabase best practice)
ALTER TABLE citation_patterns  ENABLE ROW LEVEL SECURITY;
ALTER TABLE section_mappings   ENABLE ROW LEVEL SECURITY;

-- Allow public read for all tables (anon key access)
CREATE POLICY "Allow public read on citation_patterns"
    ON citation_patterns FOR SELECT
    USING (true);

CREATE POLICY "Allow public read on section_mappings"
    ON section_mappings FOR SELECT
    USING (true);

-- ================================================
-- SEED DATA
-- ================================================

-- ============================================================
-- BRAHMO Citation Safety Engine â€” Seed Data
-- ============================================================
-- Run this in Supabase SQL Editor AFTER schema.sql
-- Uses E'' syntax for regex backslash escaping
-- ============================================================

-- ============================================================
-- 1. CITATION PATTERNS (6 Indian Legal Citation Formats)
-- ============================================================

INSERT INTO citation_patterns (pattern_name, regex_pattern, format_template, jurisdiction) VALUES
(
    'SCC',
    E'\\((\\d{4})\\)\\s+(\\d{1,2})\\s+SCC\\s+(\\d{1,5})',
    '({year}) {volume} SCC {page}',
    'IN'
),
(
    'SCC_OnLine',
    E'(\\d{4})\\s+SCC\\s+OnLine\\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj)\\s+(\\d{1,6})',
    '{year} SCC OnLine {court} {number}',
    'IN'
),
(
    'AIR',
    E'AIR\\s+(\\d{4})\\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj|NOC)\\s+(\\d{1,5})',
    'AIR {year} {court} {page}',
    'IN'
),
(
    'Cri_LJ',
    E'[\\(]?(\\d{4})[\\)]?\\s+Cri\\s+LJ\\s+(\\d{1,5})',
    '{year} Cri LJ {page}',
    'IN'
),
(
    'SCR',
    E'\\((\\d{4})\\)\\s+(\\d{1,2})\\s+SCR\\s+(\\d{1,5})',
    '({year}) {volume} SCR {page}',
    'IN'
),
(
    'MANU',
    E'MANU/(SC|DE|MH|KA|KE|WB|TN|AP|GJ|RJ|MP|UP)/(\\d{4})/(\\d{4,6})',
    'MANU/{court}/{year}/{number}',
    'IN'
);

-- ============================================================
-- 2. SECTION MAPPINGS (30 Post-2024 Statutory Transformations)
-- ============================================================
-- IPC (Indian Penal Code, 1860) â†’ BNS (Bharatiya Nyaya Sanhita, 2023)
-- CrPC (Code of Criminal Procedure, 1973) â†’ BNSS (Bharatiya Nagarik Suraksha Sanhita, 2023)
-- IEA (Indian Evidence Act, 1872) â†’ BSA (Bharatiya Sakshya Adhiniyam, 2023)
-- Effective: July 1, 2024
-- ============================================================

-- IPC â†’ BNS (21 mappings)
INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
('302',    '101',    'IPC',  'BNS'),
('304',    '105',    'IPC',  'BNS'),
('304A',   '106',    'IPC',  'BNS'),
('304B',   '80',     'IPC',  'BNS'),
('306',    '108',    'IPC',  'BNS'),
('307',    '109',    'IPC',  'BNS'),
('323',    '115',    'IPC',  'BNS'),
('326',    '119',    'IPC',  'BNS'),
('354',    '74',     'IPC',  'BNS'),
('376',    '63',     'IPC',  'BNS'),
('379',    '303',    'IPC',  'BNS'),
('384',    '308',    'IPC',  'BNS'),
('392',    '309',    'IPC',  'BNS'),
('406',    '316',    'IPC',  'BNS'),
('420',    '318',    'IPC',  'BNS'),
('467',    '336',    'IPC',  'BNS'),
('498A',   '85',     'IPC',  'BNS'),
('499',    '356',    'IPC',  'BNS'),
('506',    '351',    'IPC',  'BNS'),
('34',     '3(5)',   'IPC',  'BNS'),
('120B',   '61',     'IPC',  'BNS');

-- CrPC â†’ BNSS (8 mappings)
INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
('125',    '144',    'CrPC', 'BNSS'),
('154',    '173',    'CrPC', 'BNSS'),
('156(3)', '175(3)', 'CrPC', 'BNSS'),
('167',    '187',    'CrPC', 'BNSS'),
('437',    '480',    'CrPC', 'BNSS'),
('438',    '482',    'CrPC', 'BNSS'),
('439',    '483',    'CrPC', 'BNSS'),
('482',    '528',    'CrPC', 'BNSS');

-- IEA â†’ BSA (1 mapping)
INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
('65B',    '63',     'IEA',  'BSA');

-- ============================================================
-- VERIFICATION: Run these queries to confirm seed data
-- ============================================================
-- SELECT COUNT(*) FROM citation_patterns;    -- Expected: 6
-- SELECT COUNT(*) FROM section_mappings;     -- Expected: 30
-- SELECT * FROM citation_patterns ORDER BY id;
-- SELECT * FROM section_mappings ORDER BY old_act, old_section;


-- ================================================
-- RAG PIPELINE (pgvector)
-- ================================================

-- ============================================================
-- BRAHMO Citation Safety Engine â€” RAG Pipeline Schema Migration
-- ============================================================
-- Run this in Supabase SQL Editor AFTER schema.sql + seed.sql
-- Uses text-embedding-004 â†’ 768-dimensional vectors
-- ============================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

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


-- ============================================================
-- 5. Session History Telemetry Table
-- ============================================================
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

-- Index for chronological fetching
CREATE INDEX IF NOT EXISTS idx_session_history_created_at
    ON session_history (created_at DESC);

-- RLS Policies
ALTER TABLE session_history ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'session_history' AND policyname = 'Allow public read on session_history'
    ) THEN
        CREATE POLICY "Allow public read on session_history"
            ON session_history FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'session_history' AND policyname = 'Allow public insert on session_history'
    ) THEN
        CREATE POLICY "Allow public insert on session_history"
            ON session_history FOR INSERT WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'session_history' AND policyname = 'Allow public update on session_history'
    ) THEN
        CREATE POLICY "Allow public update on session_history"
            ON session_history FOR UPDATE USING (true) WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'session_history' AND policyname = 'Allow public delete on session_history'
    ) THEN
        CREATE POLICY "Allow public delete on session_history"
            ON session_history FOR DELETE USING (true);
    END IF;
END$$;

