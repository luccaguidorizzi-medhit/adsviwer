"""
Base Extractor Class with Security Controls
Author: Lagana Flow
Enforces:
- Rate Limiting and Polite Crawling
- Timeout Controls
- Automatic Quarantine and Sanitization
"""

import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from src.security.sanitizer import SecuritySanitizer


class BaseExtractor(ABC):
    def __init__(self, name: str, min_delay_seconds: float = 3.0, max_delay_seconds: float = 6.0):
        self.name = name
        self.min_delay = min_delay_seconds
        self.max_delay = max_delay_seconds
        self.sanitizer = SecuritySanitizer()
        self.last_request_time = 0.0

    def wait_polite_delay(self):
        """Prevents IP blocks and abusive request rates."""
        elapsed = time.time() - self.last_request_time
        target_delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < target_delay:
            time.sleep(target_delay - elapsed)
        self.last_request_time = time.time()

    def get_default_headers(self) -> Dict[str, str]:
        """Modern browser headers to avoid trivial bot detection."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

    @abstractmethod
    def run(self, competitor_config: Dict[str, Any]) -> Dict[str, Any]:
        """Subclasses must implement the extraction workflow."""
        pass
