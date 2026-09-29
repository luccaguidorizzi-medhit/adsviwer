"""
Website & Landing Page Diff Watcher
Author: Lagana Flow
Monitors competitor websites, pricing pages, and sales funnels for changes.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from curl_cffi import requests as cffi_requests
from src.extractors.base_extractor import BaseExtractor


class SiteDiffWatcher(BaseExtractor):
    def __init__(self):
        super().__init__(name="site_diff_watcher", min_delay_seconds=3.0, max_delay_seconds=6.0)

    def check_page(self, url: str, competitor_id: str) -> Dict[str, Any]:
        """Fetches landing page, computes content hash, detects changes from previous runs."""
        self.wait_polite_delay()
        headers = self.get_default_headers()

        try:
            response = cffi_requests.get(url, headers=headers, impersonate="chrome120", timeout=20)
            
            # Quarentena do HTML bruto
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            raw_filename = f"site_{competitor_id}_{timestamp}.html"
            self.sanitizer.save_raw_quarantine(raw_filename, response.text)

            # Sanitização do texto
            clean_text = self.sanitizer.sanitize_text(response.text)
            content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

            # Histórico anterior para verificação de diff
            sanitized_filename = f"site_state_{competitor_id}.json"
            sanitized_path = self.sanitizer.verify_path_jail(
                self.sanitizer.rules.get("sanitized_directory", "data/sanitized") / Path(sanitized_filename),
                Path(self.sanitizer.rules.get("sanitized_directory", "data/sanitized")).resolve()
            ) if False else None

            # Detecta se houve alteração comparando com estado anterior
            state_file = self.sanitizer.rules.get("sanitized_directory") or "data/sanitized"
            from pathlib import Path
            prev_file = Path(state_file) / sanitized_filename
            has_changed = False
            prev_hash = ""

            if prev_file.exists():
                try:
                    with open(prev_file, "r", encoding="utf-8") as f:
                        prev_data = json.load(f)
                        prev_hash = prev_data.get("content_hash", "")
                        if prev_hash and prev_hash != content_hash:
                            has_changed = True
                except Exception:
                    pass

            result = {
                "competitor_id": competitor_id,
                "url": url,
                "content_hash": content_hash,
                "previous_hash": prev_hash,
                "has_changed": has_changed,
                "text_snippet": clean_text[:500],
                "total_chars": len(clean_text),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }

            self.sanitizer.save_sanitized(sanitized_filename, result)
            return result

        except Exception as e:
            print(f"[SiteDiffWatcher] Erro ao monitorar {url}: {e}")
            return {
                "competitor_id": competitor_id,
                "url": url,
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }

    def run(self, competitor_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        competitor_id = competitor_config.get("id", "competitor")
        website = competitor_config.get("website_url")
        landing_pages = competitor_config.get("landing_pages", [])
        
        urls_to_check = []
        if website:
            urls_to_check.append(website)
        urls_to_check.extend([lp for lp in landing_pages if lp and lp not in urls_to_check])

        results = []
        for url in urls_to_check:
            print(f"[SiteDiffWatcher] Verificando página: {url}")
            res = self.check_page(url, competitor_id)
            results.append(res)
            
        return results
