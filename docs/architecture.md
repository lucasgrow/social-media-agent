# Architecture

Visão de 10.000 pés do `social-media-agent`. Se você ler só este arquivo, entende o que o sistema faz, como é construído e por quê.

## Overview

Um repo monolítico que é, ao mesmo tempo, uma skill do Codex/Claude Code e um meta-projeto de perfis. A skill dá a UX (conversa + comandos); os perfis são pastas auto-contidas com identidade, voz e posts. Não há servidor nem banco — **o estado são arquivos no disco**, e a "lógica de negócio" são funções Python puras que o agente invoca via Bash.

## Diagrama do sistema

```
┌─────────────────────────────────────────────────────────────┐
│ CODEX / CLAUDE CODE (conversa)                               │
│   AGENTS.md + SKILL.md  →  drivers finos (.codex / .claude) │
└───────────────────────────┬─────────────────────────────────┘
                            │ importa o pacote instalado
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ src/social_media_agent/  (pacote instalável, agnóstico)     │
│                                                             │
│   brand/      brand_loader · prompt_builder                 │
│   engines/    openai_gpt_image_2 · openai_vision            │
│   ingest/     yt_dlp                                        │
│   render/     image_renderer                                │
│   post/       discover_profile · slug · bootstrap ·         │
│               materialize · caption · decisions_log         │
│   audit/      post_scanner · decisions_parser ·            │
│               drift_detector · pattern_extractor ·          │
│               learnings_writer · audit                      │
│   grounding/  extract · search · verify · ground            │
│   utils/      env                                           │
└───────────────────────────┬─────────────────────────────────┘
                            │ lê/escreve
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ profiles/<nome>/   (estado — arquivos)                      │
│   brand-kit/ · VOICE.md · assets/ · references/ ·          │
│   posts/AAAA-MM/NN-slug/ · learnings.md                     │
└─────────────────────────────────────────────────────────────┘
```

## Subsistemas

Cada um é um subpacote de `social_media_agent` (em `src/social_media_agent/`), com funções puras (sem estado de módulo, sem globais) — fácil de testar e de estender. Importável como `from social_media_agent.<subpkg> import ...` após `pip install -e .`.

| Pacote | Responsabilidade | Funções-chave |
|---|---|---|
| `brand` | Carregar identidade + montar prompt | `parse_design_md`, `parse_voice_md`, `list_brand_pages`, `build_prompt` |
| `engines` | Falar com APIs de IA | `openai_gpt_image_2.generate/edit`, `openai_vision.analyze_image/extract_structured` |
| `ingest` | Baixar mídia de links | `yt_dlp.fetch` |
| `render` | Salvar bytes + preview | `image_renderer.save`, `preview_grid` |
| `post` | Ciclo de vida do post | `discover_profile`, `auto_slug`, `bootstrap_post`, `materialize_craft_py`, `create_caption_skeleton`, `decisions_log` |
| `audit` | Loop de aprendizado cross-post | `scan_posts`, `parse_decisions`, `detect_drift`, `extract_patterns`, `write_learnings`, `run_audit` |
| `grounding` | Ancorar sujeitos reais em refs reais | `extract_subjects`, `serper_image_search`, `verify_ref`, `register_ref`, `collect_grounded_refs` |
| `utils` | Helpers | `env.load_env`, `env.find_repo_root` |

## Schema do perfil (canônico)

```
profiles/<nome>/
├── brand-kit/
│   ├── DESIGN.md     # OBRIGATÓRIO — YAML frontmatter (máquina) + markdown rico (humano)
│   └── pages/        # PNGs — SEMPRE anexados como image refs nos prompts (se houver)
├── VOICE.md          # OBRIGATÓRIO — YAML: tone, go_words, no_go_words, contexts
├── assets/           # opcional — logo, foto de perfil, ícones, cenas reutilizáveis
├── references/       # opcional — vault de inspirações
├── posts/AAAA-MM/NN-slug/   # criado no 1º post
└── learnings.md      # criado pelo audit (não existe até rodar `audit`)
```

> Mínimo válido = `brand-kit/DESIGN.md`. O resto aparece sob demanda. O perfil de exemplo `example-brand` traz a estrutura canônica completa.

`DESIGN.md` frontmatter relevante: `palette`, `fonts`, `mark` (`type: none` quando não há logo — evita o modelo inventar emblema), `formats_enabled`, `default_engine`, `principles`, `anti_refs`.

## O pipeline de geração

```
brief.md  →  build_prompt(design, voice, brand_pages, extra_refs, learnings)
                  │  (texto + lista de image refs, na ordem: source → brand pages)
                  ▼
          openai_gpt_image_2.generate/edit
                  ▼
          image_renderer.save  →  outputs/vN/feed.png
```

`build_prompt` é o coração da qualidade: injeta paleta + tipografia + princípios + anti-refs + regra de `mark.type` + voz + **top-N learnings** do perfil, e anexa as `brand-kit/pages/` como referências visuais.

## O loop de aprendizado

```
produzir post → decisions.md (cada iteração)
                     │
            audit:  scan_posts → drift_detector (vision vs brand pages)
                              → decisions_parser → pattern_extractor (LLM)
                              → learnings_writer → learnings.md
                     │
            próximo post: build_prompt injeta os learnings → erro não se repete
```

É o diferencial do projeto — memória cross-post explícita.

## Decisões-chave

| Decisão | Escolha | Por quê |
|---|---|---|
| Repo único | Skill + perfis + docs no mesmo git | 1 unidade de versionamento; clona e roda; hand-off pra cliente |
| Estado em arquivos | Sem banco, sem servidor | Simplicidade; tudo inspecionável; gitável por perfil |
| Funções puras | Adapters sem estado | Testável (suíte pytest), fácil de estender |
| brand-kit/pages como image refs | Sempre anexar PNGs do brand no prompt | Sem isso o modelo inventa elementos (ex: um emblema/monograma que não existe) |
| `mark.type: none` explícito | Schema declara ausência de logo | Trava o modelo de inventar emblema |
| Schema canônico de perfil | Toda conta segue o mesmo layout | Reuso, hand-off e aprendizado cross-post |
| Vídeo via adapter externo | Phase 5d chama um toolkit de vídeo externo (template `twitter-style-9x16`), não reimplementa | Stack HTML+Chrome+ffmpeg já existe e funciona (com legenda burned-in via SRT). Adapter, igual yt-dlp pra ingest |

## Como o sistema cresceu (fases)

| Fase | Entrega | Tag |
|---|---|---|
| 1 | Scaffold (repo, install, smoke tests) | `phase-1-scaffold-complete` |
| 2 | Vertical slice (4 adapters → PNG real) | `phase-2-vertical-slice-complete` |
| 3 | Workflows conversacionais A/B/C/D | `phase-3-conversational-complete` |
| 4 | Audit + learning loop | `phase-4-audit-loop-complete` |
| 6 | Gemini engine + grounding | `phase-6-complete` |
| roadmap | cobalt/twitter ingest · vídeo | — |

## Stack

Python 3.11+ · `requests` (HTTP) · `pyyaml` (frontmatter) · `Pillow` (preview grid) · `pytest`/`ruff` (gate). yt-dlp via subprocess. OpenAI `gpt-image-2` (geração) + visão (audit). Sem framework web, sem DB.

## Onde ler mais

- [getting-started.md](getting-started.md) — instalar + primeiro uso
- [usage.md](usage.md) — comandos + workflows
- `AGENTS.md` — contexto Codex do repo
- `.claude/skills/social-media-agent/SKILL.md` — verdade maior operacional, driver detalhado + referência operacional
- `.codex/skills/social-media-agent/SKILL.md` — driver Codex sincronizado com o Claude
