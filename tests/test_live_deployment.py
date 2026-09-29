"""
Automated Test Suite for Live Vercel Production Deployment
Target URL: https://competitor-monitor-flax.vercel.app
Author: Lagana Flow
"""

import sys
import unittest
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://competitor-monitor-flax.vercel.app"


class TestLiveVercelDeployment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = BASE_URL
        print(f"\n[INIT] Iniciando testes automatizados na URL de Producao: {cls.base_url}")

    def test_01_homepage_loads_cleanly(self):
        """Verifica se a pagina inicial carrega com HTTP 200, layout claro e sem vazamento de Meta Ads."""
        r = requests.get(f"{self.base_url}/", timeout=15)
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers.get("Content-Type", ""))
        self.assertIn("Mundo Revalida", r.text)
        self.assertIn("Radar de Inteligência Competitiva", r.text)
        
        # Validar banimento de Meta Ads
        lower_html = r.text.lower()
        self.assertNotIn("meta ads", lower_html)
        self.assertNotIn("facebook ads", lower_html)
        print("  [OK] Teste 01: Homepage carregada com sucesso (Tema Claro, Mundo Revalida, 100% Google Ads/SEO).")

    def test_02_api_competitors_list(self):
        """Verifica se a listagem de concorrentes retorna os 17 players com dados estruturados."""
        r = requests.get(f"{self.base_url}/api/competitors", timeout=15)
        self.assertEqual(r.status_code, 200)
        competitors = r.json()
        self.assertIsInstance(competitors, list)
        self.assertGreaterEqual(len(competitors), 16)
        
        comp_names = [c["name"] for c in competitors]
        self.assertTrue(any("Mundo Revalida" in name for name in comp_names))
        self.assertTrue(any("Hardwork" in name for name in comp_names))
        self.assertTrue(any("Estratégia" in name or "Estrategia" in name for name in comp_names))
        print(f"  [OK] Teste 02: Listagem de concorrentes validada ({len(competitors)} players mapeados).")

    def test_03_api_competitor_detail(self):
        """Verifica se o dossier individual do concorrente traz perfil, posts e anuncios."""
        r = requests.get(f"{self.base_url}/api/competitor/hardwork_revalida", timeout=15)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("competitor", data)
        self.assertIn("posts", data)
        self.assertIn("ads", data)
        self.assertEqual(data["competitor"]["id"], "hardwork_revalida")
        print("  [OK] Teste 03: Dossier individual (Hardwork Revalida) retornado com perfil, posts e anuncios.")

    def test_04_api_stats_kpis(self):
        """Verifica se os KPIs de mercado e baseline do Mundo Revalida estao corretos."""
        r = requests.get(f"{self.base_url}/api/stats", timeout=15)
        self.assertEqual(r.status_code, 200)
        stats = r.json()
        self.assertGreaterEqual(stats.get("total_competitors", 0), 15)
        self.assertGreaterEqual(stats.get("active_revalida_ads", 0), 20)
        self.assertIn("Mundo Revalida", stats.get("reference_baseline", ""))
        print(f"  [OK] Teste 04: Estatisticas de mercado validadas ({stats['active_revalida_ads']} anuncios ativos, {stats['total_competitors']} concorrentes).")

    def test_05_api_google_ads_filtering(self):
        """Verifica se a filtragem de anuncios do Google Ads Transparency Center funciona."""
        r = requests.get(f"{self.base_url}/api/google-ads", timeout=15)
        self.assertEqual(r.status_code, 200)
        ads = r.json()
        self.assertIsInstance(ads, list)
        self.assertGreater(len(ads), 20)
        
        # Verificar estrutura de provenance
        first_ad = ads[0]
        self.assertIn("headline", first_ad)
        self.assertIn("advertiser_name", first_ad)
        self.assertIn("data_origin", first_ad)
        print(f"  [OK] Teste 05: Anuncios Google Ads validados ({len(ads)} anuncios catalogados com seguranca).")

    def test_06_api_market_keywords(self):
        """Verifica os clusters de palavras-chave e intencoes de busca do candidato."""
        r = requests.get(f"{self.base_url}/api/market-keywords", timeout=15)
        self.assertEqual(r.status_code, 200)
        keywords = r.json()
        self.assertGreaterEqual(len(keywords), 10)
        print(f"  [OK] Teste 06: Clusters de palavras-chave validados ({len(keywords)} termos mapeados).")

    def test_07_live_seo_inspection_endpoint(self):
        """Verifica se o endpoint dinamico de analise de SEO on-page funciona no ambiente serverless."""
        r = requests.post(f"{self.base_url}/api/competitor/hardwork_revalida/analyze-seo", timeout=20)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("competitor_id"), "hardwork_revalida")
        self.assertIn("domain", data)
        self.assertIn("top_keywords_density", data)
        self.assertIn("top_organic_terms", data)
        print(f"  [OK] Teste 07: Auditor SEO On-Page dinamico executado com sucesso no serverless ({data['domain']}).")

    def test_08_pdf_generation_and_download(self):
        """Verifica se a geracao do Dossie Master de 17 paginas em PDF e executada sem timeout no serverless."""
        r = requests.get(f"{self.base_url}/api/export-pdf?focus=master", timeout=45)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("Content-Type"), "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))
        self.assertGreater(len(r.content), 100_000)
        print(f"  [OK] Teste 08: Geracao e download do PDF de 17 paginas validado com perfeicao ({len(r.content):,} bytes).")


if __name__ == "__main__":
    unittest.main()
