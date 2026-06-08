---
name: social-media-agent
description: Conversational agent for producing Instagram posts across multiple profiles. Use when the user pastes an IG/Twitter/YouTube link asking for a post, requests edits to a generated post, asks for captions, or invokes structural commands (init/new-profile/audit/learnings). Profile lookup auto-detects from chat context or asks user. NOT for: generic image generation (use image-generator), generic copy (use write).
---

# social-media-agent

Produces Instagram posts (feed, carousel, story, reel, story-video) across multiple profiles, with canonical brand schema, multi-engine support (OpenAI gpt-image-2 + Gemini gemini-3-pro-image), and cross-post learning loop.

**Repo root resolution:** if cwd is inside the repo, use that. Otherwise, use the `$SOCIAL_MEDIA_AGENT_HOME` env var. If neither resolves, ask the user for the repo path — do not assume a hard-coded location. The implementation is the installed `social_media_agent` package (`pip install -e .`), so imports are `from social_media_agent.<subpkg> import ...` with no `sys.path` manipulation.

## Sub-commands

| Command | Description | Reference |
|---|---|---|
| `init` | Bootstrap meta-project structure | (Phase 1: stubbed) |
| `new-profile <name>` | Create a new profile (interactive interview) | (Phase 3) |
| `audit <profile>` | Run vision audit + update learnings.md | Bash: `.venv/bin/python -c "from social_media_agent.audit.audit import run_audit; from pathlib import Path; import os; print(run_audit(Path('profiles/<profile>'), os.environ['OPENAI_API_KEY']))"` |
| `learnings <profile>` | Show or edit learnings.md | Bash: `cat profiles/<profile>/learnings.md` or open in editor |

Without sub-command → list commands above + offer conversational entry ("Paste a link to start, or say what you want to do").

## New profile onboarding (do this BEFORE generating anything)

A profile's brand is the source of truth and it is per-project. Get it right up front — most
bad output traces to a guessed/invented brand. Checklist for a new profile:

1. **Download AND inspect the real references first.** Pull the identity/reference images
   (via the ingest selector) into the profile, then actually *view* them. Never build a brand
   from imagination or from a single input you over-weight — look at what the user gave you.
2. **Distill the register(s) into `DESIGN.md`.** A brand often has MORE THAN ONE register
   (e.g. a dark dramatic photographic register AND a light editorial one). Capture all of them,
   the palette (red/accent is usually first-class, not a hairline), fonts, and anti-refs.
   Cite where each came from.
3. **Verify the brand refs actually load.** `brand-kit/pages/` must return count > 0
   (`list_brand_pages`). `brand=0` at craft time means the style anchor is missing — fix it
   before generating, don't generate blind.

## Design method (where the "taste" comes from)

The brand INPUT is per-project and stays per-project: each profile's `DESIGN.md` is the source
of truth for palette/fonts/registers. The design METHOD — how slides are created and validated —
carries the taste from the design skills, layered: **`/readable`** (type scale, measure, leading,
contrast) as the base, **`/nasa-style`** (Helvetica, bold red accent, strict flush-left grid) and
the profile's register on top, and **`/impeccable`** shared laws as the bar (OKLCH-tinted neutrals —
never pure #000/#fff; ≥1.25 hierarchy ratio; rhythmic spacing; no side-stripe borders, no gradient
text, no glassmorphism; no em-dashes in copy; pass the AI-slop test). Don't hand-roll design that
ignores these. `render.html_renderer` already encodes them for text slides; image prompts carry the
same direction.

## Conversational driver

The skill auto-detects user intent from chat messages. Three primary workflows:

### Workflow A — New post from link

**Trigger:** user message contains an IG/Twitter/X/YouTube URL, OR user says "faz post pra X com [link]".

**Steps Claude executes:**

1. **Detect profile.** Look for the profile name in the user message ("example-brand", etc.). If unclear:
   - 1 profile total → use it
   - Multiple → use `AskUserQuestion` to disambiguate
   - 0 → say "No profiles yet. Run `/social-media-agent new-profile <name>` first."

2. **Detect format.** Look for format hints ("carrossel", "feed", "story", "reel"). If unclear, ask:
   - Default suggestions based on common usage: feed_4x5 for single image, carousel_4x5 for multi-slide
   - Use `AskUserQuestion` if ambiguous

3. **Ingest the source.** ALWAYS use the deterministic selector — never pick a
   downloader yourself. It routes by URL so there is no judgement call:

   | URL pattern | Tool (chosen automatically) | Why |
   |---|---|---|
   | Instagram `/p/...` (image or carousel) | **Cobalt** | yt-dlp's IG extractor is video-only → returns 0 files for image carousels |
   | IG `/reel/`, `/tv/`, YouTube, X, others | **yt-dlp** | yt-dlp handles these well |

   ```bash
   .venv/bin/python -c "
   from social_media_agent.ingest.select import fetch
   import json
   r = fetch('<URL>', __import__('pathlib').Path('/tmp/sma-ingest-$$'))
   print(json.dumps({'meta': r['meta'], 'media_files': [str(p) for p in r['media_files']]}, default=str))
   "
   ```
   Cobalt needs a local API running. Setup (`install.sh`) auto-starts it; if ingest
   reports it's unreachable, run `.venv/bin/python -m social_media_agent.cobalt ensure`.
   Never improvise a browser/screenshot path to download media.

4. **Bootstrap the post folder.** Use `social_media_agent.post.bootstrap.bootstrap_post(...)` via Python — provide profile_dir, auto-gen slug via `social_media_agent.post.slug.auto_slug(title=meta['title'], url=URL)`, year_month = current YYYY-MM, format from step 2, engine from profile's DESIGN default (or override), source_files = ingest result.

5. **Materialize craft.py.** Call `social_media_agent.post.materialize.materialize_craft_py(post_dir)` — the template ships inside the package, so `template_dir` is optional. For a **carousel**, put a `slides:` list in the brief frontmatter (see the rules below); materialize then emits a looping, modality-aware craft.py automatically.

6. **Show the user the brief.md** — read it back, summarize 2-3 lines. Ask: "Brief OK? Posso rodar craft.py?" before generating (avoids burning API credits on stale brief).

7. **Ground real-world subjects (if any).** Before generating, ask: does this post depict a *real* person, place, building, saint, or branded object? If yes, run **Workflow G** to anchor the generation in real reference images. If the brief is purely abstract/typographic, skip. (craft.py auto-picks up whatever `refs/grounded/` holds — no extra wiring.)

8. **Run craft.py:**
   ```bash
   .venv/bin/python <post_dir>/craft.py
   ```
   Read the resulting PNG path from script output. Use the Read tool to view it inline so user sees the output.

9. **Init decisions log** for this post: `social_media_agent.post.decisions_log.append_entry(...)`.

### Carousel & rendering modality (HARD RULES — not judgement calls)

The post folder is **self-contained**: the reference being adapted lives in
`<post_dir>/source/` (where ingest/bootstrap put it), next to `brief.md`, `craft.py` and
`outputs/`. A profile-level `references/`/`brand-kit/` is for brand identity, NOT for a
single post's reference. Slide `ref:` paths are relative to the post dir (e.g. `source/01-photo.jpg`).

A carousel is **N slides → N output PNGs**. It NEVER collapses into one image. Define a
`slides:` list in the brief frontmatter; `materialize` emits a craft.py that loops them and
routes EACH slide by these deterministic rules (encoded in `post.slide_modality.classify`):

The deciding question is **"does this slide follow a clear, defined template standard?"** —
NEVER "how much text is there?" (the most text-heavy slide can be the most art-directed).

| Slide | `render:` | Tool | Note |
|---|---|---|---|
| Follows a **defined template standard** (legend, quote, info, hours, table, prose) | `html` | `render.html_renderer` (real fonts, crisp body copy) | Only for our known templates |
| **Art-directed / expressive / no matching template** (covers, display-type, integrated imagery, the whole encyclical look) | `image` | `engines.openai_gpt_image_2`, **adapting the reference** | A generic HTML template CANNOT honour art direction — never force it |

**When in doubt, it is NOT html.** A typographic cover is text-heavy but art-directed → image.
Default (`post.slide_modality.classify`) is `image` unless a templated `kind`/`render: html` is set.

Within an **image** slide, the method is also fixed, not chosen:
| Intent | Method | Refs |
|---|---|---|
| Adapt / replicate a reference slide | `edit()` | the source slide (layout) + brand pages (style) |
| Original piece, no reference | `generate()` | brand pages only |

**Gates:** if you are about to (a) produce one image for a multi-slide carousel, (b) route an
art-directed slide (a cover, display-type, the encyclical look) through the generic HTML
template, or (c) call `generate()` while adapting a reference (dropping its image) — STOP,
you are on the wrong path. HTML is only for slides that match a defined template standard.

### Workflow B — Edit iteration

**Trigger:** user says something like "tira X", "muda Y pra Z", "deixa o título maior", "trocar a fonte do hero" on the active post.

**Steps:**

1. **Identify active post.** The active post is the one most recently mentioned/generated in the conversation. If unclear, ask user.

2. **Build a focused edit prompt.** Compose: "Edit this image — [user's request]. PRESERVE everything else (mention key elements explicitly so model knows what NOT to change)." Reference brand mark.type=none rule if applicable.

3. **Call `openai_gpt_image_2.edit()`** with the previous version as image #1, brand-kit/pages as additional refs, and the focused prompt. Save to next version dir (e.g. v1 → v2).

4. **Show new output** via Read tool, ask "tá melhor?"

5. **Log the iteration** in decisions.md: `append_entry(version="v2", prompt=<focused_prompt>, note=<user request paraphrase>)`.

### Workflow C — Caption generation

**Trigger:** user says "qual a legenda?", "escreve a caption", "faz a legenda pra esse".

**Steps:**

1. **Identify active post.** Same as Workflow B.

2. **Generate skeleton** via `social_media_agent.post.caption.create_caption_skeleton(post_dir, profile_dir)` — creates `caption.md` if missing.

3. **Fill caption conversationally** — read the skeleton's pattern hint, write a caption following the voice/context. Show to user, iterate.

4. **Save final caption** by editing caption.md (replacing the placeholder content with the agreed text).

### Workflow D — Engagement annotation

**Trigger:** user says "esse funcionou bem", "engagement alto", "esse foi flop".

**Steps:**

1. Identify the post being discussed.
2. Append annotation to that post's decisions.md: `append_entry(version="engagement", prompt="(N/A)", note=<user's words>)`.
3. Confirm to user: "Anotado pra próximo audit."

---

### Workflow E — Audit (cross-post learning)

**Trigger:** user says "run audit on <profile>", "/social-media-agent audit <profile>", "audit example-brand".

**Steps:**

1. **Identify profile.** Same disambiguation as Workflow A step 1.
2. **Confirm with user** before running — audit hits OpenAI vision per post + 1 text-extraction call. Mention estimated cost (~$0.01 per post for vision + ~$0.02 total for synthesis at gpt-5 rates as of 2026-05).
3. **Run the audit:**
   ```bash
   .venv/bin/python -c "
   import sys, os, json
   from social_media_agent.audit.audit import run_audit
   from pathlib import Path
   r = run_audit(Path('profiles/<profile>'), os.environ['OPENAI_API_KEY'])
   print(json.dumps({'posts_analyzed': r['posts_analyzed'], 'learnings_path': str(r['learnings_path']), 'patterns': r['patterns'], 'drift_count': sum(1 for d in r['drifts'] if d.get('palette_drift') or d.get('font_drift') or d.get('donts_violations'))}, indent=2))
   "
   ```
4. **Show the user** the resulting learnings.md (Read tool) + summary of new vs prior patterns if previous learnings.md existed.
5. **Subsequent posts** will automatically incorporate learnings via prompt_builder — no extra step needed.

---

### Workflow G — Grounding (anchor real-world subjects to real refs)

**Why:** by default the engine invents faces/places from imagination → wrong, inconsistent subjects. Grounding anchors generation to real reference images of the actual subject (ports stages 1–3 of the opennanobanana flow; stage 4 is just `craft.py`).

**Trigger:** the brief depicts a **real** person, place, building, saint, or branded object (Workflow A step 7, or user says "ancora", "usa foto de referência", "fica igual à pessoa/lugar real").

**Steps Claude executes:**

1. **Extract subjects.** Find what needs grounding:
   ```bash
   .venv/bin/python -c "
   import os, json
   from social_media_agent.grounding.extract import extract_subjects
   print(json.dumps(extract_subjects(open('<post_dir>/brief.md').read(), os.environ['OPENAI_API_KEY']), ensure_ascii=False))
   "
   ```
   Empty list → nothing to ground, skip the rest.

2. **Acquire references — user first.** For each subject, **ask the user**: "Pode me mandar a foto do/da **{subject}** que quer usar de referência?" The user's own photo is the highest-fidelity, lowest-risk source. Wait for it.

3. **If the user has no photo** ("acha você", "pode buscar"), acquire refs yourself, in order:
   - **Chrome MCP web search** (preferred — visible, you pick the best image): search `{subject.search_query}`, open a couple of strong candidates, save the image files locally.
   - **Serper** (only if `SERPER_API_KEY` set): `social_media_agent.grounding.search.serper_image_search(query)` → download a candidate. Tertiary fallback.

4. **Verify each candidate** before keeping it (skips bad matches before burning gen credit):
   ```bash
   .venv/bin/python -c "
   import os, json
   from social_media_agent.grounding.verify import verify_ref
   from pathlib import Path
   print(json.dumps(verify_ref({'name':'<name>','kind':'<kind>','why':'<why>'}, Path('<candidate>'), os.environ['OPENAI_API_KEY'])))
   "
   ```
   `match:false` → discard, get another.

5. **Register validated refs** into the post (copies file + writes `refs/grounded/grounding.json` manifest):
   ```bash
   .venv/bin/python -c "
   from social_media_agent.grounding.ground import register_ref
   from pathlib import Path
   register_ref(Path('<post_dir>'), {'name':'<name>','kind':'<kind>','search_query':'<q>','why':'<why>'}, Path('<validated-img>'), source='user', score=0.9)
   "
   ```
   `source` ∈ {user, web, serper}.

6. **Tell the user which refs locked**, then continue to craft.py (Workflow A step 8). craft.py calls `collect_grounded_refs` automatically — grounded refs lead the ref list, capped at `engine.MAX_REFS`.

**Engine note:** for grounded posts (faces, scenes, multi-ref) prefer the **Gemini** engine (`default_engine: gemini_image` in the profile DESIGN.md, or override in the brief) — it accepts up to **14 refs** vs gpt-image-2's 5, and holds subject likeness better. Keep gpt-image-2 where crisp text rendering matters more.

---

## Conversational guardrails

- **Validate cheap before paid.** Image generation costs credits; HTML rendering and dry-runs are free. Confirm the brief, and render/preview the FREE parts first (HTML text slides, the materialized prompt) before spending on image slides. Don't iterate aesthetics by repeatedly regenerating paid images.
- **Fix pointed defects slide-by-slide, never the whole carousel.** A bad hand on slide 3 → regenerate only slide 3 (one image call), not all N slides. Overwrite that one output.
- **Always confirm format + brief before craft.py runs** (avoid burning credits on misalignment).
- **Always show output PNG inline** (Read tool with the path) so user can see what was made — and inspect it for defects (anatomy, garbled text, wrong palette) BEFORE claiming it's done.
- **Always log iterations to decisions.md** for the audit command later.
- **Never overwrite outputs/final/** — only outputs/v{N}/.
- **Never invent emblems/monograms** — `prompt_builder` already injects the mark.type=none rule, but reinforce in your own prose if user requests visual elements not in DESIGN.md.
- **Never let the model invent a real subject** — if a post shows a real person/place/saint/building, run Workflow G first. Ask the user for a reference photo before searching yourself.
- **Match the user's tone in conversation** — mirror the register the user writes in.

## Profile schema

See `docs/architecture.md` for the canonical schema (DESIGN.md YAML+markdown, brand-kit/pages/, VOICE.md, assets/, references/, posts/YYYY-MM/NN-slug/, learnings.md).

## Hard gates

| Gate | Check | Failure → |
|---|---|---|
| Profile context | Profile inferred or asked | Ask user with `AskUserQuestion` |
| API keys | OPENAI_API_KEY or GEMINI_API_KEY present per engine choice | Error with install.sh instruction |
| Brand context | DESIGN.md + brand-kit/pages/ present | If new profile: trigger `new-profile`. If existing: error |
| Mutation | All above pass | Nothing generates |

## Phase status

- **Phase 1 (scaffold) DONE** — repo + install.sh + smoke tests + skill skeleton
- **Phase 2 (vertical slice) DONE** — adapters wired (`brand.brand_loader`, `brand.prompt_builder`, `engines.openai_gpt_image_2`, `ingest.yt_dlp`, `render.image_renderer`); the `example-brand` profile ships as a reference with the canonical schema
- **Phase 3 (conversational driver) DONE** — Workflows A/B/C/D
- **Phase 4 (audit + learning loop) DONE** — `audit` scans posts, vision-checks drift vs brand pages, LLM-extracts patterns from decisions.md, writes `<profile>/learnings.md`. `prompt_builder` now injects top-N learnings into future prompts (closes the cross-post feedback loop).
- **Phase 6 (Gemini engine + grounding) DONE** — `engines.gemini_image` (up to 14 refs) + `engines.get_engine()` registry; craft.py is engine-agnostic (per-profile `default_engine`). `grounding.*` extracts subjects → acquires refs (user/Chrome/Serper) → vision-verifies → registers into `refs/grounded/`; Workflow G drives it; `select_refs` gives grounded refs priority within `engine.MAX_REFS`.

What the adapters expose (Phase 3 driver can call these via Bash invocations of `scripts/post/...`):
- `brand_loader.parse_design_md(path) → (meta_dict, body_str)` — YAML frontmatter + markdown
- `brand_loader.parse_voice_md(path) → (meta_dict, body_str)` — same shape
- `brand_loader.list_brand_pages(pages_dir) → list[Path]` — sorted PNGs
- `prompt_builder.build_prompt(task, design, voice, brand_pages, extra_refs, *, grounded_refs, ref_limit) → (text_prompt, image_refs)` — injects mark.type=none rule; `select_refs` orders grounded→source→brand, caps at ref_limit
- `engines.get_engine(name) → module` — resolves `openai_gpt_image_2`/`gemini_image` (+ aliases); each exposes `generate`, `edit`, `MAX_REFS`, `API_KEY_ENV`
- `engines.spec.resolve_gen_kwargs(engine, format) → dict` — per-engine size/aspect kwargs
- `openai_gpt_image_2.generate/edit(...)` → bytes (1–5 refs) · `gemini_image.generate/edit(...)` → bytes (1–14 refs)
- `grounding.extract.extract_subjects`, `grounding.verify.verify_ref`, `grounding.search.serper_image_search`, `grounding.ground.register_ref/collect_grounded_refs`
- `yt_dlp.fetch(url, output_dir) → {meta, media_files}` — shell-out to yt-dlp
- `image_renderer.save(data: bytes, path: Path)` — write bytes, mkdir parents
- `image_renderer.preview_grid(slide_paths, cols=3) → PIL.Image` — composite NxM
