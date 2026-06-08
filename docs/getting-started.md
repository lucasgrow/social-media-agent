# Getting Started

Tudo que você precisa pra rodar o `social-media-agent` do zero. Cada comando é copy-paste.

## O que é

Um agente conversacional (skill do Codex, com compatibilidade Claude Code) que produz posts de Instagram pra múltiplos perfis. Você cola um link (IG/Twitter/YouTube) ou descreve o post, escolhe o perfil, e ele gera a peça on-brand usando OpenAI — com brand kit, voz e learnings de cada perfil.

Não é um app web. Não tem servidor, banco, nem frontend. **O estado são arquivos no disco** e a interface é a conversa no Codex ou no Claude Code.

## Pré-requisitos

| Ferramenta | Versão | Como checar |
|---|---|---|
| Python | ≥ 3.11 | `python3 --version` |
| Codex | atual | abra uma sessão dentro do repo |
| Claude Code | atual | `claude --version` (opcional, compatibilidade antiga) |
| yt-dlp | qualquer | `yt-dlp --version` (opcional — só pra ingestão de links) |
| Chave OpenAI | — | precisa de acesso aos modelos `gpt-image-2-2026-04-21` (geração) e `gpt-5` (visão/audit/voice). Confira no dashboard da OpenAI (platform.openai.com) se sua org tem acesso a esses |

> Testado em **macOS** (zsh + Homebrew). Em Linux o fluxo é o mesmo trocando `brew` pelo gerenciador da distro.

yt-dlp no macOS: `brew install yt-dlp`.

## Instalação (uma vez)

```bash
git clone <repo-url> social-media-agent
cd social-media-agent
./install.sh
```

O `install.sh` faz, de forma idempotente (pode rodar 2x sem quebrar):
1. Cria o virtualenv `.venv/`
2. Instala o pacote editável + deps (`pip install -e .` → `requests`, `pyyaml`, `Pillow` + dev: `pytest`, `ruff`)
3. Cria os symlinks `~/.codex/skills/social-media-agent` e `~/.claude/skills/social-media-agent`
4. Copia `.env.example` → `.env` se não existir
5. Avisa se `yt-dlp` não está instalado (não-fatal)
6. Provisiona e sobe o **Cobalt local** (ingest de imagem/carrossel do IG) — clona da fonte e inicia em `127.0.0.1:9000`. Precisa de `node` + `pnpm`.

### Cobalt local (cross-platform)

A ingestão de carrosséis/imagens do Instagram usa o Cobalt — o yt-dlp só pega vídeo. O Cobalt roda **localmente, provisionado por este repo** (sem depender de nenhum outro projeto). Entrypoint cross-platform (Win/Mac/Linux):

```bash
.venv/bin/python -m social_media_agent.cobalt ensure   # sobe se não estiver no ar (o setup já roda isso)
.venv/bin/python -m social_media_agent.cobalt status   # checa saúde
.venv/bin/python -m social_media_agent.cobalt stop      # derruba
```

A fonte do Cobalt é clonada em `.cobalt/` (gitignored). No **Windows**, rode a linha `ensure` acima após o setup. Sem `node`/`pnpm`, o comando dá erro claro com instruções de instalação.

## Configurar as chaves

Edite o `.env` na raiz do repo:

```bash
# obrigatória
OPENAI_API_KEY=sk-proj-...

# opcionais
GEMINI_API_KEY=AIza...
TWITTER_API_KEY=...
# Cobalt: default é a instância local 127.0.0.1:9000 (provisionada pelo repo).
# Só defina para apontar a outra instância.
# COBALT_API_URL=http://127.0.0.1:9000/

# opcional — só se você rodar a skill de FORA da pasta do repo
# SOCIAL_MEDIA_AGENT_HOME=/path/to/social-media-agent
```

> O `.env` está no `.gitignore` — nunca é commitado.
> `SOCIAL_MEDIA_AGENT_HOME` só é necessário se você invocar a skill de um diretório fora do repo; rodando dentro do repo, é auto-detectado.

## Verificar que funcionou

```bash
# 1. testes verdes
./scripts/check.sh
# esperado: "ruff lint ... pytest ... passed ... OK: all checks passed"

# 2. skill Codex alcançável globalmente
test -f ~/.codex/skills/social-media-agent/SKILL.md && echo "codex skill OK"

# 3. skill Claude Code alcançável globalmente (compatibilidade)
test -f ~/.claude/skills/social-media-agent/SKILL.md && echo "skill OK"

# 4. perfis existentes
ls profiles/
# esperado: example-brand
```

Se os 4 passarem, está pronto.

## Primeiro uso (no Codex)

Abra o Codex dentro do repo (`cd social-media-agent`).

O `AGENTS.md` dá o contexto do projeto e a skill global `social-media-agent` cobre os workflows. Exemplos:

```
faz um post pra example-brand com esse link https://www.instagram.com/p/XXXX/
```
```
qual a legenda desse post?
```
```
roda audit em example-brand
```

## Uso legado (Claude Code)

Abra o Claude Code DENTRO do repo (`cd social-media-agent && claude`) — ou de qualquer lugar, já que o symlink deixa a skill global.

Aí é conversa normal. Exemplos:

```
faz um post pra example-brand com esse link https://www.instagram.com/p/XXXX/
```
```
qual a legenda desse post?
```
```
/social-media-agent audit example-brand
```

O guia completo de comandos e workflows está em [`docs/usage.md`](usage.md).

## O que você vai ver no disco

Cada post gerado vira uma pasta auto-contida:

```
profiles/example-brand/posts/2026-06/01-meu-post/
├── brief.md                # o que o post deve dizer (você revisa antes de gerar)
├── source/                 # original baixado do link
├── craft.py                # script de geração (gerado pela skill)
├── outputs/v1/feed.png     # a peça gerada (v2, v3... nas iterações)
├── outputs/final/          # versão aprovada
├── caption.md              # legenda
└── decisions.md            # log de cada iteração (prompt + reação)
```

Os PNGs gerados (`outputs/`) e os downloads (`source/`) estão no `.gitignore` — não incham o repo.

## Próximos passos

- [`docs/usage.md`](usage.md) — todos os comandos + workflows com exemplos
- [`docs/architecture.md`](architecture.md) — como o sistema é construído por dentro
