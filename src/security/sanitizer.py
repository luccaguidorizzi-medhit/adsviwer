"""
Security Sanitizer & Path Jail Module
Author: Lagana Flow
Protects against:
- Indirect Prompt Injection (OWASP LLM01)
- XSS and Executable Script Ingestion
- Path Traversal (Directory Escape)
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SANITIZED_DIR = DATA_DIR / "sanitized"
CONFIG_FILE = PROJECT_ROOT / "config" / "security-rules.json"


class CompetitorAdRecord(BaseModel):
    competitor_id: str
    platform: str = Field(..., description="meta, google, or tiktok")
    ad_id: str
    headline: Optional[str] = None
    body_text: Optional[str] = None
    call_to_action: Optional[str] = None
    landing_page_url: Optional[str] = None
    media_url: Optional[str] = None
    start_date: Optional[str] = None
    is_active: bool = True
    scraped_at: str


class CompetitorProfileRecord(BaseModel):
    competitor_id: str
    platform: str = "instagram"
    username: str
    full_name: Optional[str] = None
    bio_text: Optional[str] = None
    external_url: Optional[str] = None
    followers_count: Optional[int] = 0
    posts_count: Optional[int] = 0
    recent_posts: List[Dict[str, Any]] = Field(default_factory=list)
    scraped_at: str


class SecuritySanitizer:
    def __init__(self):
        self.rules = self._load_rules()
        self.injection_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.rules.get("blacklisted_prompt_injection_patterns", [])
        ]
        self.dangerous_tags = self.rules.get("strip_dangerous_html_tags", [
            "script", "style", "iframe", "object", "embed", "applet", "link", "meta"
        ])

    def _load_rules(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("security_policy", {})
        return {}

    def sanitize_text(self, text: Optional[str]) -> str:
        """Strips scripts, collapses whitespace, and neutralizes prompt injection vectors."""
        if not text or not isinstance(text, str):
            return ""

        # Remove HTML tags and entities
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(self.dangerous_tags):
            tag.decompose()
        clean = soup.get_text(separator=" ")

        # 1. Remove null bytes and non-printable control characters
        clean = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", clean)

        # 2. Normalize whitespace and newlines before scanning patterns
        clean = re.sub(r"\s+", " ", clean).strip()

        # 3. Flag or neutralize prompt injection attempts
        for pattern in self.injection_patterns:
            if pattern.search(clean):
                clean = pattern.sub("[REDACTED_SUSPICIOUS_PAYLOAD]", clean)

        # 4. Guarantee clean output with normalized whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def sanitize_html(self, raw_html: str) -> str:
        """Parses raw HTML and strips all active scripting/embedded elements."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in self.dangerous_tags:
            for s in soup.find_all(tag):
                s.decompose()
        # Remove all inline event handlers (onclick, onerror, onload, etc.)
        for tag in soup.find_all():
            tag.attrs = {
                attr: val for attr, val in tag.attrs.items()
                if not attr.lower().startswith("on") and not (isinstance(val, str) and "javascript:" in val.lower())
            }
        return str(soup)

    def verify_path_jail(self, target_path: Path, must_be_under: Path) -> Path:
        """Enforces Path Jail: target_path MUST strictly resolve inside must_be_under."""
        resolved_target = target_path.resolve()
        resolved_base = must_be_under.resolve()
        try:
            resolved_target.relative_to(resolved_base)
        except ValueError:
            raise PermissionError(
                f"[SECURITY ALERT] Path traversal blocked: '{target_path}' escapes jail '{must_be_under}'!"
            )
        return resolved_target

    def save_raw_quarantine(self, filename: str, content: str) -> Path:
        """Saves unverified raw scraped content inside the isolated data/raw directory."""
        target = RAW_DIR / filename
        safe_path = self.verify_path_jail(target, RAW_DIR)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return safe_path

    def save_sanitized(self, filename: str, data: Dict[str, Any]) -> Path:
        """Saves cleaned, structured, validated data inside data/sanitized."""
        target = SANITIZED_DIR / filename
        safe_path = self.verify_path_jail(target, SANITIZED_DIR)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return safe_path
