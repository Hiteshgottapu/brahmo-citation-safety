-- ============================================================
-- BRAHMO Citation Safety Engine — Database Schema
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

-- 2. Section Mappings: IPC → BNS, CrPC → BNSS, IEA → BSA
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


