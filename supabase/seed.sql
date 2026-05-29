-- ============================================================
-- BRAHMO Citation Safety Engine — Seed Data
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
-- IPC (Indian Penal Code, 1860) → BNS (Bharatiya Nyaya Sanhita, 2023)
-- CrPC (Code of Criminal Procedure, 1973) → BNSS (Bharatiya Nagarik Suraksha Sanhita, 2023)
-- IEA (Indian Evidence Act, 1872) → BSA (Bharatiya Sakshya Adhiniyam, 2023)
-- Effective: July 1, 2024
-- ============================================================

-- IPC → BNS (21 mappings)
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

-- CrPC → BNSS (8 mappings)
INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
('125',    '144',    'CrPC', 'BNSS'),
('154',    '173',    'CrPC', 'BNSS'),
('156(3)', '175(3)', 'CrPC', 'BNSS'),
('167',    '187',    'CrPC', 'BNSS'),
('437',    '480',    'CrPC', 'BNSS'),
('438',    '482',    'CrPC', 'BNSS'),
('439',    '483',    'CrPC', 'BNSS'),
('482',    '528',    'CrPC', 'BNSS');

-- IEA → BSA (1 mapping)
INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
('65B',    '63',     'IEA',  'BSA');

-- ============================================================
-- VERIFICATION: Run these queries to confirm seed data
-- ============================================================
-- SELECT COUNT(*) FROM citation_patterns;    -- Expected: 6
-- SELECT COUNT(*) FROM section_mappings;     -- Expected: 30
-- SELECT * FROM citation_patterns ORDER BY id;
-- SELECT * FROM section_mappings ORDER BY old_act, old_section;
