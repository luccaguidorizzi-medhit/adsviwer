"""
Instagram Profile & Funnel Link Watcher
Author: Lagana Flow
Extracts public profile information, bio changes, external links (funnels), and post activity.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any
from curl_cffi import requests as cffi_requests
from src.extractors.base_extractor import BaseExtractor
from src.security.sanitizer import CompetitorProfileRecord


class InstagramProfileWatcher(BaseExtractor):
    def __init__(self):
        super().__init__(name="ig_profile_watcher", min_delay_seconds=5.0, max_delay_seconds=10.0)

    def fetch_profile(self, username: str) -> Dict[str, Any]:
        """
        Fetches the public Instagram profile info using TLS-mimicking curl_cffi.
        Saves raw response in quarantine and produces clean, sanitized data.
        """
        self.wait_polite_delay()
        clean_username = username.strip().replace("@", "")
        url = f"https://www.instagram.com/{clean_username}/"

        headers = self.get_default_headers()
        headers["Referer"] = "https://www.google.com/"

        try:
            response = cffi_requests.get(url, headers=headers, impersonate="chrome120", timeout=25)
            
            # Quarentena dos dados brutos
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            raw_filename = f"ig_profile_{clean_username}_{timestamp}.html"
            self.sanitizer.save_raw_quarantine(raw_filename, response.text)

            # Processamento seguro dos metadados
            profile_data = self._extract_profile_data(response.text, clean_username)
            return profile_data
        except Exception as e:
            print(f"[InstagramProfileWatcher] Erro ao consultar perfil @{clean_username}: {e}")
            return {
                "competitor_id": clean_username,
                "platform": "instagram",
                "username": clean_username,
                "error": str(e),
                "scraped_at": datetime.now(timezone.utc).isoformat()
            }

    def _extract_profile_data(self, html_content: str, username: str) -> Dict[str, Any]:
        """Extracts og:description, meta tags and title while stripping prompt injection attempts."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # OpenGraph meta tags often contain follower count and bio snippets
        meta_desc = soup.find("meta", property="og:description")
        desc_text = meta_desc["content"] if meta_desc and "content" in meta_desc.attrs else ""

        meta_title = soup.find("meta", property="og:title")
        title_text = meta_title["content"] if meta_title and "content" in meta_title.attrs else ""

        sanitized_bio = self.sanitizer.sanitize_text(desc_text)
        sanitized_title = self.sanitizer.sanitize_text(title_text)

        # Parse followers and posts from standard description: "X Followers, Y Following, Z Posts"
        followers = 0
        posts = 0
        if "Followers" in sanitized_bio:
            parts = sanitized_bio.split(",")
            for part in parts:
                if "Followers" in part:
                    f_str = part.replace("Followers", "").replace("Seguidores", "").strip()
                    try:
                        followers = int(float(f_str.replace("k", "000").replace("m", "000000").replace(".", "").replace(",", "")))
                    except Exception:
                        pass
                if "Posts" in part or "Publicações" in part:
                    p_str = part.replace("Posts", "").replace("Publicações", "").strip()
                    try:
                        posts = int(p_str.replace(".", "").replace(",", ""))
                    except Exception:
                        pass

        record = CompetitorProfileRecord(
            competitor_id=username,
            platform="instagram",
            username=username,
            full_name=sanitized_title,
            bio_text=sanitized_bio,
            followers_count=followers,
            posts_count=posts,
            scraped_at=datetime.now(timezone.utc).isoformat()
        )
        return record.model_dump()

    def run(self, competitor_config: Dict[str, Any]) -> Dict[str, Any]:
        ig_settings = competitor_config.get("instagram", {})
        username = ig_settings.get("username", "")

        if not username:
            return {"error": "Instagram username not specified in configuration"}

        print(f"[InstagramProfileWatcher] Monitorando perfil: @{username}")
        data = self.fetch_profile(username)

        # Salva dados limpos em data/sanitized/
        filename = f"profile_ig_{competitor_config.get('id')}.json"
        self.sanitizer.save_sanitized(filename, data)
        return data
