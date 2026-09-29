"""
Market Data Processor & Intelligence Pipeline
Author: Lagana Flow

This script processes raw intelligence notes from `data/raw/concorrentes_doc.txt`
and `config/competitors.json`, sanitizes all inputs using `SecuritySanitizer`,
validates Pydantic records, and generates sanitized datasets in `data/sanitized/`:
- `data/sanitized/competitor_profiles.json`
- `data/sanitized/competitor_ads.json`
- `data/sanitized/market_summary.json`
- `data/sanitized/supabase_schema.sql`
- Individual `ads_meta_{id}.json` and `profile_ig_{id}.json` bundles
"""

import os
import sys
import re
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.security.sanitizer import (
    SecuritySanitizer,
    CompetitorProfileRecord,
    CompetitorAdRecord,
    RAW_DIR,
    SANITIZED_DIR,
)


CONFIG_COMPETITORS = PROJECT_ROOT / "config" / "competitors.json"
RAW_DOC_FILE = RAW_DIR / "concorrentes_doc.txt"


class MarketDataProcessor:
    def __init__(self):
        self.sanitizer = SecuritySanitizer()
        # Verify path jail on base directories
        self.sanitizer.verify_path_jail(RAW_DIR, PROJECT_ROOT / "data")
        self.sanitizer.verify_path_jail(SANITIZED_DIR, PROJECT_ROOT / "data")
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def load_raw_doc(self) -> str:
        """Loads raw competitor document under path jail verification."""
        verified_path = self.sanitizer.verify_path_jail(RAW_DOC_FILE, RAW_DIR)
        with open(verified_path, "r", encoding="utf-8") as f:
            return f.read()

    def load_config_competitors(self) -> Dict[str, Any]:
        """Loads competitors configuration."""
        with open(CONFIG_COMPETITORS, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_followers_number(self, val_str: str) -> int:
        """Converts followers string like '65.2k', '280k', '4,4k' to integer."""
        if not val_str:
            return 0
        cleaned = val_str.strip().lower().replace(",", ".")
        if "k" in cleaned:
            number_part = cleaned.replace("k", "").strip()
            try:
                return int(float(number_part) * 1000)
            except ValueError:
                return 0
        try:
            return int(cleaned)
        except ValueError:
            return 0

    def extract_raw_notes_per_player(self, raw_text: str) -> Dict[str, Dict[str, Any]]:
        """Parses the structured/unstructured raw notes from concorrentes_doc.txt."""
        player_blocks: Dict[str, Dict[str, Any]] = {}
        
        # Player signature mappings in doc
        signatures = [
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

        for p_id, p_name in signatures:
            player_blocks[p_id] = {
                "name": p_name,
                "reels": [],
                "static_posts": [],
                "paid_ads": [],
                "notes": []
            }

        # Detailed extraction of baseline and april 2026 followers and topics
        lines = raw_text.splitlines()
        current_id: Optional[str] = None
        current_section = None

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check if this line is a player header
            matched_player = False
            for p_id, p_name in signatures:
                if line_str.lower().startswith(p_name.lower() + ":") or line_str.lower() == p_name.lower():
                    current_id = p_id
                    matched_player = True
                    # Check if line contains followers count
                    f_match = re.search(r"seguidores\s+([\d\.,]+k?)", line_str, re.IGNORECASE)
                    if f_match:
                        player_blocks[current_id]["notes"].append(f"Followers info: {f_match.group(1)}")
                    break
            
            if matched_player:
                current_section = None
                continue

            if current_id:
                lower_line = line_str.lower()
                if "últimos 3 reels" in lower_line or "social media" in lower_line:
                    current_section = "reels"
                    continue
                elif "últimos estático" in lower_line or "último estático" in lower_line:
                    current_section = "static"
                    continue
                elif "tráfego pago" in lower_line:
                    current_section = "ads"
                    continue
                elif "último post 2025" in lower_line or "inativo" in lower_line:
                    player_blocks[current_id]["notes"].append("Inativo desde 2025")
                    continue

                clean_item = self.sanitizer.sanitize_text(line_str.lstrip("*-• "))
                if not clean_item:
                    continue

                if current_section == "reels":
                    player_blocks[current_id]["reels"].append(clean_item)
                elif current_section == "static":
                    player_blocks[current_id]["static_posts"].append(clean_item)
                elif current_section == "ads":
                    player_blocks[current_id]["paid_ads"].append(clean_item)
                else:
                    player_blocks[current_id]["notes"].append(clean_item)

        return player_blocks

    def process_all(self) -> Dict[str, Any]:
        """Main pipeline execution: sanitization, validation, structuring, and saving."""
        raw_text = self.load_raw_doc()
        config_data = self.load_config_competitors()
        extracted_doc = self.extract_raw_notes_per_player(raw_text)

        # Baseline & April 2026 verified metrics
        metrics_truth = {
            "mundo_revalida": {"prev": 54000, "curr": 65200, "tier": "Baseline de Referência / Líder Nicho", "yt": "https://www.youtube.com/@mundorevalida", "site": "https://mundorevalida.com.br", "city": "São Paulo (SP)", "spend_tier": "Mid Spender (Alta Eficiência)", "price_range": "R$ 3.000 a R$ 6.500"},
            "estrategia_med": {"prev": 217500, "curr": 280000, "tier": "Tier 1 - Líder Geral Multiprova", "yt": "https://www.youtube.com/@EstrategiaMed", "site": "https://med.estrategia.com", "city": "São Paulo (SP) / Nacional", "spend_tier": "Heavy Spender (Corporativo)", "price_range": "R$ 1.500 a R$ 7.500+"},
            "medcel": {"prev": 44400, "curr": 125000, "tier": "Tier 1 - Grande Player Corporativo", "yt": "https://www.youtube.com/@medcel", "site": "https://www.medcel.com.br", "city": "Nacional / Online", "spend_tier": "Heavy Spender (Captação em Massa)", "price_range": "R$ 0,00 (Isca) a R$ 5.500"},
            "hardwork_revalida": {"prev": 37500, "curr": 43100, "tier": "Tier 1 - Grande Concorrente Especialista", "yt": "https://www.youtube.com/@HardworkMedicina", "site": "https://home.hardworkmedicina.com.br", "city": "Online / Nacional", "spend_tier": "Mid Spender", "price_range": "R$ 1.490 a R$ 3.590"},
            "medtwins": {"prev": 26400, "curr": 32200, "tier": "Tier 2 - Forte no Revalida", "yt": "https://www.youtube.com/@medtwinsrevalida", "site": "https://medtwins.com.br", "city": "Online / Presencial Pontual", "spend_tier": "Mid Spender (Lançamentos)", "price_range": "R$ 1.497 a R$ 6.000"},
            "bastidores_revalida": {"prev": 25800, "curr": 31800, "tier": "Tier 2 - Especialista de Nicho", "yt": "https://www.youtube.com/@bastidoresdorevalida", "site": "https://bastidoresdorevalida.com.br", "city": "Online / Workshop Itinerante", "spend_tier": "Mid Spender", "price_range": "R$ 800 a R$ 4.500"},
            "medcof_revalida": {"prev": 14200, "curr": 21800, "tier": "Tier 2 - Em Alta Crescimento", "yt": "https://www.youtube.com/@grupomedcof", "site": "https://revalida.grupomedcof.com.br", "city": "São Paulo (SP) / Online", "spend_tier": "Mid Spender", "price_range": "R$ 3.500 a R$ 5.000"},
            "pense_revalida": {"prev": 14900, "curr": 19300, "tier": "Tier 3 - Prova Prática & Checklists", "yt": "https://www.youtube.com/@penserevalida", "site": "https://penserevalida.com.br", "city": "Online", "spend_tier": "100% Orgânico", "price_range": "R$ 1.200 a R$ 2.500"},
            "revalideii": {"prev": 18500, "curr": 18100, "tier": "Tier 3 - Escola da Prática & Materiais", "yt": "https://www.youtube.com/@revalideii6331", "site": "https://revalideii.com.br", "city": "Online / Presencial", "spend_tier": "100% Orgânico (Retração)", "price_range": "R$ 350 a R$ 4.200"},
            "medgrupo_revalida": {"prev": 17300, "curr": 17300, "tier": "Tier 1 - Tradicional de Mercado", "yt": "https://www.youtube.com/@medgrupo", "site": "https://medgrupo.com.br", "city": "Rio de Janeiro / SP / Presencial CPMED", "spend_tier": "Orgânico / Impulsionamento Simples", "price_range": "R$ 6.000 a R$ 10.000+"},
            "revmed_mentoria": {"prev": 14400, "curr": 14900, "tier": "Tier 3 - Cursos Presenciais & Mentoria Fronteira", "yt": "", "site": "https://revmed.com.br", "city": "Foz do Iguaçu (PR)", "spend_tier": "Hiper-Local Presencial", "price_range": "R$ 3.500 a R$ 5.500"},
            "alphamed_revalida": {"prev": 7700, "curr": 9700, "tier": "Tier 4 - Presencial & Habilidades Clínicas", "yt": "", "site": "https://alphamedrevalida.com.br", "city": "Presencial / Regional", "spend_tier": "Hiper-Local Presencial", "price_range": "R$ 3.000 a R$ 4.500"},
            "aristo_revalida": {"prev": 9800, "curr": 9700, "tier": "Tier 3 - Metodologia IA / Repetição", "yt": "https://www.youtube.com/@AristoRevalida", "site": "https://aristo.com.br", "city": "Online", "spend_tier": "100% Orgânico (Retração)", "price_range": "R$ 2.500 a R$ 4.000"},
            "revalida360": {"prev": 1500, "curr": 4400, "tier": "Tier 4 - Hiperaceleração Presencial Foz", "yt": "", "site": "https://revalida360.com.br", "city": "Foz do Iguaçu (PR)", "spend_tier": "Hiper-Local Presencial (+193%)", "price_range": "R$ 3.500 a R$ 5.000"},
            "revalidando": {"prev": 25100, "curr": 24100, "tier": "Inativo / Abandonado", "yt": "", "site": "", "city": "N/A", "spend_tier": "Zumbi (Sem atividade)", "price_range": "N/A"},
            "eumedicorevalida": {"prev": 5800, "curr": 5700, "tier": "Inativo / Abandonado", "yt": "", "site": "", "city": "N/A", "spend_tier": "Zumbi (Sem atividade)", "price_range": "N/A"},
        }

        # Build list of all players (our brand + competitors)
        raw_players = [config_data["our_brand"]] + config_data["competitors"]

        sanitized_profiles: List[Dict[str, Any]] = []
        all_ads_records: List[Dict[str, Any]] = []

        for p in raw_players:
            p_id = p["id"]
            p_name = self.sanitizer.sanitize_text(p["name"])
            p_status = p.get("status", "active")
            p_focus = self.sanitizer.sanitize_text(p.get("focus", ""))
            meta_info = metrics_truth.get(p_id, {})

            prev_followers = meta_info.get("prev", 0)
            curr_followers = meta_info.get("curr", 0)
            delta_followers = curr_followers - prev_followers
            growth_pct = round((delta_followers / prev_followers * 100), 2) if prev_followers > 0 else 0.0

            ig_username = p.get("instagram", {}).get("username", "")
            ig_profile_url = p.get("instagram", {}).get("profile_url", "")
            yt_url = meta_info.get("yt") or p.get("youtube", "")
            website_url = meta_info.get("site") or p.get("website_url", "")

            # Recent posts from raw doc
            doc_data = extracted_doc.get(p_id, {})
            recent_reels = doc_data.get("reels", [])
            recent_statics = doc_data.get("static_posts", [])
            raw_paid_ads = doc_data.get("paid_ads", [])

            recent_posts_combined = []
            for r in recent_reels:
                recent_posts_combined.append({"type": "reels", "topic": self.sanitizer.sanitize_text(r)})
            for s in recent_statics:
                recent_posts_combined.append({"type": "static", "topic": self.sanitizer.sanitize_text(s)})

            # Instantiate and validate Pydantic Profile Record
            profile_record = CompetitorProfileRecord(
                competitor_id=p_id,
                platform="instagram",
                username=ig_username,
                full_name=p_name,
                bio_text=p_focus,
                external_url=website_url if website_url else None,
                followers_count=curr_followers,
                posts_count=len(recent_posts_combined),
                recent_posts=recent_posts_combined,
                scraped_at=self.timestamp,
            )

            # Enriched profile object
            enriched_profile = {
                **profile_record.model_dump(),
                "status": p_status,
                "tier": meta_info.get("tier", p.get("tier", "Outro")),
                "previous_followers_count": prev_followers,
                "followers_delta": delta_followers,
                "growth_rate_pct": growth_pct,
                "youtube_url": yt_url,
                "website_url": website_url,
                "instagram_profile_url": ig_profile_url,
                "focus_summary": p_focus,
                "practical_exam_city": meta_info.get("city", "Online"),
                "pricing_range": meta_info.get("price_range", "Sob consulta"),
                "media_spend_tier": meta_info.get("spend_tier", "Orgânico"),
                "has_first_phase": p_id not in ["revalida360", "revmed_mentoria", "alphamed_revalida", "pense_revalida"],
                "has_second_phase_practical": p_id not in ["revalidando", "eumedicorevalida", "aristo_revalida"],
                "has_flashcards_physical": p_id == "revalideii",
            }
            sanitized_profiles.append(enriched_profile)

            # Process Ads for this competitor
            competitor_ads: List[Dict[str, Any]] = []
            for idx, raw_ad in enumerate(raw_paid_ads):
                sanitized_ad_text = self.sanitizer.sanitize_text(raw_ad)
                if not sanitized_ad_text or sanitized_ad_text.lower() in ["não tem", "nenhum"]:
                    continue

                # Classify hook and format
                lower_ad = sanitized_ad_text.lower()
                hook_cat = "outro"
                creative_fmt = "estatico"

                if "reels:" in lower_ad or "vídeo" in lower_ad or "video" in lower_ad:
                    creative_fmt = "reels_video"
                elif "estático:" in lower_ad or "carrossel" in lower_ad:
                    creative_fmt = "estatico"

                # Categorize the 7 hooks
                if any(k in lower_ad for k in ["12mil", "12 mil", "dinheiro", "mensal", "ganhar"]):
                    hook_cat = "apelo_financeiro"
                elif any(k in lower_ad for k in ["escuro", "laço", "tempo", "desafios"]):
                    hook_cat = "medo_clareza"
                elif any(k in lower_ad for k in ["r$00,00", "r$ 0", "0,00", "grátis", "gratis", "procura-se"]):
                    hook_cat = "isca_gratuita"
                elif any(k in lower_ad for k in ["2026", "2027", "antecipa"]):
                    hook_cat = "antecipacao_funil"
                elif any(k in lower_ad for k in ["whatsapp", "m60", "vip", "grupo"]):
                    hook_cat = "comunidade_whatsapp"
                elif any(k in lower_ad for k in ["foz do iguaçu", "foz", "presencial", "aula presencial", "prática"]):
                    hook_cat = "prova_pratica_presencial"
                elif any(k in lower_ad for k in ["pegadinha", "questão", "jeito certo", "mentira", "desmistifica"]):
                    hook_cat = "desmistificacao_banca"
                elif "depoimento" in lower_ad:
                    hook_cat = "prova_social_depoimento"

                ad_id = f"ad_{p_id}_{idx+1:02d}"
                ad_record = CompetitorAdRecord(
                    competitor_id=p_id,
                    platform="meta",
                    ad_id=ad_id,
                    headline=sanitized_ad_text.replace("Reels:", "").replace("Estático:", "").strip(),
                    body_text=f"Campanha ativa de Meta Ads para {p_name}: {sanitized_ad_text}",
                    call_to_action="Saiba Mais" if "aula" not in lower_ad else "Inscreva-se",
                    landing_page_url=website_url if website_url else "https://facebook.com/ads/library",
                    media_url=None,
                    start_date="2026-04-01T00:00:00Z",
                    is_active=True,
                    scraped_at=self.timestamp,
                )

                ad_dict = {
                    **ad_record.model_dump(),
                    "competitor_name": p_name,
                    "hook_category": hook_cat,
                    "creative_format": creative_fmt,
                    "spend_tier": meta_info.get("spend_tier", "Orgânico"),
                }
                competitor_ads.append(ad_dict)
                all_ads_records.append(ad_dict)

            # Save individual files for bridge interoperability
            # 1. Profile IG
            self.sanitizer.save_sanitized(
                f"profile_ig_{p_id}.json",
                profile_record.model_dump()
            )
            # 2. Ads Meta
            self.sanitizer.save_sanitized(
                f"ads_meta_{p_id}.json",
                {
                    "competitor_id": p_id,
                    "competitor_name": p_name,
                    "platform": "meta",
                    "total_ads_found": len(competitor_ads),
                    "scraped_at": self.timestamp,
                    "ads": competitor_ads
                }
            )
            # 3. Site state hash
            clean_hash = hashlib.sha256(f"{p_name}{website_url}{p_focus}".encode("utf-8")).hexdigest()
            self.sanitizer.save_sanitized(
                f"site_state_{p_id}.json",
                {
                    "competitor_id": p_id,
                    "target_url": website_url,
                    "content_hash": clean_hash,
                    "has_changed": False,
                    "last_checked": self.timestamp
                }
            )

        # 1. Save master competitor_profiles.json
        self.sanitizer.save_sanitized(
            "competitor_profiles.json",
            {
                "version": "2.0.0",
                "author": "Lagana Flow",
                "generated_at": self.timestamp,
                "total_profiles": len(sanitized_profiles),
                "profiles": sanitized_profiles
            }
        )

        # 2. Save master competitor_ads.json
        self.sanitizer.save_sanitized(
            "competitor_ads.json",
            {
                "version": "2.0.0",
                "author": "Lagana Flow",
                "generated_at": self.timestamp,
                "total_ads": len(all_ads_records),
                "ads": all_ads_records
            }
        )

        # 3. Build and save market_summary.json
        active_players = [p for p in sanitized_profiles if p["status"] != "inactive_2025"]
        total_active_followers = sum(p["followers_count"] for p in active_players)
        total_net_growth = sum(p["followers_delta"] for p in active_players)
        
        # Rankings
        ranked_by_followers = sorted(active_players, key=lambda x: x["followers_count"], reverse=True)
        ranked_by_growth_pct = sorted(active_players, key=lambda x: x["growth_rate_pct"], reverse=True)

        hook_counts: Dict[str, int] = {}
        for ad in all_ads_records:
            cat = ad["hook_category"]
            hook_counts[cat] = hook_counts.get(cat, 0) + 1

        summary_data = {
            "version": "2.0.0",
            "author": "Lagana Flow",
            "generated_at": self.timestamp,
            "metrics": {
                "total_tracked_players": len(sanitized_profiles),
                "active_players_count": len(active_players),
                "inactive_players_count": len(sanitized_profiles) - len(active_players),
                "total_audience_tracked": total_active_followers,
                "total_net_audience_growth": total_net_growth,
                "our_brand": {
                    "id": "mundo_revalida",
                    "followers": 65200,
                    "followers_delta": 11200,
                    "growth_pct": 20.74,
                    "market_share_in_niche": round((65200 / (total_active_followers - 280000 - 125000)) * 100, 2), # Excluding general residency giants
                    "rank_in_dedicated_revalida": 1
                },
                "fastest_growing_player": {
                    "id": "revalida360",
                    "name": "Revalida 360",
                    "growth_pct": 193.33,
                    "city": "Foz do Iguaçu (PR)"
                },
                "fastest_growing_corporate": {
                    "id": "medcel",
                    "name": "Medcel",
                    "growth_pct": 181.53
                }
            },
            "hook_distribution": hook_counts,
            "top_audience_ranking": [
                {"rank": i+1, "id": p["competitor_id"], "name": p["full_name"], "followers": p["followers_count"], "delta": p["followers_delta"], "growth_pct": p["growth_rate_pct"]}
                for i, p in enumerate(ranked_by_followers[:7])
            ],
            "top_growth_velocity_ranking": [
                {"rank": i+1, "id": p["competitor_id"], "name": p["full_name"], "growth_pct": p["growth_rate_pct"], "delta": p["followers_delta"], "followers": p["followers_count"]}
                for i, p in enumerate(ranked_by_growth_pct[:7])
            ]
        }
        self.sanitizer.save_sanitized("market_summary.json", summary_data)

        # 4. Generate supabase_schema.sql
        sql_content = self.generate_supabase_schema()
        sql_target = SANITIZED_DIR / "supabase_schema.sql"
        safe_sql_path = self.sanitizer.verify_path_jail(sql_target, SANITIZED_DIR)
        with open(safe_sql_path, "w", encoding="utf-8") as f:
            f.write(sql_content)

        return {
            "total_profiles": len(sanitized_profiles),
            "total_ads": len(all_ads_records),
            "summary": summary_data
        }

    def generate_supabase_schema(self) -> str:
        """Generates comprehensive SQL DDL with RLS policies, tables and SWOT seeds."""
        return """-- =====================================================================
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
"""


if __name__ == "__main__":
    processor = MarketDataProcessor()
    res = processor.process_all()
    print(f"✅ Processamento concluído com sucesso!")
    print(f"Perfis sanitizados: {res['total_profiles']}")
    print(f"Anúncios catalogados: {res['total_ads']}")
    print(f"Audiência total monitorada: {res['summary']['metrics']['total_audience_tracked']}")
