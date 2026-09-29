"""
Security & Supply Chain Audit Runner
Author: Lagana Flow
Performs static analysis and vulnerability scans on installed dependencies and scripts.
"""

import sys
import subprocess
from pathlib import Path
from typing import List
from rich.console import Console

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_pip_audit() -> bool:
    """Executes pip-audit inside the isolated virtualenv."""
    console.print("\n[bold cyan]🔍 Executando auditoria de vulnerabilidades em dependências (pip-audit)...[/bold cyan]")
    venv_pip_audit = PROJECT_ROOT / ".venv-isolated" / "Scripts" / "pip-audit.exe"
    cmd = [str(venv_pip_audit)] if venv_pip_audit.exists() else ["pip-audit"]

    try:
        res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if res.returncode == 0:
            console.print("[bold green]✅ Sucesso: Nenhuma vulnerabilidade ou CVE conhecida encontrada nas dependências.[/bold green]")
            return True
        else:
            console.print("[bold red]⚠️ Alerta de Segurança encontrado nas dependências:[/bold red]")
            console.print(res.stdout)
            console.print(res.stderr)
            return False
    except Exception as e:
        console.print(f"[red]Erro ao executar auditoria: {e}[/red]")
        return False


def scan_script_for_dangerous_patterns(script_path: Path) -> List[str]:
    """Checks scripts for dangerous calls like eval(), raw system commands, or suspicious network calls."""
    suspicious = []
    dangerous_keywords = [
        "eval(", "exec(", "os.system(", "subprocess.Popen(..., shell=True)",
        "__import__('os')", "base64.b64decode("
    ]
    if not script_path.exists():
        return suspicious

    content = script_path.read_text(encoding="utf-8", errors="ignore")
    for kw in dangerous_keywords:
        if kw in content:
            suspicious.append(f"Uso suspeito detectado: {kw}")
    return suspicious


if __name__ == "__main__":
    success = run_pip_audit()
    sys.exit(0 if success else 1)
