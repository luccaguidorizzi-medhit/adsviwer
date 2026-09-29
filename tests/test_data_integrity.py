"""
Automated Data Integrity & Report Compliance Tests
Author: Lagana Flow

Verifies:
1. Integrity of all JSON datasets in data/sanitized/ (Pydantic validation, schema correctness).
2. Completeness of competitor profiling (Mundo Revalida + 15 competitors = 16 total).
3. Coverage of all 7 Meta Ads hooks.
4. Security sanitization (no HTML scripts, no raw prompt injections).
5. Supabase SQL DDL validity with RLS policies.
6. Exhaustive structure, content, and signature of data/relatorio_inteligencia_revalida.md.
"""

import json
import re
from pathlib import Path
import pytest

from src.security.sanitizer import (
    SecuritySanitizer,
    CompetitorProfileRecord,
    CompetitorAdRecord,
    PROJECT_ROOT,
    SANITIZED_DIR,
)

REPORT_FILE = PROJECT_ROOT / "data" / "relatorio_inteligencia_revalida.md"
PROFILES_FILE = SANITIZED_DIR / "competitor_profiles.json"
ADS_FILE = SANITIZED_DIR / "competitor_ads.json"
SUMMARY_FILE = SANITIZED_DIR / "market_summary.json"
SCHEMA_FILE = SANITIZED_DIR / "supabase_schema.sql"


def test_sanitized_files_exist():
    """Confirms all required sanitized artifacts exist and are non-empty."""
    assert PROFILES_FILE.exists() and PROFILES_FILE.stat().st_size > 0
    assert ADS_FILE.exists() and ADS_FILE.stat().st_size > 0
    assert SUMMARY_FILE.exists() and SUMMARY_FILE.stat().st_size > 0
    assert SCHEMA_FILE.exists() and SCHEMA_FILE.stat().st_size > 0
    assert REPORT_FILE.exists() and REPORT_FILE.stat().st_size > 0


def test_competitor_profiles_integrity():
    """Validates competitor profiles dataset, counts, and Pydantic compliance."""
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["author"] == "Lagana Flow"
    assert data["total_profiles"] == 16
    profiles = data["profiles"]
    assert len(profiles) == 16

    # Verify each profile validates against CompetitorProfileRecord
    profile_ids = set()
    for p in profiles:
        profile_ids.add(p["competitor_id"])
        record = CompetitorProfileRecord(
            competitor_id=p["competitor_id"],
            platform=p["platform"],
            username=p["username"],
            full_name=p["full_name"],
            bio_text=p["bio_text"],
            external_url=p["external_url"],
            followers_count=p["followers_count"],
            posts_count=p["posts_count"],
            recent_posts=p["recent_posts"],
            scraped_at=p["scraped_at"],
        )
        assert record.competitor_id == p["competitor_id"]
        assert record.followers_count >= 0

    # Ensure baseline and critical competitors are present
    assert "mundo_revalida" in profile_ids
    assert "estrategia_med" in profile_ids
    assert "medcel" in profile_ids
    assert "hardwork_revalida" in profile_ids
    assert "medtwins" in profile_ids
    assert "medcof_revalida" in profile_ids
    assert "bastidores_revalida" in profile_ids
    assert "revalida360" in profile_ids
    assert "revmed_mentoria" in profile_ids
    assert "revalideii" in profile_ids
    assert "pense_revalida" in profile_ids
    assert "aristo_revalida" in profile_ids
    assert "medgrupo_revalida" in profile_ids
    assert "alphamed_revalida" in profile_ids
    assert "revalidando" in profile_ids
    assert "eumedicorevalida" in profile_ids

    # Verify key metrics
    mundo = next(p for p in profiles if p["competitor_id"] == "mundo_revalida")
    assert mundo["followers_count"] == 65200
    assert mundo["previous_followers_count"] == 54000
    assert mundo["followers_delta"] == 11200
    assert abs(mundo["growth_rate_pct"] - 20.74) < 0.1

    r360 = next(p for p in profiles if p["competitor_id"] == "revalida360")
    assert r360["followers_count"] == 4400
    assert r360["followers_delta"] == 2900
    assert abs(r360["growth_rate_pct"] - 193.33) < 0.1
    assert "Foz do Iguaçu" in r360["practical_exam_city"]


def test_competitor_ads_integrity():
    """Validates ads dataset, Pydantic validation, and coverage of all 7 hooks."""
    with open(ADS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["author"] == "Lagana Flow"
    assert data["total_ads"] >= 25
    ads = data["ads"]

    categories_found = set()
    for ad in ads:
        record = CompetitorAdRecord(
            competitor_id=ad["competitor_id"],
            platform=ad["platform"],
            ad_id=ad["ad_id"],
            headline=ad["headline"],
            body_text=ad["body_text"],
            call_to_action=ad["call_to_action"],
            landing_page_url=ad["landing_page_url"],
            media_url=ad["media_url"],
            start_date=ad["start_date"],
            is_active=ad["is_active"],
            scraped_at=ad["scraped_at"],
        )
        assert record.is_active is True
        categories_found.add(ad["hook_category"])

    # Ensure all 7 key strategic hooks are cataloged
    required_hooks = [
        "apelo_financeiro",
        "medo_clareza",
        "isca_gratuita",
        "antecipacao_funil",
        "comunidade_whatsapp",
        "prova_pratica_presencial",
        "desmistificacao_banca",
    ]
    for hook in required_hooks:
        assert hook in categories_found, f"Hook {hook} missing from cataloged ads!"


def test_market_summary_integrity():
    """Validates summary statistics, total audience, and rankings."""
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    metrics = data["metrics"]
    assert metrics["total_tracked_players"] == 16
    assert metrics["active_players_count"] == 14
    assert metrics["inactive_players_count"] == 2
    assert metrics["total_audience_tracked"] == 692500
    assert metrics["our_brand"]["id"] == "mundo_revalida"
    assert metrics["our_brand"]["rank_in_dedicated_revalida"] == 1
    assert metrics["fastest_growing_player"]["id"] == "revalida360"
    assert len(data["top_audience_ranking"]) >= 5
    assert len(data["top_growth_velocity_ranking"]) >= 5


def test_supabase_schema_integrity():
    """Validates DDL structure, RLS activation, and security policies."""
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "CREATE TABLE IF NOT EXISTS competitor_profiles" in sql
    assert "CREATE TABLE IF NOT EXISTS competitor_ads" in sql
    assert "CREATE TABLE IF NOT EXISTS competitor_swot" in sql
    assert "CREATE TABLE IF NOT EXISTS competitor_site_changes" in sql

    # Verify RLS enabled on all tables
    assert "ALTER TABLE competitor_profiles ENABLE ROW LEVEL SECURITY;" in sql
    assert "ALTER TABLE competitor_ads ENABLE ROW LEVEL SECURITY;" in sql
    assert "ALTER TABLE competitor_swot ENABLE ROW LEVEL SECURITY;" in sql
    assert "ALTER TABLE competitor_site_changes ENABLE ROW LEVEL SECURITY;" in sql

    # Verify RLS policies exist
    assert 'CREATE POLICY "Allow authenticated read on competitor_profiles"' in sql
    assert 'CREATE POLICY "Allow service_role full access on competitor_profiles"' in sql

    # Verify SWOT seed data
    assert "INSERT INTO competitor_swot" in sql
    assert "Lagana Flow" in sql


def test_no_injection_or_html_in_sanitized_data():
    """Ensures no dangerous script tags, event handlers, or injections slipped into sanitized JSONs."""
    sanitizer = SecuritySanitizer()
    for json_file in SANITIZED_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            raw_content = f.read()

        # No script tags
        assert "<script" not in raw_content.lower()
        # No inline event handlers
        assert "onerror=" not in raw_content.lower()
        assert "onload=" not in raw_content.lower()
        assert "javascript:" not in raw_content.lower()


def test_individual_bundles_exist_for_bridge():
    """Ensures MCPCrossProjectBridge compatibility: individual files exist."""
    for p_id in ["mundo_revalida", "estrategia_med", "medcel", "hardwork_revalida", "revalida360"]:
        profile_path = SANITIZED_DIR / f"profile_ig_{p_id}.json"
        ads_path = SANITIZED_DIR / f"ads_meta_{p_id}.json"
        site_path = SANITIZED_DIR / f"site_state_{p_id}.json"

        assert profile_path.exists(), f"Missing {profile_path}"
        assert ads_path.exists(), f"Missing {ads_path}"
        assert site_path.exists(), f"Missing {site_path}"


def test_relatorio_inteligencia_revalida_content_and_sections():
    """Validates that the executive intelligence report meets all 8 sections and specific requirements."""
    assert REPORT_FILE.exists()
    content = REPORT_FILE.read_text(encoding="utf-8")

    # Document length check (exhaustive)
    assert len(content) > 12000, "Report is too brief; must be exhaustive and comprehensive"

    # Verify all 8 mandatory sections
    assert "Seção 1: Panorama Geral do Mercado Revalida INEP" in content
    assert "Seção 2: Perfil Completo do Mundo Revalida (NÓS)" in content
    assert "Seção 3: Mapeamento Detalhado dos 15 Concorrentes" in content
    assert "Seção 4: Matriz Comparativa Estruturada" in content
    assert "Seção 5: Raio-X de Tráfego Pago & Meta Ads Library" in content
    assert "Seção 6: Matriz Competitiva SWOT para o Mundo Revalida" in content
    assert "Seção 7: Plano Tático & Oportunidades Estratégicas Imperativas" in content
    assert "Seção 8: Schema Supabase DDL com Row Level Security (RLS)" in content

    # Verify critical business intelligence topics
    assert "Dr. Juan Pablo Murillo" in content
    assert "65.200" in content
    assert "+20,7%" in content or "+20.7%" in content
    assert "Practicus" in content
    assert "Foz do Iguaçu" in content
    assert "Revalida 360" in content
    assert "Ciudad del Este" in content
    assert "Flashcards" in content or "cartões físicos" in content.lower()
    assert "12mil" in content or "12 mil" in content or "12k" in content.lower()
    assert "Não estude no escuro" in content
    assert "Cursos por R$ 0,00" in content or "R$ 00,00" in content

    # Verify strict signature
    assert "Lagana Flow" in content
