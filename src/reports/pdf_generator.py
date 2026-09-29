"""
Dossiê Executivo de Inteligência Competitiva & Google Ads — Revalidação Médica INEP
Marca & Referência: Mundo Revalida
Diagramação & Arquitetura Forense: Lagana Flow

Estrutura:
- Página 1: Capa & Visão Geral Executiva do Mercado, KPIs Gerais, Matriz Resumo e Benchmark Próprio (Mundo Revalida).
- Páginas 2 a 17: Dossiê Individual e Exclusivo por Concorrente (1 página por player com links 100% clicáveis,
  dados cadastrais, CNPJ, Razão Social, links de pareamento do Google Ads Transparency, palavras-chave,
  termos de pesquisa reais, segregação de temas e SEO).
"""

import sys
import json
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Force UTF-8 on Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
if os.environ.get("VERCEL"):
    OUTPUT_DIR = Path("/tmp/reports")
else:
    OUTPUT_DIR = PROJECT_ROOT / "data" / "reports"
try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

from src.database.local_db import LocalDatabase


def safe_text(val: Any) -> str:
    """Safely escapes text for ReportLab XML/HTML Paragraph parsing."""
    if val is None:
        return ""
    s = str(val)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


class NumberedCanvas(canvas.Canvas):
    """Header e Rodapé institucional dinâmico para o Dossiê Mundo Revalida."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header (Em todas as páginas a partir da Página 2)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#0F766E")) # Emerald/Teal
            self.drawString(1.5 * cm, 28.5 * cm, "MUNDO REVALIDA • DOSSIÊ DE INTELIGÊNCIA COMPETITIVA & GOOGLE ADS")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(19.5 * cm, 28.5 * cm, "AUDITORIA FORENSE REVALIDA INEP")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.6)
            self.line(1.5 * cm, 28.3 * cm, 19.5 * cm, 28.3 * cm)

        # Footer Institucional (Todas as páginas)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.6)
        self.line(1.5 * cm, 1.4 * cm, 19.5 * cm, 1.4 * cm)
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.HexColor("#0F766E"))
        self.drawString(1.5 * cm, 1.0 * cm, "Mundo Revalida")
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(3.6 * cm, 1.0 * cm, "| Sistema de Inteligência Competitiva • Todos os links deste relatório são interativos e clicáveis")
        self.drawRightString(19.5 * cm, 1.0 * cm, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


class CompetitorReportGenerator:
    def __init__(self):
        self.db = LocalDatabase()
        self.styles = self._setup_styles()

    def _setup_styles(self):
        styles = getSampleStyleSheet()

        # Paleta Corporativa Clara (Executive Light Mode)
        self.c_navy = colors.HexColor("#0F172A")
        self.c_emerald = colors.HexColor("#047857")
        self.c_emerald_dark = colors.HexColor("#065F46")
        self.c_teal = colors.HexColor("#0F766E")
        self.c_blue = colors.HexColor("#0284C7")
        self.c_sky_dark = colors.HexColor("#0369A1")
        self.c_amber = colors.HexColor("#B45309")
        self.c_text = colors.HexColor("#1E293B")
        self.c_muted = colors.HexColor("#64748B")
        self.c_card_bg = colors.HexColor("#F8FAFC")
        self.c_border = colors.HexColor("#E2E8F0")
        self.c_border_emerald = colors.HexColor("#A7F3D0")
        self.c_bg_emerald_light = colors.HexColor("#ECFDF5")
        self.c_bg_blue_light = colors.HexColor("#F0F9FF")
        self.c_bg_amber_light = colors.HexColor("#FFFBEB")

        styles.add(ParagraphStyle(
            name="CoverPreTitle",
            fontName="Helvetica-Bold",
            fontSize=9.0,
            leading=12.0,
            textColor=self.c_emerald,
            spaceAfter=3
        ))

        styles.add(ParagraphStyle(
            name="CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=16.0,
            leading=20.0,
            textColor=self.c_navy,
            spaceAfter=4
        ))

        styles.add(ParagraphStyle(
            name="CoverSubtitle",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.0,
            textColor=self.c_muted,
            spaceAfter=6
        ))

        styles.add(ParagraphStyle(
            name="CompPageTitle",
            fontName="Helvetica-Bold",
            fontSize=14.0,
            leading=17.0,
            textColor=self.c_navy
        ))

        styles.add(ParagraphStyle(
            name="CompBadge",
            fontName="Helvetica-Bold",
            fontSize=8.0,
            leading=10.5,
            textColor=self.c_navy
        ))

        styles.add(ParagraphStyle(
            name="SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13.0,
            textColor=self.c_navy,
            spaceBefore=4,
            spaceAfter=2,
            keepWithNext=True
        ))

        styles.add(ParagraphStyle(
            name="BodySmall",
            fontName="Helvetica",
            fontSize=8.0,
            leading=11.2,
            textColor=self.c_text
        ))

        styles.add(ParagraphStyle(
            name="BodySmallBold",
            fontName="Helvetica-Bold",
            fontSize=8.0,
            leading=11.2,
            textColor=self.c_navy
        ))

        styles.add(ParagraphStyle(
            name="TableCellNormal",
            fontName="Helvetica",
            fontSize=7.6,
            leading=10.4,
            textColor=self.c_text
        ))

        styles.add(ParagraphStyle(
            name="TableCellBold",
            fontName="Helvetica-Bold",
            fontSize=7.6,
            leading=10.4,
            textColor=self.c_navy
        ))

        styles.add(ParagraphStyle(
            name="TableHead",
            fontName="Helvetica-Bold",
            fontSize=8.0,
            leading=10.5,
            textColor=colors.white
        ))

        styles.add(ParagraphStyle(
            name="LinkText",
            fontName="Helvetica",
            fontSize=7.6,
            leading=10.4,
            textColor=self.c_blue
        ))

        styles.add(ParagraphStyle(
            name="RevalidaScoreBox",
            fontName="Helvetica",
            fontSize=8.2,
            leading=11.5,
            textColor=self.c_navy
        ))

        return styles

    def generate_pdf(self, focus: str = "master") -> Path:
        target_path = OUTPUT_DIR / "Dossie_Inteligencia_Competitiva_Revalida_INEP.pdf"
        
        doc = SimpleDocTemplate(
            str(target_path),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm
        )

        all_competitors = self.db.get_all_competitors()
        all_ads = self.db.get_google_ads()

        # Separate Mundo Revalida from external competitors
        our_brand = next((c for c in all_competitors if c.get("id") == "mundo_revalida" or c.get("is_our_brand") == 1), None)
        external_comps = [c for c in all_competitors if c.get("id") != "mundo_revalida" and not c.get("is_our_brand")]
        external_comps.sort(key=lambda x: (x.get("domain_reputation_score") or 0), reverse=True)

        story = []

        # =========================================================================
        # PÁGINA 1: CAPA, RESUMO EXECUTIVO DO MERCADO & NOSSO BENCHMARK
        # =========================================================================
        story.append(Paragraph("MUNDO REVALIDA • INTELIGÊNCIA DE MERCADO", self.styles["CoverPreTitle"]))
        story.append(Paragraph("Dossiê Executivo de Inteligência Competitiva & Google Ads", self.styles["CoverTitle"]))
        story.append(Paragraph(
            f"Auditoria Forense de Mídia Paga, Pareamento Societário na Receita Federal e SEO • Emissão: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles["CoverSubtitle"]
        ))

        # KPI Summary Cards (Table)
        with_ads_count = sum(1 for c in external_comps if c.get("has_google_ads") == 1)
        no_ads_count = len(external_comps) - with_ads_count
        total_revalida_ads = sum(c.get("revalida_ads_count") or 0 for c in external_comps)

        kpi_data = [
            [
                Paragraph("<b>Concorrentes Monitorados</b>", self.styles["TableCellBold"]),
                Paragraph("<b>Com Anúncios no Google</b>", self.styles["TableCellBold"]),
                Paragraph("<b>Sem Anúncios no Google</b>", self.styles["TableCellBold"]),
                Paragraph("<b>Ads Específicos Revalida</b>", self.styles["TableCellBold"]),
            ],
            [
                Paragraph(f"<font size='10' color='#0F172A'><b>{len(external_comps)} Players</b></font><br/><font color='#64748B'>100% no Revalida INEP</font>", self.styles["TableCellNormal"]),
                Paragraph(f"<font size='10' color='#047857'><b>{with_ads_count} Players ({round(with_ads_count/len(external_comps)*100)}%)</b></font><br/><font color='#64748B'>Disputam Search/YouTube</font>", self.styles["TableCellNormal"]),
                Paragraph(f"<font size='10' color='#475569'><b>{no_ads_count} Players ({round(no_ads_count/len(external_comps)*100)}%)</b></font><br/><font color='#64748B'>100% Orgânico / SEO / Próprio</font>", self.styles["TableCellNormal"]),
                Paragraph(f"<font size='10' color='#0284C7'><b>~{total_revalida_ads} Ads</b></font><br/><font color='#64748B'>Campanhas ativas no ar</font>", self.styles["TableCellNormal"]),
            ]
        ]
        t_kpi = Table(kpi_data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
        t_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.c_card_bg),
            ("BOX", (0, 0), (-1, -1), 0.8, self.c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_kpi)
        story.append(Spacer(1, 4))

        # Quadro de Destaque: Mundo Revalida (Nosso Benchmark)
        if our_brand:
            ob_domain = our_brand.get("domain") or "mundorevalida.com.br"
            ob_adv_id = our_brand.get("advertiser_id")
            ob_ads_url = f"https://adstransparency.google.com/advertiser/{ob_adv_id}" if ob_adv_id else f"https://adstransparency.google.com/?region=anywhere&domain={ob_domain}"
            ob_terms = [t.strip() for t in (our_brand.get("seo_top_organic_terms") or "").split(",") if t.strip()][:5]
            ob_terms_highlight = " &nbsp;•&nbsp; ".join([f"<font color='#065F46'><b>\"{t}\"</b></font>" for t in ob_terms])
            our_content = [
                Paragraph("<font color='#047857' size='9'><b>★ NOSSO BENCHMARK DE REFERÊNCIA: MUNDO REVALIDA (NÓS) • ESPECIALISTA EM REVALIDAÇÃO</b></font>", self.styles["TableCellBold"]),
                Spacer(1, 1),
                Paragraph(
                    f"• <b>Proposta de Valor & Posicionamento Estratégico:</b> {safe_text(our_brand.get('attack_front'))}<br/>"
                    f"• <b>Estimativa de Mídia Realista:</b> <font color='#B45309'><b>{safe_text(our_brand.get('estimated_monthly_spend'))}</b></font> (Hiperfoco nos médicos que prestam o Revalida INEP)<br/>"
                    f"• <b>Autoridade & SEO:</b> DR {our_brand.get('domain_reputation_score') or 44} | ~650 palavras indexadas | ~1.800 backlinks | <b>Termos dominantes:</b> {ob_terms_highlight}<br/>"
                    f"• <b>Canais Oficiais Clicáveis:</b> "
                    f"<a href='https://mundorevalida.com.br' color='#0284C7'><u>Site mundorevalida.com.br ↗</u></a> | "
                    f"<a href='https://instagram.com/{our_brand.get('instagram_user')}' color='#DB2777'><u>Instagram @{our_brand.get('instagram_user')} ↗</u></a> | "
                    f"<a href='{our_brand.get('youtube_url')}' color='#DC2626'><u>Canal YouTube ↗</u></a> | "
                    f"<a href='{ob_ads_url}' color='#047857'><u>Google Ads Transparency ↗</u></a>",
                    self.styles["TableCellNormal"]
                )
            ]
            t_our = Table([[our_content]], colWidths=[18.0 * cm])
            t_our.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_emerald_light),
                ("BOX", (0, 0), (-1, -1), 1.0, self.c_emerald),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t_our)
            story.append(Spacer(1, 5))

        # Tabela Geral Comparativa de Todos os 16 Concorrentes
        story.append(Paragraph("<b>Matriz Geral de Concorrentes Mapeados (Visão Executiva)</b>", self.styles["SectionHeading"]))
        
        matrix_rows = [
            [
                Paragraph("<b>Concorrente</b>", self.styles["TableHead"]),
                Paragraph("<b>Tier</b>", self.styles["TableHead"]),
                Paragraph("<b>Google Ads</b>", self.styles["TableHead"]),
                Paragraph("<b>DR</b>", self.styles["TableHead"]),
                Paragraph("<b>Mídia Est./mês</b>", self.styles["TableHead"]),
                Paragraph("<b>Proposta de Valor & Posicionamento</b>", self.styles["TableHead"]),
                Paragraph("<b>Link Oficial</b>", self.styles["TableHead"]),
            ]
        ]

        for c in external_comps:
            has_ads = c.get("has_google_ads") == 1
            ads_badge = "<font color='#047857'><b>Com Ads</b></font>" if has_ads else "<font color='#64748B'>Sem Ads</font>"
            site_url = c.get("website_url") or f"https://{c.get('domain')}"
            domain = c.get("domain") or ""
            link_p = Paragraph(f"<a href='{site_url}' color='#0284C7'><u>{domain[:16]} ↗</u></a>", self.styles["TableCellNormal"])
            
            matrix_rows.append([
                Paragraph(f"<b>{safe_text(c.get('name'))}</b>", self.styles["TableCellBold"]),
                Paragraph(safe_text(c.get("tier", "Especialista")), self.styles["TableCellNormal"]),
                Paragraph(ads_badge, self.styles["TableCellNormal"]),
                Paragraph(str(c.get("domain_reputation_score") or "-"), self.styles["TableCellNormal"]),
                Paragraph(safe_text(c.get("estimated_monthly_spend", "-").split("(")[0]), self.styles["TableCellNormal"]),
                Paragraph(safe_text((c.get("attack_front") or "-").split("+")[0].strip()[:65]), self.styles["TableCellNormal"]),
                link_p
            ])

        t_matrix = Table(matrix_rows, colWidths=[3.2 * cm, 1.8 * cm, 1.7 * cm, 1.0 * cm, 2.6 * cm, 5.2 * cm, 2.5 * cm])
        t_matrix.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_card_bg]),
            ("BOX", (0, 0), (-1, -1), 0.6, self.c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, self.c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 1.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ]))
        story.append(t_matrix)

        # Quebra de página: Cada concorrente terá sua página exclusiva a seguir!
        story.append(PageBreak())

        # =========================================================================
        # PÁGINAS 2 A 17: DOSSIÊ INDIVIDUAL EXCLUSIVO POR CONCORRENTE
        # =========================================================================
        for idx, c in enumerate(external_comps, start=1):
            comp_id = c.get("id")
            name = c.get("name")
            tier = c.get("tier", "Especialista")
            domain = c.get("domain") or ""
            root_domain = c.get("root_domain") or domain
            has_distinct_root = root_domain and domain and root_domain.lower() != domain.lower()
            site_url = c.get("website_url") or f"https://{domain}"
            has_ads = c.get("has_google_ads") == 1
            revalida_ads = c.get("revalida_ads_count") or 0
            other_ads = c.get("other_themes_ads_count") or 0
            total_approx = c.get("google_ads_count_approx") or (revalida_ads + other_ads)
            revalida_pct = round((revalida_ads / total_approx) * 100) if total_approx > 0 else 0
            legal_name = c.get("legal_name") or name
            cnpj = c.get("cnpj") or "Sob Consulta"
            spend = c.get("estimated_monthly_spend") or "R$ 2.000 - 5.000/mês"
            attack_front = c.get("attack_front") or "Não informado"
            kw_list = [k.strip() for k in (c.get("google_ads_keywords") or "").split(",") if k.strip()]
            user_terms = [t.strip() for t in (c.get("user_search_terms") or "").split(",") if t.strip()]
            organic_terms = [o.strip() for o in (c.get("seo_top_organic_terms") or "").split(",") if o.strip()]
            bio_links = [b.strip() for b in (c.get("bio_links") or "").split(",") if b.strip()]

            # Build Google Ads Transparency URLs
            advertiser_id = c.get("advertiser_id")
            if advertiser_id:
                direct_ads_url = f"https://adstransparency.google.com/advertiser/{advertiser_id}"
            else:
                direct_ads_url = f"https://adstransparency.google.com/?region=anywhere&domain={urllib.parse.quote(domain)}"
            subdomain_ads_url = direct_ads_url
            root_ads_url = f"https://adstransparency.google.com/?region=anywhere&domain={urllib.parse.quote(root_domain)}"
            legal_ads_url = f"https://adstransparency.google.com/?region=anywhere&term={urllib.parse.quote(legal_name)}"

            dr_label = c.get('domain_reputation_label') or f"DR {c.get('domain_reputation_score') or '-'}"

            # 1. Header do Concorrente
            status_tag = "<font color='#047857'><b>● MÍDIA ATIVA NO GOOGLE ADS</b></font>" if has_ads else "<font color='#64748B'><b>○ SEM ANÚNCIOS NO GOOGLE</b></font>"
            header_content = [
                Paragraph(f"<font color='#64748B'>DOSSIÊ AUDITADO #{idx:02d} DE {len(external_comps):02d} • REVALIDA INEP</font>", self.styles["CoverPreTitle"]),
                Paragraph(f"<b>{safe_text(name)}</b>", self.styles["CompPageTitle"]),
                Spacer(1, 1),
                Paragraph(
                    f"{status_tag} &nbsp;|&nbsp; "
                    f"<b>Tier:</b> {safe_text(tier)} &nbsp;|&nbsp; "
                    f"<b>Autoridade de Domínio:</b> <font color='#4338CA'><b>{safe_text(dr_label)}</b></font>",
                    self.styles["CompBadge"]
                )
            ]
            t_comp_header = Table([[header_content]], colWidths=[18.0 * cm])
            t_comp_header.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_emerald_light if has_ads else self.c_card_bg),
                ("BOX", (0, 0), (-1, -1), 0.8, self.c_emerald if has_ads else self.c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t_comp_header)
            story.append(Spacer(1, 2))

            # DESTAQUE MÁXIMO: ÍNDICE DE RELEVÂNCIA NO REVALIDA INEP
            is_pure_revalida = (
                comp_id in ["hardwork_revalida", "bastidores_revalida", "revalideii", "revalida_360", "revmed_mentoria", "medtwins_revalida", "alphamed_revalida", "pense_revalida"] 
                or (revalida_pct >= 75)
            )
            revalida_stars = "★★★★★" if is_pure_revalida else "★★★☆☆"
            revalida_badge_color = "#047857" if is_pure_revalida else "#0284C7"
            revalida_focus_label = (
                "FOCO 100% ESPECIALISTA NO REVALIDA INEP" 
                if is_pure_revalida else 
                f"PORTFÓLIO MISTO (~{revalida_pct}% Revalida vs ~{100-revalida_pct}% Residência Médica)"
            )
            revalida_exam_stage = (
                "<b>Frentes de Prova:</b> 🎯 2ª Fase Prática (Estações Clínicas & Simulação Realística) + 1ª Fase Teórica"
                if comp_id in ["revalideii", "revalida_360", "revmed_mentoria", "alphamed_revalida"] else
                "<b>Frentes de Prova:</b> 📚 Ambas as Fases (Extensivo Teórico 1ª Fase + Mentoria Prática 2ª Fase)"
            )

            revalida_box_content = [
                Paragraph(
                    f"<font color='{revalida_badge_color}'><b>★ RELEVÂNCIA NO REVALIDA: {revalida_stars} {revalida_focus_label}</b></font><br/>"
                    f"<font color='#334155'>{revalida_exam_stage}</font>",
                    self.styles["RevalidaScoreBox"]
                )
            ]
            t_revalida_score = Table([[revalida_box_content]], colWidths=[18.0 * cm])
            t_revalida_score.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_emerald_light if is_pure_revalida else self.c_bg_blue_light),
                ("BOX", (0, 0), (-1, -1), 0.8, self.c_emerald if is_pure_revalida else self.c_blue),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t_revalida_score)
            story.append(Spacer(1, 3))

            # 2. Central de Pareamento & Links Clicáveis
            story.append(Paragraph("<b>1. Central de Pareamento Google Ads & Links Oficiais Clicáveis</b>", self.styles["SectionHeading"]))
            
            links_row = [
                Paragraph(f"<b>Website Oficial:</b><br/><a href='{site_url}' color='#0284C7'><u>{domain} ↗</u></a>", self.styles["TableCellNormal"]),
                Paragraph(f"<b>Ads no Google ({domain}):</b><br/><a href='{direct_ads_url}' color='#047857'><u>{('Ver Criativos (ID Verificado) ↗' if advertiser_id else 'Abrir Ads Transparency ↗')}</u></a>", self.styles["TableCellNormal"]),
                Paragraph(
                    f"<b>Pesquisa por Razão Social:</b><br/><a href='{legal_ads_url}' color='#0369A1'><u>Buscar Entidade no Google ↗</u></a>"
                    if not has_distinct_root else
                    f"<b>Ads por Domínio Raiz ({root_domain}):</b><br/><a href='{root_ads_url}' color='#0369A1'><u>Abrir Domínio Raiz ↗</u></a>",
                    self.styles["TableCellNormal"]
                ),
            ]

            social_links = []
            if c.get("youtube_url"):
                social_links.append(f"<a href='{c.get('youtube_url')}' color='#DC2626'><u>YouTube Oficial ↗</u></a>")
            if c.get("instagram_user"):
                social_links.append(f"<a href='https://instagram.com/{c.get('instagram_user')}' color='#DB2777'><u>Instagram @{c.get('instagram_user')} ↗</u></a>")
            if not social_links:
                social_links.append("Nenhum canal ativo registrado")

            bio_links_formatted = []
            for b in bio_links[:3]:
                b_url = b if b.startswith("http") else f"https://{b}"
                bio_links_formatted.append(f"<a href='{b_url}' color='#7E22CE'><u>{b[:28]} ↗</u></a>")

            if has_distinct_root:
                right_cell = Paragraph(f"<b>Busca por Razão Social:</b><br/><a href='{legal_ads_url}' color='#0369A1'><u>Buscar Entidade ↗</u></a>", self.styles["TableCellNormal"])
            else:
                right_cell = Paragraph("<b>Status de Pareamento:</b><br/><font color='#047857'>Auditado e Mapeado</font>", self.styles["TableCellNormal"])

            links_grid = [
                links_row,
                [
                    Paragraph(f"<b>Canais & Redes Sociais:</b><br/>{' | '.join(social_links)}", self.styles["TableCellNormal"]),
                    Paragraph(f"<b>Links Rastreados em Bios/LPs:</b><br/>{' | '.join(bio_links_formatted) if bio_links_formatted else 'Portal principal'}", self.styles["TableCellNormal"]),
                    right_cell
                ]
            ]
            t_links = Table(links_grid, colWidths=[6.0 * cm, 6.0 * cm, 6.0 * cm])
            t_links.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, self.c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, self.c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_links)
            story.append(Spacer(1, 3))

            # 3. Dados Corporativos, Fiscais e Estimativa de Gasto
            story.append(Paragraph("<b>2. Metadados Fiscais, Registro na Receita Federal & Investimento de Mídia</b>", self.styles["SectionHeading"]))
            
            corp_data = [
                [
                    Paragraph(f"<b>Razão Social Oficial:</b> {safe_text(legal_name)}", self.styles["TableCellNormal"]),
                    Paragraph(f"<b>CNPJ Oficial:</b> <font color='#0369A1'><b>{safe_text(cnpj)}</b></font>", self.styles["TableCellNormal"]),
                ],
                [
                    Paragraph(f"<b>Investimento Estimado de Mídia (Real):</b> <font color='#B45309'><b>{safe_text(spend)}</b></font>", self.styles["TableCellNormal"]),
                    Paragraph(
                        f"<b>Volume de Conteúdo:</b> YouTube: {safe_text(c.get('content_volume_youtube', '-').split('(')[0])} | TikTok: {safe_text(c.get('content_volume_tiktok', '-').split('(')[0])}",
                        self.styles["TableCellNormal"]
                    )
                ]
            ]
            t_corp = Table(corp_data, colWidths=[10.5 * cm, 7.5 * cm])
            t_corp.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_card_bg),
                ("BOX", (0, 0), (-1, -1), 0.6, self.c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, self.c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_corp)
            story.append(Spacer(1, 3))

            # 4. Proposta de Valor & Posicionamento Estratégico
            story.append(Paragraph("<b>3. Proposta de Valor & Posicionamento Estratégico</b>", self.styles["SectionHeading"]))
            attack_p = Paragraph(f"<b>Posicionamento Central:</b> {safe_text(attack_front)}", self.styles["BodySmall"])
            t_attack = Table([[attack_p]], colWidths=[18.0 * cm])
            t_attack.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, self.c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_attack)
            story.append(Spacer(1, 3))

            # 5. Auditoria de Google Ads & Segregação de Temas
            story.append(Paragraph("<b>4. Auditoria Forense de Google Ads & Segregação de Temas</b>", self.styles["SectionHeading"]))
            
            kw_highlight = " &nbsp;•&nbsp; ".join([f"<font color='#0369A1'><b>\"{k}\"</b></font>" for k in kw_list[:8]]) if kw_list else "Termos institucionais"
            user_terms_highlight = " &nbsp;•&nbsp; ".join([f"<font color='#0F172A'><b>\"{t}\"</b></font>" for t in user_terms])

            if has_ads:
                ads_analysis_text = (
                    f"• <b>Divisão de Campanhas:</b> 🎯 Revalida INEP: ~{revalida_ads} anúncios ({revalida_pct}%) | 🏢 Outros Temas: ~{other_ads} anúncios ({100-revalida_pct}%)<br/>"
                    f"• <b>Outros Temas Atacados:</b> {safe_text(c.get('other_themes_description') or 'Residência Médica R1/R3 e Concursos')}<br/>"
                    f"• <b>Palavras-Chave Compradas no Leilão:</b> {kw_highlight}<br/>"
                    f"• <b>Onde os Anúncios Aparecem:</b> {safe_text(c.get('google_ads_placements') or 'Google Search e YouTube')}<br/>"
                    f"• <b>O que os Candidatos Realmente Pesquisam ({len(user_terms)} termos):</b> {user_terms_highlight}"
                )
            else:
                ads_analysis_text = (
                    f"• <b>Estratégia 100% Fora do Google Ads:</b> Este concorrente não compra leilão de Google Search ou YouTube Ads para o Revalida.<br/>"
                    f"• <b>Canais de Captação Alternativos:</b> Captação orgânica via redes sociais, YouTube, comunidades de WhatsApp/Telegram e polos presenciais.<br/>"
                    f"• <b>O que os Candidatos Pesquisam no Google & YouTube ({len(user_terms)} termos):</b> {user_terms_highlight}"
                )

            t_ads_box = Table([[Paragraph(ads_analysis_text, self.styles["BodySmall"])]], colWidths=[18.0 * cm])
            t_ads_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_emerald_light if has_ads else self.c_card_bg),
                ("BOX", (0, 0), (-1, -1), 0.6, self.c_emerald if has_ads else self.c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t_ads_box)
            story.append(Spacer(1, 3))

            # 6. Autoridade de Domínio & SEO Orgânico
            story.append(Paragraph("<b>5. Auditoria de SEO & Termos de Maior Tráfego no Google</b>", self.styles["SectionHeading"]))
            
            organic_terms_highlight = " &nbsp;•&nbsp; ".join([f"<font color='#065F46'><b>\"{t}\"</b></font>" for t in organic_terms]) if organic_terms else "revalida inep, preparatorio revalida"

            seo_content = (
                f"• <b>Autoridade de Domínio:</b> {safe_text(dr_label)} | "
                f"<b>Palavras Indexadas:</b> {safe_text(c.get('seo_keywords_count') or '~1.000')} | "
                f"<b>Perfil de Backlinks:</b> {safe_text(c.get('seo_backlinks_estimate') or '~3.000')}<br/>"
                f"• <b>Termos de Maior Tráfego Orgânico no Google (Lista Completa • {len(organic_terms)} termos):</b><br/>"
                f"{organic_terms_highlight}"
            )
            t_seo = Table([[Paragraph(seo_content, self.styles["BodySmall"])]], colWidths=[18.0 * cm])
            t_seo.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_emerald_light),
                ("BOX", (0, 0), (-1, -1), 0.6, self.c_emerald),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t_seo)
            story.append(Spacer(1, 3))

            # 7. Amostra de Criativos Auditados de Revalidação
            comp_ads = [a for a in all_ads if a.get("competitor_id") == comp_id]
            displayed_ads = comp_ads[:4]
            story.append(Paragraph(f"<b>6. Amostra de Criativos Auditados de Revalidação Médica ({len(displayed_ads)} de {len(comp_ads)} no banco{' • +' + str(len(comp_ads)-len(displayed_ads)) + ' adicionais' if len(comp_ads) > 4 else ''})</b>", self.styles["SectionHeading"]))
            
            if displayed_ads:
                ad_cells = []
                for ad in displayed_ads:
                    target = ad.get("target_url") or ""
                    link_dest = f"<a href='{target}' color='#0284C7'><u>{target[:32]} ↗</u></a>" if target else "Página de Captura"
                    ad_text = (
                        f"<b>[{safe_text(ad.get('ad_format', 'TEXT'))}] {safe_text(ad.get('headline'))}</b><br/>"
                        f"{safe_text(ad.get('body_text'))}<br/>"
                        f"<font color='#64748B'>Status: {safe_text(ad.get('first_seen', 'Ativo'))} | Destino: {link_dest}</font>"
                    )
                    ad_cells.append(Paragraph(ad_text, self.styles["BodySmall"]))

                # Pair into rows of 2 columns
                grid_rows = []
                for i in range(0, len(ad_cells), 2):
                    row = [ad_cells[i]]
                    if i + 1 < len(ad_cells):
                        row.append(ad_cells[i + 1])
                    else:
                        row.append(Paragraph("", self.styles["BodySmall"]))
                    grid_rows.append(row)

                # Banner link row spanning full width
                grid_rows.append([
                    Paragraph(f"<font color='#047857'><b>Google Ads Transparency Center:</b></font> <a href='{direct_ads_url}' color='#047857'><u>Acessar todos os criativos e histórico oficial deste anunciante no Google ↗</u></a>", self.styles["BodySmall"]),
                    Paragraph("", self.styles["BodySmall"])
                ])

                t_creatives = Table(grid_rows, colWidths=[9.0 * cm, 9.0 * cm])
                t_creatives.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.c_border),
                    ("INNERGRID", (0, 0), (-1, -2), 0.4, self.c_border),
                    ("SPAN", (0, -1), (1, -1)),
                    ("BACKGROUND", (0, -1), (1, -1), self.c_bg_emerald_light),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t_creatives)
            else:
                empty_msg = (
                    f"Consulte criativos dinâmicos em tempo real no Google Ads Transparency Center: "
                    f"<a href='{direct_ads_url}' color='#047857'><u>Abrir Painel Oficial do Google ↗</u></a>"
                    if has_ads else
                    "Nenhum anúncio veiculado no Google Ads. Player atua 100% em canais orgânicos, SEO e redes sociais."
                )
                t_empty = Table([[Paragraph(empty_msg, self.styles["BodySmall"])]], colWidths=[18.0 * cm])
                t_empty.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), self.c_card_bg),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.c_border),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t_empty)

            # Quebra de página estrita após cada concorrente (exceto no último)
            if idx < len(external_comps):
                story.append(PageBreak())

        # Constrói o PDF com o NumberedCanvas para paginação perfeita
        doc.build(story, canvasmaker=NumberedCanvas)
        return target_path


if __name__ == "__main__":
    focus_arg = sys.argv[1] if len(sys.argv) > 1 else "master"
    gen = CompetitorReportGenerator()
    out = gen.generate_pdf(focus=focus_arg)
    print(f"Dossiê Executivo PDF gerado com sucesso em: {out}")
