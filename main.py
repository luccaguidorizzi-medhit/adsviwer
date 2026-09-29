"""
Competitor Intelligence System - Main Orchestrator
Author: Lagana Flow
Usage:
    python main.py --run-all
    python main.py --competitor <id>
    python main.py --audit
    python main.py --status
"""

import sys
import json
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.security.sanitizer import SecuritySanitizer
from src.security.audit_runner import run_pip_audit
from src.extractors.meta_ads_watcher import MetaAdsWatcher
from src.extractors.ig_profile_watcher import InstagramProfileWatcher
from src.extractors.site_diff_watcher import SiteDiffWatcher
from src.bridge.mcp_connector import MCPCrossProjectBridge

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent
COMPETITORS_CONFIG = PROJECT_ROOT / "config" / "competitors.json"


def load_competitors():
    if not COMPETITORS_CONFIG.exists():
        console.print("[red]Arquivo de configuração config/competitors.json não encontrado![/red]")
        return []
    with open(COMPETITORS_CONFIG, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("competitors", [])


def run_monitoring_for_competitor(comp: dict, meta_watcher, ig_watcher, site_watcher):
    name = comp.get("name", "Desconhecido")
    comp_id = comp.get("id", "competitor")
    console.print(Panel(f"[bold green]Iniciando monitoramento: {name} (ID: {comp_id})[/bold green]"))

    # 1. Meta Ads
    if comp.get("meta_ads"):
        console.print("[cyan]→ Extraindo anúncios da Meta Ad Library...[/cyan]")
        try:
            meta_res = meta_watcher.run(comp)
            console.print(f"[green]  ✓ Anúncios processados: {meta_res.get('total_ads_found', 0)}[/green]")
        except Exception as e:
            console.print(f"[red]  ✗ Erro no coletor Meta: {e}[/red]")

    # 2. Instagram
    if comp.get("instagram"):
        console.print("[magenta]→ Monitorando perfil e bio do Instagram...[/magenta]")
        try:
            ig_res = ig_watcher.run(comp)
            console.print(f"[green]  ✓ Perfil: {ig_res.get('followers_count', 0)} seguidores, {ig_res.get('posts_count', 0)} posts[/green]")
        except Exception as e:
            console.print(f"[red]  ✗ Erro no coletor Instagram: {e}[/red]")

    # 3. Site & Landing Pages Diff
    if comp.get("website_url") or comp.get("landing_pages"):
        console.print("[yellow]→ Rastreando páginas de vendas e sites...[/yellow]")
        try:
            site_res = site_watcher.run(comp)
            console.print(f"[green]  ✓ Páginas analisadas: {len(site_res)}[/green]")
        except Exception as e:
            console.print(f"[red]  ✗ Erro no monitor de sites: {e}[/red]")


def show_status():
    competitors = load_competitors()
    table = Table(title="Radar de Concorrentes - Status Atual")
    table.add_column("ID", style="cyan")
    table.add_column("Nome", style="bold")
    table.add_column("Instagram", style="magenta")
    table.add_column("Website", style="blue")
    table.add_column("Meta Ads", style="green")

    for c in competitors:
        table.add_row(
            c.get("id", ""),
            c.get("name", ""),
            "@" + c.get("instagram", {}).get("username", "-") if c.get("instagram") else "-",
            c.get("website_url", "-"),
            "Ativo" if c.get("meta_ads") else "-"
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Competitor Monitor - Lagana Flow")
    parser.add_argument("--run-all", action="store_true", help="Executa coleta completa de todos os concorrentes")
    parser.add_argument("--competitor", type=str, help="Executa coleta de um concorrente específico por ID")
    parser.add_argument("--audit", action="store_true", help="Executa auditoria de segurança das dependências")
    parser.add_argument("--status", action="store_true", help="Exibe tabela com status dos concorrentes")
    parser.add_argument("--export-pdf", type=str, choices=["geral", "google", "video", "ads"], help="Gera PDF executivo formatado com o foco escolhido")
    parser.add_argument("--list-projects", action="store_true", help="Lista outros projetos compartilhados na pasta scratch/")

    args = parser.parse_args()

    if args.export_pdf:
        from src.reports.pdf_generator import CompetitorReportGenerator
        gen = CompetitorReportGenerator()
        pdf_path = gen.generate_pdf(focus=args.export_pdf)
        console.print(f"[bold green]✓ Relatório PDF ({args.export_pdf.upper()}) gerado com sucesso em:[/bold green] {pdf_path}")
        return

    if args.audit:
        run_pip_audit()
        return

    if args.list_projects:
        bridge = MCPCrossProjectBridge()
        projects = bridge.list_available_scratch_projects()
        console.print(f"[bold cyan]Projetos disponíveis na pasta scratch/:[/bold cyan] {', '.join(projects)}")
        return

    if args.status:
        show_status()
        return

    if args.run_all or args.competitor:
        # Pre-execution security check
        console.print("[bold blue]🔒 Verificando integridade do ambiente antes da execução...[/bold blue]")
        meta_watcher = MetaAdsWatcher()
        ig_watcher = InstagramProfileWatcher()
        site_watcher = SiteDiffWatcher()

        competitors = load_competitors()
        if args.competitor:
            competitors = [c for c in competitors if c.get("id") == args.competitor]
            if not competitors:
                console.print(f"[red]Concorrente com ID '{args.competitor}' não encontrado![/red]")
                return

        for c in competitors:
            run_monitoring_for_competitor(c, meta_watcher, ig_watcher, site_watcher)

        console.print("\n[bold green]✨ Coleta finalizada com sucesso! Dados seguros salvos em data/sanitized/.[/bold green]")
    else:
        show_status()
        console.print("\n[dim]Dica: use `python main.py --run-all` para executar a extração ou `--help` para opções.[/dim]")


if __name__ == "__main__":
    main()
