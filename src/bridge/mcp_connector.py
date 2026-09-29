"""
Secure MCP & Cross-Project Bridge
Author: Lagana Flow
Connects the competitor-monitor system safely to:
- MCP Servers (Supabase, Gemini API, Google Workspace, GitHub)
- Adjacent projects in scratch/ (sales-clarity, migracao-landing-pages, etc.)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

console = Console()
SCRATCH_DIR = Path("C:/Users/Lucca/.gemini/antigravity/scratch")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class MCPCrossProjectBridge:
    def __init__(self):
        self.config_path = PROJECT_ROOT / "config" / "mcp-bridge.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "enabled_mcps": ["supabase-thiago", "gemini-api", "google-workspace-general", "github"],
            "shared_scratch_projects": [
                "sales-clarity",
                "migracao-landing-pages",
                "workshop-dr-fillipe"
            ]
        }

    def list_available_scratch_projects(self) -> List[str]:
        """Lists accessible projects in scratch without leaving workspace boundaries."""
        if not SCRATCH_DIR.exists():
            return []
        return [d.name for d in SCRATCH_DIR.iterdir() if d.is_dir()]

    def export_to_shared_format(self, competitor_id: str) -> Dict[str, Any]:
        """Collects all sanitized data for a competitor into a unified format for other projects and MCPs."""
        sanitized_dir = PROJECT_ROOT / "data" / "sanitized"
        
        ads_file = sanitized_dir / f"ads_meta_{competitor_id}.json"
        profile_file = sanitized_dir / f"profile_ig_{competitor_id}.json"
        site_file = sanitized_dir / f"site_state_{competitor_id}.json"

        bundle = {
            "competitor_id": competitor_id,
            "ads": json.load(open(ads_file, "r", encoding="utf-8")) if ads_file.exists() else {},
            "instagram": json.load(open(profile_file, "r", encoding="utf-8")) if profile_file.exists() else {},
            "website_state": json.load(open(site_file, "r", encoding="utf-8")) if site_file.exists() else {}
        }
        return bundle

    def generate_supabase_schema(self) -> str:
        """Returns the recommended SQL table schema to store competitor data in Supabase."""
        return """
        -- Schema for Competitor Intelligence in Supabase
        CREATE TABLE IF NOT EXISTS competitor_profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            instagram_username TEXT,
            followers_count INTEGER DEFAULT 0,
            bio_text TEXT,
            website_url TEXT,
            last_checked_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS competitor_ads (
            id TEXT PRIMARY KEY,
            competitor_id TEXT REFERENCES competitor_profiles(id),
            platform TEXT NOT NULL,
            headline TEXT,
            body_text TEXT,
            landing_page_url TEXT,
            media_url TEXT,
            start_date TIMESTAMPTZ,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS competitor_site_changes (
            id SERIAL PRIMARY KEY,
            competitor_id TEXT REFERENCES competitor_profiles(id),
            url TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            has_changed BOOLEAN DEFAULT FALSE,
            snippet TEXT,
            detected_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
