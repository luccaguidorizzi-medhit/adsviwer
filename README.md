# Competitor Intelligence & Monitoring System
**Autor:** Lagana Flow  
**Arquitetura:** Sandbox Híbrida Isolada + Ponte MCP (Supabase, Gemini API, Google Workspace)

---

## 🛡️ Camada de Segurança e Isolamento

Este projeto foi construído sob o princípio de **Defesa em Profundidade**:
1. **Ambiente Virtual Isolado (`.venv-isolated`):** Todas as dependências são fixadas e auditadas contra CVEs e vulnerabilidades de supply chain via `pip-audit`.
2. **Quarentena e Path Jail:** O módulo `SecuritySanitizer` impede que qualquer script ou dado bruto acesse caminhos fora do diretório `data/` (bloqueio de Directory Traversal).
3. **Proteção Anti-Prompt Injection (OWASP LLM01):** Todo texto e HTML de páginas e anúncios é higienizado e filtrado antes de ser disponibilizado para agentes de IA ou bancos de dados.

---

## 🚀 Como Usar

### 1. Configurar Concorrentes
Edite o arquivo `config/competitors.json` e adicione seus concorrentes:

```json
{
  "id": "meu_concorrente",
  "name": "Nome da Empresa",
  "website_url": "https://concorrente.com",
  "landing_pages": [
    "https://concorrente.com/oferta-especial"
  ],
  "instagram": {
    "username": "perfil_concorrente"
  },
  "meta_ads": {
    "search_keyword": "Nome da Empresa"
  }
}
```

### 2. Comandos Principais

Ative o ambiente virtual ou utilize o executável do ambiente isolado:

```powershell
# Ver status dos concorrentes cadastrados
.\.venv-isolated\Scripts\python.exe main.py --status

# Rodar coleta de todos os concorrentes
.\.venv-isolated\Scripts\python.exe main.py --run-all

# Rodar coleta apenas para um concorrente específico
.\.venv-isolated\Scripts\python.exe main.py --competitor meu_concorrente

# Executar auditoria de vulnerabilidades
.\.venv-isolated\Scripts\python.exe main.py --audit

# Listar projetos vizinhos acessíveis na pasta scratch
.\.venv-isolated\Scripts\python.exe main.py --list-projects
```

---

## 🔗 Integração com MCPs e Projetos Vizinhos

O módulo `src/bridge/mcp_connector.py` permite:
* Exportar os dados higienizados para o **Supabase** via MCP `supabase-thiago`.
* Utilizar o **Gemini API** para gerar análises comparativas de criativos e copies de anúncios.
* Compartilhar dados com projetos em `scratch/` (como `sales-clarity` e `migracao-landing-pages`).
