"""
SerpApi Google Ads Transparency Center Scraper & Synchronizer
Author: Lagana Flow
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.database.local_db import LocalDatabase


def get_serpapi_key() -> str:
    key = os.environ.get("SERPAPI_API_KEY", "")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SERPAPI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return key


def format_unix_timestamp(ts: Optional[int]) -> str:
    if not ts:
        return "Ativo"
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(ts)


def query_serpapi_transparency(search_text: str, api_key: str, region: Optional[str] = None) -> Dict[str, Any]:
    params = {
        "engine": "google_ads_transparency_center",
        "text": search_text,
        "api_key": api_key
    }
    if region and region != "anywhere":
        params["region"] = region
    url = "https://serpapi.com/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sync_competitor_ads_with_serpapi(competitor_id: str, db: Optional[LocalDatabase] = None) -> Dict[str, Any]:
    api_key = get_serpapi_key()
    if not api_key:
        return {
            "success": False,
            "error": "Chave SERPAPI_API_KEY não configurada no arquivo .env."
        }

    if db is None:
        db = LocalDatabase()

    comp = db.get_competitor(competitor_id)
    if not comp:
        return {
            "success": False,
            "error": f"Concorrente com ID '{competitor_id}' não encontrado no banco."
        }

    # Determine best search term: root_domain > domain > legal_name
    root_domain = comp.get("root_domain") or ""
    domain = comp.get("domain") or ""
    legal_name = comp.get("legal_name") or ""

    queries_to_try = []
    if root_domain and root_domain != "N/A":
        queries_to_try.append(root_domain)
    if domain and domain != root_domain and domain != "N/A":
        queries_to_try.append(domain)
    if legal_name and legal_name != comp.get("name"):
        queries_to_try.append(legal_name.split("/")[0].strip())

    if not queries_to_try:
        queries_to_try = [comp.get("name")]

    result_data = None
    query_used = ""
    creatives = []
    total_results = 0

    for query in queries_to_try:
        try:
            data = query_serpapi_transparency(query, api_key)
            status = data.get("search_metadata", {}).get("status")
            if status == "Success":
                ad_creatives = data.get("ad_creatives", [])
                tot = data.get("search_information", {}).get("total_results") or 0
                if tot > 0 or len(ad_creatives) > 0:
                    result_data = data
                    query_used = query
                    creatives = ad_creatives
                    total_results = tot
                    break
                elif result_data is None:
                    result_data = data
                    query_used = query
        except Exception as e:
            continue

    if result_data is None:
        return {
            "success": False,
            "competitor_id": competitor_id,
            "error": "Falha na comunicação com a SerpApi."
        }

    advertiser_info = result_data.get("advertiser") or {}
    adv_id = advertiser_info.get("id", "")
    adv_name = advertiser_info.get("name") or comp.get("name")

    saved_creatives_count = 0
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        for c in creatives:
            c_id = c.get("ad_creative_id")
            if not c_id:
                continue

            format_type = (c.get("format") or "TEXT").upper()
            media = c.get("image") or c.get("link") or ""
            target = c.get("details_link") or ""
            first_seen_str = format_unix_timestamp(c.get("first_shown"))
            last_seen_str = format_unix_timestamp(c.get("last_shown"))

            headline = f"Anúncio Google Ads ({format_type}) • {comp.get('name')}"
            target_domain = c.get("target_domain") or domain or query_used
            days_shown = c.get("total_days_shown", 1)
            body = f"Veiculação ativa em {target_domain}. Total de dias em exibição no Google: {days_shown} dia(s)."

            cursor.execute("""
            INSERT INTO competitor_google_ads (
                creative_id, competitor_id, competitor_name, domain, advertiser_id, advertiser_name,
                ad_format, headline, body_text, media_url, target_url, first_seen, last_seen,
                region, is_revalida_relevant, data_origin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'anywhere', 1, 'SerpApi - Google Ads Transparency')
            ON CONFLICT(creative_id) DO UPDATE SET
                advertiser_id=excluded.advertiser_id,
                advertiser_name=excluded.advertiser_name,
                ad_format=excluded.ad_format,
                media_url=excluded.media_url,
                target_url=excluded.target_url,
                first_seen=excluded.first_seen,
                last_seen=excluded.last_seen
            """, (
                c_id,
                competitor_id,
                comp.get("name"),
                domain or root_domain,
                c.get("advertiser_id", adv_id),
                c.get("advertiser", adv_name),
                format_type,
                headline,
                body,
                media,
                target,
                first_seen_str,
                last_seen_str
            ))
            saved_creatives_count += 1

        # Update competitor stats in DB
        has_ads = 1 if (total_results > 0 or len(creatives) > 0) else 0
        cursor.execute("""
        UPDATE competitors SET
            has_google_ads = ?,
            google_ads_count_approx = ?,
            last_serpapi_sync = ?
        WHERE id = ?
        """, (
            has_ads,
            total_results if total_results > 0 else len(creatives),
            now_str,
            competitor_id
        ))
        conn.commit()

    return {
        "success": True,
        "competitor_id": competitor_id,
        "competitor_name": comp.get("name"),
        "query_used": query_used,
        "total_results": total_results,
        "creatives_saved": saved_creatives_count,
        "advertiser": advertiser_info,
        "synced_at": now_str
    }
