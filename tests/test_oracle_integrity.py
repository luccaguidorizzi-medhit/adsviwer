"""
Independent Oracle & Adversarial Data Integrity Verification Test Suite
Author: Lagana Flow
Role: Challenger 1 (EMPIRICAL CHALLENGER / teamwork_preview_challenger)

This suite performs 100% independent verification of data integrity:
1. Independent raw document parsing without relying on pipeline internals.
2. Differential comparison between data/raw/concorrentes_doc.txt and data/sanitized/ JSONs.
3. Strict mathematical validation of follower deltas, percentage growth, market totals, and rankings.
4. Formal verification of Tier categorization and Meta Ads hook classification.
5. Adversarial edge-case and boundary stress-testing.
"""

import re
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DOC_FILE = PROJECT_ROOT / "data" / "raw" / "concorrentes_doc.txt"
CONFIG_FILE = PROJECT_ROOT / "config" / "competitors.json"
PROFILES_FILE = PROJECT_ROOT / "data" / "sanitized" / "competitor_profiles.json"
ADS_FILE = PROJECT_ROOT / "data" / "sanitized" / "competitor_ads.json"
SUMMARY_FILE = PROJECT_ROOT / "data" / "sanitized" / "market_summary.json"


def parse_raw_follower_string(val_str: str) -> int:
    """Independent helper to parse follower string with 'k', 'K', comma, or dot."""
    cleaned = val_str.strip().replace(" ", "").lower().replace(",", ".")
    if "k" in cleaned:
        num_part = cleaned.replace("k", "")
        return int(Decimal(num_part) * Decimal(1000))
    return int(Decimal(cleaned))


def independent_parse_raw_document(filepath: Path):
    """
    Independent parser for data/raw/concorrentes_doc.txt.
    Extracts all competitor blocks, their previous and current followers,
    reels topics, static topics, and paid traffic lines.
    Handles UTF-8 BOM safely using utf-8-sig.
    """
    content = filepath.read_text(encoding="utf-8-sig")
    lines = content.splitlines()

    # Canonical competitor signatures in doc
    known_signatures = [
        ("mundo_revalida", "Mundo Revalida"),
        ("hardwork_revalida", "Hardwork Revalida"),
        ("estrategia_med", "Estratégiamed"),
        ("medtwins", "Medtwins"),
        ("medcel", "Medcel"),
        ("medgrupo_revalida", "Medgrupo Revalida"),
        ("aristo_revalida", "Aristo Revalida"),
        ("medcof_revalida", "Medcof Revalida"),
        ("bastidores_revalida", "Bastidores do Revalida"),
        ("revalidando", "Revalidando"),
        ("revalideii", "Revalideii"),
        ("revalida360", "Revalida360"),
        ("eumedicorevalida", "Eumedicorevalida"),
        ("alphamed_revalida", "Alphamed Revalida"),
        ("pense_revalida", "Pense Revalida"),
        ("revmed_mentoria", "Revmed mentoria"),
    ]

    extracted = {}
    current_key = None
    current_section = None

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        # Detect player start
        matched_key = None
        for key, name in known_signatures:
            # Check prefix or line match
            pattern = rf"^\s*{re.escape(name)}\s*:\s*Seguidores\s+([\d\.,]+[kK]?)"
            m = re.match(pattern, line_s, re.IGNORECASE)
            if m:
                matched_key = key
                f_val = parse_raw_follower_string(m.group(1))
                if key not in extracted:
                    extracted[key] = {
                        "canonical_name": name,
                        "follower_records": [],
                        "reels": [],
                        "statics": [],
                        "ads": [],
                        "other_notes": []
                    }
                extracted[key]["follower_records"].append(f_val)
                current_key = key
                current_section = None
                break

        if matched_key:
            continue

        if current_key:
            low = line_s.lower()
            if "últimos 3 reels" in low or "social media" in low:
                current_section = "reels"
                continue
            elif "últimos estático" in low or "último estático" in low:
                current_section = "statics"
                continue
            elif "tráfego pago" in low:
                current_section = "ads"
                continue
            elif "abril 2026" in low:
                continue
            elif "último post 2025" in low:
                extracted[current_key]["other_notes"].append("inativo_2025")
                continue

            cleaned_item = line_s.lstrip("*-• \"'").rstrip("\"'")
            if not cleaned_item:
                continue

            if current_section == "reels":
                extracted[current_key]["reels"].append(cleaned_item)
            elif current_section == "statics":
                extracted[current_key]["statics"].append(cleaned_item)
            elif current_section == "ads":
                extracted[current_key]["ads"].append(cleaned_item)
            else:
                extracted[current_key]["other_notes"].append(cleaned_item)

    return extracted


def test_oracle_raw_document_extraction():
    """
    EMPIRICAL ORACLE: Asserts that all 16 competitors exist in raw document,
    each has exactly 2 follower snapshots, and parses without loss.
    """
    raw_data = independent_parse_raw_document(RAW_DOC_FILE)
    assert len(raw_data) == 16, f"Expected 16 competitors in raw doc, found {len(raw_data)}"

    for comp_id, d in raw_data.items():
        assert len(d["follower_records"]) == 2, (
            f"Competitor {comp_id} has {len(d['follower_records'])} follower snapshots, expected 2"
        )
        prev_f, curr_f = d["follower_records"]
        assert prev_f > 0, f"{comp_id} prev_f must be > 0"
        assert curr_f > 0, f"{comp_id} curr_f must be > 0"


def test_oracle_differential_raw_vs_sanitized_profiles():
    """
    EMPIRICAL ORACLE: Compares raw extracted numbers directly against
    data/sanitized/competitor_profiles.json. No discrepancy allowed.
    """
    raw_data = independent_parse_raw_document(RAW_DOC_FILE)

    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_json = json.load(f)

    sanitized_map = {p["competitor_id"]: p for p in profiles_json["profiles"]}
    assert len(sanitized_map) == 16, f"Expected 16 sanitized profiles, found {len(sanitized_map)}"

    # Ensure 100% intersection of keys
    assert set(raw_data.keys()) == set(sanitized_map.keys())

    for comp_id, raw_p in raw_data.items():
        san_p = sanitized_map[comp_id]
        raw_prev, raw_curr = raw_p["follower_records"]

        # Exact number checks
        assert san_p["previous_followers_count"] == raw_prev, (
            f"Discrepancy for {comp_id}: raw prev {raw_prev} != sanitized {san_p['previous_followers_count']}"
        )
        assert san_p["followers_count"] == raw_curr, (
            f"Discrepancy for {comp_id}: raw curr {raw_curr} != sanitized {san_p['followers_count']}"
        )


def test_oracle_mathematical_precision_of_growth():
    """
    EMPIRICAL ORACLE: Re-calculates growth delta and percentage with high-precision Decimal.
    Asserts mathematical exactness for all 16 competitors.
    """
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_json = json.load(f)

    for p in profiles_json["profiles"]:
        prev = p["previous_followers_count"]
        curr = p["followers_count"]

        # Expected delta
        expected_delta = curr - prev
        assert p["followers_delta"] == expected_delta, (
            f"Delta math error in {p['competitor_id']}: {curr} - {prev} = {expected_delta}, got {p['followers_delta']}"
        )

        # Expected growth percentage
        if prev > 0:
            raw_pct = (Decimal(expected_delta) / Decimal(prev)) * Decimal(100)
            expected_pct = float(raw_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        else:
            expected_pct = 0.0

        actual_pct = p["growth_rate_pct"]
        # Allow at most 0.01 delta due to standard float vs Decimal rounding
        assert abs(actual_pct - expected_pct) <= 0.01, (
            f"Growth rate math error in {p['competitor_id']}: expected {expected_pct}%, got {actual_pct}%"
        )


def test_oracle_market_summary_aggregations():
    """
    EMPIRICAL ORACLE: Validates market_summary.json aggregations from scratch.
    """
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)
    profiles = profiles_data["profiles"]

    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        summary_data = json.load(f)
    metrics = summary_data["metrics"]

    # 1. Total players
    assert metrics["total_tracked_players"] == len(profiles) == 16

    # 2. Active vs Inactive
    active_profiles = [p for p in profiles if p["status"] != "inactive_2025"]
    inactive_profiles = [p for p in profiles if p["status"] == "inactive_2025"]

    assert len(active_profiles) == metrics["active_players_count"] == 14
    assert len(inactive_profiles) == metrics["inactive_players_count"] == 2

    # 3. Sum of audience
    expected_total_audience = sum(p["followers_count"] for p in active_profiles)
    assert metrics["total_audience_tracked"] == expected_total_audience == 692500

    # 4. Sum of net growth
    expected_total_growth = sum(p["followers_delta"] for p in active_profiles)
    assert metrics["total_net_audience_growth"] == expected_total_growth == 188600

    # 5. Niche Market Share calculation for Mundo Revalida
    mundo = next(p for p in profiles if p["competitor_id"] == "mundo_revalida")
    # Niche audience = total active minus general residency giants (Estratégia MED 280k, Medcel 125k)
    niche_denominator = 692500 - 280000 - 125000  # 287500
    expected_market_share = round((mundo["followers_count"] / niche_denominator) * 100, 2)
    assert expected_market_share == 22.68
    assert metrics["our_brand"]["market_share_in_niche"] == 22.68

    # 6. Fastest growing player verification
    fastest_player = max(active_profiles, key=lambda x: x["growth_rate_pct"])
    assert fastest_player["competitor_id"] == "revalida360"
    assert fastest_player["growth_rate_pct"] == 193.33
    assert metrics["fastest_growing_player"]["id"] == "revalida360"


def test_oracle_tier_categorization_rules():
    """
    EMPIRICAL ORACLE: Asserts that Tier categorization strictly follows
    the 4-tier strategic structure defined in PROJECT.md and config/competitors.json.
    """
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)
    profiles = profiles_data["profiles"]

    expected_tiers = {
        "mundo_revalida": "Baseline de Referência / Líder Nicho",
        "estrategia_med": "Tier 1 - Líder Geral Multiprova",
        "medcel": "Tier 1 - Grande Player Corporativo",
        "hardwork_revalida": "Tier 1 - Grande Concorrente Especialista",
        "medgrupo_revalida": "Tier 1 - Tradicional de Mercado",
        "medtwins": "Tier 2 - Forte no Revalida",
        "bastidores_revalida": "Tier 2 - Especialista de Nicho",
        "medcof_revalida": "Tier 2 - Em Alta Crescimento",
        "aristo_revalida": "Tier 3 - Metodologia IA / Repetição",
        "pense_revalida": "Tier 3 - Prova Prática & Checklists",
        "revalideii": "Tier 3 - Escola da Prática & Materiais",
        "revmed_mentoria": "Tier 3 - Cursos Presenciais & Mentoria Fronteira",
        "revalida360": "Tier 4 - Hiperaceleração Presencial Foz",
        "alphamed_revalida": "Tier 4 - Presencial & Habilidades Clínicas",
        "revalidando": "Inativo / Abandonado",
        "eumedicorevalida": "Inativo / Abandonado",
    }

    for p in profiles:
        c_id = p["competitor_id"]
        assert c_id in expected_tiers, f"Unexpected competitor: {c_id}"
        assert p["tier"] == expected_tiers[c_id], (
            f"Tier mismatch for {c_id}: expected '{expected_tiers[c_id]}', got '{p['tier']}'"
        )


def test_oracle_ads_and_hooks_completeness_and_classification():
    """
    EMPIRICAL ORACLE: Validates that all ads in data/sanitized/competitor_ads.json
    accurately reflect raw doc notes and cover all 7 required hook categories.
    """
    with open(ADS_FILE, "r", encoding="utf-8") as f:
        ads_data = json.load(f)
    ads = ads_data["ads"]

    assert len(ads) == 29, f"Expected 29 ads, found {len(ads)}"

    # Required 7 hooks check
    required_7_hooks = {
        "apelo_financeiro",
        "medo_clareza",
        "isca_gratuita",
        "antecipacao_funil",
        "comunidade_whatsapp",
        "prova_pratica_presencial",
        "desmistificacao_banca",
    }

    found_hooks = set(ad["hook_category"] for ad in ads)
    missing = required_7_hooks - found_hooks
    assert not missing, f"Missing required hooks: {missing}"

    # Verify specific key hook mappings
    # 1. Apelo Financeiro: Estratégia MED ('12mil')
    fin_ads = [a for a in ads if a["hook_category"] == "apelo_financeiro"]
    assert len(fin_ads) >= 1
    assert any("12mil" in a["headline"] for a in fin_ads)

    # 2. Medo / Clareza: Mundo Revalida ('Não estude no escuro')
    fear_ads = [a for a in ads if a["hook_category"] == "medo_clareza"]
    assert any("não estude no escuro" in a["headline"].lower() for a in fear_ads)

    # 3. Isca Gratuita: Medcel ('R$00,00' or 'procura-se')
    free_ads = [a for a in ads if a["hook_category"] == "isca_gratuita"]
    assert any("r$00,00" in a["headline"].lower() or "grátis" in a["headline"].lower() for a in free_ads)

    # 4. Antecipação de Funil: Hardwork ('2026' or '2027')
    anticip_ads = [a for a in ads if a["hook_category"] == "antecipacao_funil"]
    assert any("2026" in a["headline"] for a in anticip_ads)
    assert any("2027" in a["headline"] for a in anticip_ads)

    # 5. Comunidade / WhatsApp: Medtwins ('whatsapp' or 'm60')
    comm_ads = [a for a in ads if a["hook_category"] == "comunidade_whatsapp"]
    assert any("whatsapp" in a["headline"].lower() or "m60" in a["headline"].lower() for a in comm_ads)

    # 6. Prova Prática Presencial: Revalida 360 / AlphaMed / Revmed / Mundo Revalida
    pract_ads = [a for a in ads if a["hook_category"] == "prova_pratica_presencial"]
    assert len(pract_ads) >= 4
    pract_players = set(a["competitor_id"] for a in pract_ads)
    assert "revalida360" in pract_players
    assert "alphamed_revalida" in pract_players
    assert "revmed_mentoria" in pract_players

    # 7. Desmistificação / Pegadinha: Estratégia MED / MedCof
    banca_ads = [a for a in ads if a["hook_category"] == "desmistificacao_banca"]
    assert any("pegadinha" in a["headline"].lower() or "jeito certo" in a["headline"].lower() for a in banca_ads)


def test_oracle_ad_content_exact_correspondence():
    """
    EMPIRICAL ORACLE: Verifies 1-to-1 correspondence between raw ad notes and sanitized ads.
    Ensures no ad was fabricated or omitted, and that bodies contain original strings.
    """
    raw_data = independent_parse_raw_document(RAW_DOC_FILE)
    with open(ADS_FILE, "r", encoding="utf-8") as f:
        ads_json = json.load(f)["ads"]

    for cid, raw_info in raw_data.items():
        raw_ads = [a for a in raw_info["ads"] if a.lower() not in ["não tem", "nenhum"]]
        san_ads = [a for a in ads_json if a["competitor_id"] == cid]

        assert len(raw_ads) == len(san_ads), (
            f"Ad count mismatch for {cid}: raw has {len(raw_ads)}, sanitized has {len(san_ads)}"
        )

        for raw_item, san_item in zip(raw_ads, san_ads):
            clean_raw = raw_item.lstrip("*-• ").strip()
            # The sanitized body_text or headline must contain the key text
            assert clean_raw.lower() in san_item["body_text"].lower(), (
                f"Raw ad content '{clean_raw}' missing from sanitized body '{san_item['body_text']}'"
            )


def test_adversarial_stress_and_edge_cases():
    """
    ADVERSARIAL STRESS TEST: Verifies edge cases such as zero growth, negative growth,
    extreme values, and presence of special formatting.
    """
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)
    profiles = {p["competitor_id"]: p for p in profiles_data["profiles"]}

    # Zero growth edge case: Medgrupo Revalida (17.3k -> 17.3k)
    medgrupo = profiles["medgrupo_revalida"]
    assert medgrupo["followers_delta"] == 0
    assert medgrupo["growth_rate_pct"] == 0.0

    # Negative growth edge cases: Aristo (-100), Revalideii (-400), Revalidando (-1000), Eu Médico (-100)
    assert profiles["aristo_revalida"]["followers_delta"] == -100
    assert profiles["aristo_revalida"]["growth_rate_pct"] == -1.02

    assert profiles["revalideii"]["followers_delta"] == -400
    assert profiles["revalideii"]["growth_rate_pct"] == -2.16

    assert profiles["revalidando"]["followers_delta"] == -1000
    assert profiles["revalidando"]["growth_rate_pct"] == -3.98

    assert profiles["eumedicorevalida"]["followers_delta"] == -100
    assert profiles["eumedicorevalida"]["growth_rate_pct"] == -1.72

    # High growth edge case: Revalida 360 (1.5k -> 4.4k, +193.33%)
    r360 = profiles["revalida360"]
    assert r360["followers_delta"] == 2900
    assert r360["growth_rate_pct"] == 193.33

    # Check that no numerical fields are NaN or null
    for cid, p in profiles.items():
        assert not math.isnan(p["growth_rate_pct"]), f"NaN growth_rate_pct in {cid}"
        assert p["followers_count"] >= 0, f"Negative followers_count in {cid}"
        assert p["previous_followers_count"] >= 0, f"Negative previous_followers_count in {cid}"
