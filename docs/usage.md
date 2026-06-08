# Usage — Guia anti-burro

Como usar o `social-media-agent` no dia a dia. 90% é conversa; alguns comandos são estruturais.

> Pré-requisito: já rodou `./install.sh` e preencheu o `.env`. Veja [getting-started.md](getting-started.md).

---

## Modelo mental em 1 minuto

- **Perfil** = uma conta de Instagram. Tem identidade (`brand-kit/DESIGN.md`), voz (`VOICE.md`), assets, referências e posts. Vive em `profiles/<nome>/`.
- **Post** = uma unidade de trabalho. Pasta auto-contida com brief, source, outputs versionados, caption, log.
- **Learnings** = o que o perfil aprendeu cruzando posts (`learnings.md`). Alimenta os próximos prompts.
- Você **conversa** pra produzir/editar/legendar. Você usa **comandos** pra configurar (auditar, ver learnings).

---

## Os comandos estruturais

No Codex, peça diretamente pelo comando ou workflow, por exemplo `roda audit em example-brand`. No Claude Code legado, invoque com `/social-media-agent <comando>`.

| Comando | Status | Pra quê | Quando usar |
|---|---|---|---|
| `audit <perfil>` | ✅ pronto | Roda análise de drift + extrai learnings | Periodicamente, pra fechar o loop de aprendizado |
| `learnings <perfil>` | ✅ pronto | Mostra/edita o `learnings.md` | Conferir o que o perfil aprendeu |
| `init` | ⏳ roadmap | Bootstrapa a estrutura do meta-projeto | Hoje desnecessário — `profiles/` já existe no repo |
| `new-profile <nome>` | ⏳ roadmap | Cria um perfil novo do zero (entrevista) | **Ainda não implementado.** Hoje, pra criar perfil novo: crie a pasta `profiles/<nome>/brand-kit/DESIGN.md` + `VOICE.md` à mão (veja a anatomia abaixo) |

> **Status honesto:** só `audit` e `learnings` têm execução real hoje (têm receita no `SKILL.md`). `init`/`new-profile` são roadmap. A produção de posts (Workflows A–D) é toda conversacional e funciona.

Tudo o resto é conversa.

---

## Workflow A — Post novo a partir de link (o mais comum)

**Você diz:**
```
faz um post pra example-brand com esse link https://www.instagram.com/p/XXXX/
```

**O que acontece:**
1. Detecta o perfil (se ambíguo, pergunta). Detecta o formato (feed/carrossel/story — se ambíguo, pergunta).
2. Baixa o link (yt-dlp) pra `posts/AAAA-MM/NN-slug/source/`.
3. Cria o `brief.md` (preenchido com o que extraiu do link).
4. **Te mostra o brief e pergunta antes de gerar** — pra não queimar API com brief errado.
5. Você aprova → roda `craft.py` → gera `outputs/v1/feed.png` → te mostra inline.

**Formatos suportados:** `feed_4x5` (1024×1280), `feed_1x1`, `carousel_4x5`, `story_9x16_still` (1024×1536).

---

## Workflow B — Editar uma peça já gerada

**Você diz:**
```
tira esse emblema, mantém o resto
```
```
deixa o título maior e mais escuro
```

**O que acontece:** identifica o post ativo na conversa → constrói um prompt de edição focado (preservando o que você NÃO pediu pra mudar) → chama o editor de imagem → salva `outputs/v2/` (v3, v4...) → te mostra.

Cada iteração é logada em `decisions.md` (prompt + sua reação). Isso vira matéria-prima do `audit` depois.

---

## Workflow C — Legenda

**Você diz:**
```
qual a legenda?
```

Gera `caption.md` puxando o contexto do brief + a voz do perfil (devocional/utility/announcement). Você itera conversando.

---

## Workflow D — Marcar engajamento

**Você diz:**
```
esse post foi muito bem, alto engajamento
```
```
esse foi flop
```

Anota em `decisions.md`. O próximo `audit` considera esse sinal ao extrair padrões.

---

## Workflow E — Audit (fecha o loop de aprendizado)

`audit example-brand`

**O que faz:**
1. Varre todos os posts com `outputs/final/`.
2. Vision compara cada peça com `brand-kit/pages/` (detecta drift de paleta/fonte/don'ts).
3. Lê todos os `decisions.md` → LLM extrai padrões (o que funcionou / o que evitar / voz / engajamento).
4. Escreve/atualiza `profiles/<perfil>/learnings.md`.

**Efeito:** os próximos posts daquele perfil já incorporam os learnings no prompt automaticamente. Erro cometido uma vez vira regra explícita.

> Custo: ~1 chamada de visão por post + 1 de síntese. Para um perfil com muitos posts, leva alguns minutos.

---

## Anatomia de um perfil

```
profiles/<nome>/
├── brand-kit/
│   ├── DESIGN.md          # OBRIGATÓRIO — identidade: paleta, fontes, mark, princípios, anti-refs
│   └── pages/             # PNGs do brand kit — SEMPRE anexados como refs nos prompts (se houver)
├── VOICE.md               # OBRIGATÓRIO — tom, go_words, no_go_words, contexts
├── assets/                # opcional — logo, foto de perfil, ícones, cenas reutilizáveis
├── references/            # opcional — vault de inspirações (carrosséis baixados, screenshots)
├── posts/AAAA-MM/NN-slug/ # criado quando você faz o 1º post
└── learnings.md           # criado pelo audit (não existe até você rodar `audit`)
```

> **Mínimo de um perfil válido:** só `brand-kit/DESIGN.md`. Os outros diretórios aparecem conforme você usa. O perfil de exemplo `example-brand` traz a estrutura canônica completa.

### Por que `brand-kit/pages/` importa tanto
As imagens do brand kit são **sempre anexadas como image refs** nos prompts de geração. É a virada de qualidade do projeto — sem elas o modelo inventa elementos (ex: um emblema/monograma que não existe). Por isso o schema tem `mark.type: none` explícito quando o perfil não tem logo.

---

## Anatomia de um post

```
posts/AAAA-MM/NN-slug/
├── brief.md               # spec: formato, engine, contexto, o que dizer
├── source/                # original do link (gitignored)
├── craft.py               # script de geração materializado do template
├── outputs/
│   ├── v1/ v2/ v3/        # iterações (gitignored)
│   └── final/             # versão aprovada
├── caption.md             # legenda
└── decisions.md           # log de iterações (prompt + reação) — input do audit
```

---

## Dúvidas frequentes

**A skill não aparece no Codex.** Rode `./install.sh` de novo e abra uma nova sessão. Trabalhando dentro do repo, `AGENTS.md` já dá o contexto principal.

**A skill não aparece no Claude Code.** Rode `./install.sh` de novo (recria o symlink). Ou abra o Claude dentro do repo.

**"OPENAI_API_KEY not set".** Preencha o `.env` na raiz do repo.

**Gerou com cara errada / fora da marca.** Edite o `brand-kit/DESIGN.md` do perfil (paleta/fonte/anti-refs) e rode `audit` pra capturar o que deu errado em `learnings.md`.

**Quero trocar o engine de imagem.** Hoje é OpenAI. Gemini está no roadmap (Phase 5b) — vai ser declarável por post no `brief.md`.

**Quanto custa de API?** Geração de imagem: ~1 chamada gpt-image-2 por peça (+1 por iteração de edit). Audit: ~1 chamada de visão por post + 1 de síntese (~$0.01–0.05 por audit dependendo do nº de posts). Cada edit/iteração é uma nova chamada — por isso a skill confirma o brief antes de gerar.

**Quero fazer vídeo (Reel).** É roadmap. Hoje o vídeo sai por um toolkit de vídeo externo (adapter); integração nativa é roadmap.

**Onde vejo o que cada peça do código faz.** [docs/architecture.md](architecture.md).
