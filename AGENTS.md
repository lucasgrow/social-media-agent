# social-media-agent — Codex Instructions

## Projeto

`social-media-agent` é um meta-projeto file-based para produzir posts de Instagram por perfil. Não há servidor, banco ou frontend. O estado vive em `profiles/<name>/`, e a lógica reutilizável vive em scripts Python puros.

Este repo começou como uma skill do Claude Code, mas a implementação hoje é um pacote Python instalável e agnóstico de ferramenta. Fontes operacionais:

- `src/social_media_agent/` — implementação Python real (importável como `social_media_agent.*`), usada pelos testes e pelos `craft.py`. Nem `.claude` nem `.codex` é "dono" dela.
- `.claude/skills/social-media-agent/SKILL.md` — verdade maior operacional: driver detalhado e catálogo das funções disponíveis.
- `.codex/skills/social-media-agent/SKILL.md` — driver Codex sincronizado com a verdade maior do Claude.
- `docs/architecture.md` — mapa do sistema.
- `docs/usage.md` — workflows e comandos de uso.

Os skills em `.codex` e `.claude` devem permanecer sincronizados; edite a verdade maior em `.claude/skills/social-media-agent/SKILL.md` e replique para `.codex/skills/social-media-agent/SKILL.md`. Os dois importam o mesmo pacote. Não mova `src/social_media_agent/` sem atualizar imports, testes e `pyproject.toml`.

## Como Trabalhar

- Use Python pelo virtualenv: `.venv/bin/python`. O pacote é instalado editável (`pip install -e .`), então `from social_media_agent.<subpkg> import ...` funciona sem mexer em `sys.path`.
- Rode verificação com `./scripts/check.sh`.
- Rode `./install.sh` quando precisar recriar o venv, reinstalar o pacote e os symlinks globais de skill para Codex e Claude.
- Se estiver fora da raiz do repo, resolva o projeto por `SOCIAL_MEDIA_AGENT_HOME` ou peça o caminho ao usuário — não assuma um caminho fixo.

## Regras Operacionais

- Antes de gerar imagem, editar imagem, rodar audit ou inferir voz por LLM, confirme com o usuário porque isso pode consumir créditos.
- Sempre leia o perfil relevante antes de produzir: `brand-kit/DESIGN.md`, `VOICE.md` se existir, `learnings.md` se existir, e o post ativo quando houver.
- Nunca sobrescreva `outputs/final/`. Iterações entram em `outputs/vN/`.
- Registre decisões/iterações em `decisions.md` quando mexer em posts.
- Depois de gerar PNG local, inspecione o arquivo visualmente com a ferramenta de imagem antes de afirmar qualidade.
- Preserve os termos do usuário em copy e fluxo de produto.

## Contexto De Perfil

Perfil canônico:

```text
profiles/<name>/
├── brand-kit/DESIGN.md
├── brand-kit/pages/
├── VOICE.md
├── assets/
├── references/
├── posts/YYYY-MM/NN-slug/
└── learnings.md
```

Perfil de exemplo incluído: `example-brand`. Crie os seus em `profiles/<name>/`.
