-- =====================================================================
-- SUPABASE RELATIONAL SCHEMA & RLS FOR REVALIDA COMPETITOR INTELLIGENCE
-- Project: competitor-monitor (Milestone 1)
-- Author: Lagana Flow
-- Database Target: Supabase (Project mundorevalida-leads / medhit-intelligence)
-- =====================================================================

-- 1. EXTENSIONS & RESET
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. TABLE: competitor_profiles
CREATE TABLE IF NOT EXISTS competitor_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'baseline_reference', 'inactive_2025')),
    tier TEXT NOT NULL,
    instagram_username TEXT,
    followers_count INTEGER NOT NULL DEFAULT 0,
    previous_followers_count INTEGER NOT NULL DEFAULT 0,
    followers_delta INTEGER GENERATED ALWAYS AS (followers_count - previous_followers_count) STORED,
    growth_rate_pct NUMERIC(6, 2) DEFAULT 0.0,
    youtube_url TEXT,
    website_url TEXT,
    focus_summary TEXT,
    practical_exam_city TEXT DEFAULT 'Online',
    pricing_range TEXT,
    media_spend_tier TEXT,
    has_first_phase BOOLEAN DEFAULT TRUE,
    has_second_phase_practical BOOLEAN DEFAULT TRUE,
    has_flashcards_physical BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. TABLE: competitor_ads
CREATE TABLE IF NOT EXISTS competitor_ads (
    id TEXT PRIMARY KEY,
    competitor_id TEXT NOT NULL REFERENCES competitor_profiles(id) ON DELETE CASCADE,
    platform TEXT NOT NULL DEFAULT 'meta' CHECK (platform IN ('meta', 'google', 'tiktok', 'youtube')),
    headline TEXT NOT NULL,
    body_text TEXT,
    call_to_action TEXT,
    hook_category TEXT NOT NULL CHECK (hook_category IN (
        'apelo_financeiro',
        'medo_clareza',
        'isca_gratuita',
        'antecipacao_funil',
        'comunidade_whatsapp',
        'prova_pratica_presencial',
        'desmistificacao_banca',
        'prova_social_depoimento',
        'outro'
    )),
    creative_format TEXT NOT NULL DEFAULT 'estatico' CHECK (creative_format IN ('reels_video', 'estatico', 'carrossel')),
    landing_page_url TEXT,
    media_url TEXT,
    spend_tier TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. TABLE: competitor_swot
CREATE TABLE IF NOT EXISTS competitor_swot (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL CHECK (category IN ('strength', 'weakness', 'opportunity', 'threat')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    strategic_impact TEXT NOT NULL CHECK (strategic_impact IN ('critical', 'high', 'medium', 'low')),
    target_competitor_id TEXT REFERENCES competitor_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_swot_category_title UNIQUE (category, title)
);

-- 5. TABLE: competitor_site_changes
CREATE TABLE IF NOT EXISTS competitor_site_changes (
    id BIGSERIAL PRIMARY KEY,
    competitor_id TEXT NOT NULL REFERENCES competitor_profiles(id) ON DELETE CASCADE,
    target_url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    has_changed BOOLEAN NOT NULL DEFAULT FALSE,
    change_snippet TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. PERFORMANCE INDEXES
CREATE INDEX IF NOT EXISTS idx_competitor_profiles_status ON competitor_profiles(status);
CREATE INDEX IF NOT EXISTS idx_competitor_profiles_tier ON competitor_profiles(tier);
CREATE INDEX IF NOT EXISTS idx_competitor_ads_competitor ON competitor_ads(competitor_id);
CREATE INDEX IF NOT EXISTS idx_competitor_ads_hook ON competitor_ads(hook_category);
CREATE INDEX IF NOT EXISTS idx_competitor_swot_category ON competitor_swot(category);

-- 7. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE competitor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_ads ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_swot ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_site_changes ENABLE ROW LEVEL SECURITY;

-- Read policy: Authenticated users can read all competitor intelligence
DROP POLICY IF EXISTS "Allow authenticated read on competitor_profiles" ON competitor_profiles;
CREATE POLICY "Allow authenticated read on competitor_profiles"
    ON competitor_profiles FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Allow authenticated read on competitor_ads" ON competitor_ads;
CREATE POLICY "Allow authenticated read on competitor_ads"
    ON competitor_ads FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Allow authenticated read on competitor_swot" ON competitor_swot;
CREATE POLICY "Allow authenticated read on competitor_swot"
    ON competitor_swot FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Allow authenticated read on competitor_site_changes" ON competitor_site_changes;
CREATE POLICY "Allow authenticated read on competitor_site_changes"
    ON competitor_site_changes FOR SELECT TO authenticated USING (true);

-- Write policies: Only service_role can mutate intelligence data
DROP POLICY IF EXISTS "Allow service_role full access on competitor_profiles" ON competitor_profiles;
CREATE POLICY "Allow service_role full access on competitor_profiles"
    ON competitor_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service_role full access on competitor_ads" ON competitor_ads;
CREATE POLICY "Allow service_role full access on competitor_ads"
    ON competitor_ads FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service_role full access on competitor_swot" ON competitor_swot;
CREATE POLICY "Allow service_role full access on competitor_swot"
    ON competitor_swot FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow service_role full access on competitor_site_changes" ON competitor_site_changes;
CREATE POLICY "Allow service_role full access on competitor_site_changes"
    ON competitor_site_changes FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 8. INITIAL SEED DATA: SWOT MATRIX PARA O MUNDO REVALIDA
INSERT INTO competitor_swot (category, title, description, strategic_impact) VALUES
('strength', 'Liderança Digital Vertical', 'Maior perfil de Instagram do Brasil 100% focado no Revalida INEP com 65.2k seguidores e crescimento de +20.7%.', 'critical'),
('strength', 'Autoridade Médica Empática', 'Corpo docente liderado pelo Dr. Juan Pablo Murillo, médico revalidado no Brasil pelo INEP em 2020.', 'critical'),
('strength', 'Metodologia Practicus Consagrada', 'Esteira completa de 1ª fase teórica e imersão prática de 2ª fase com atores e estações realísticas.', 'high'),
('weakness', 'Concentração Geográfica em São Paulo', 'Turmas presenciais do Practicus exclusivamente na capital paulista, encarecendo deslocamento de alunos.', 'high'),
('weakness', 'Gap de Presença na Fronteira (Foz do Iguaçu)', 'Ausência de base fixa na fronteira com Paraguai e Argentina, onde milhares de alunos se formam anualmente.', 'critical'),
('weakness', 'Ausência de Flashcards Físicos', 'Falta de materiais impressos de apoio (como os cartões do Revalideii) para estudo tátil e alívio de telas.', 'medium'),
('opportunity', 'Expansão do Practicus para Foz do Iguaçu', 'Criação de turmas satélite do Practicus na tríplice fronteira para neutralizar o crescimento do Revalida 360 (+193%).', 'critical'),
('opportunity', 'Testes com Ganchos Financeiros', 'Incorporação de copies abordando retorno salarial médico (R$ 12k+ a R$ 20k) no pós-revalidação com foco ético.', 'high'),
('opportunity', 'Funil Antecipado de 24 Meses', 'Captação de alunos no internato médico de faculdades do Paraguai e Bolívia (preparação 2026/2027).', 'high'),
('threat', 'Agressividade Freemium Corporativa', 'Campanhas massivas da Medcel oferecendo cursos por R$ 0,00 para alimentar telemarketing ativo.', 'high'),
('threat', 'Retenção Hiperlocal por Concorrentes de Fronteira', 'Revalida 360 e Revmed capturando alunos recém-formados em Ciudad del Este antes do retorno ao Brasil.', 'critical')
ON CONFLICT (category, title) DO NOTHING;
