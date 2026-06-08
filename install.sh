#!/usr/bin/env bash
# install.sh — set up social-media-agent on this machine
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILL_SRC="$REPO_ROOT/.claude/skills/social-media-agent"
CLAUDE_SKILL_DST="$HOME/.claude/skills/social-media-agent"
CODEX_SKILL_SRC="$REPO_ROOT/.codex/skills/social-media-agent"
CODEX_SKILL_DST="$HOME/.codex/skills/social-media-agent"

link_skill() {
    local src="$1"
    local dst="$2"
    local label="$3"

    echo "==> Symlinking $label skill"
    mkdir -p "$(dirname "$dst")"
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -e "$dst" ]; then
        echo "    ERROR: $dst exists and is not a symlink. Remove manually first."
        exit 1
    fi
    ln -s "$src" "$dst"
}

echo "==> Installing social-media-agent"
echo "    repo: $REPO_ROOT"

# 1. Ensure Python venv exists
if [ ! -d "$REPO_ROOT/.venv" ]; then
    echo "==> Creating Python venv"
    python3 -m venv "$REPO_ROOT/.venv"
fi

# 2. Install/upgrade Python deps
echo "==> Installing Python deps"
"$REPO_ROOT/.venv/bin/pip" install --quiet -e "$REPO_ROOT[dev]"

# 3. Symlink skills for Codex and Claude Code.
link_skill "$CODEX_SKILL_SRC" "$CODEX_SKILL_DST" "Codex"
link_skill "$CLAUDE_SKILL_SRC" "$CLAUDE_SKILL_DST" "Claude Code"

# 4. Check for .env
if [ ! -f "$REPO_ROOT/.env" ]; then
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
    echo "==> No .env found — copied .env.example → .env. Fill in your API keys."
fi

# 5. Check for yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "==> WARNING: yt-dlp not found. Install with: brew install yt-dlp (macOS) or pip install yt-dlp"
fi

# 6. Install the Chromium used to render text-dominant carousel slides (HTML → PNG).
echo "==> Installing Chromium for Playwright (HTML slide rendering)"
"$REPO_ROOT/.venv/bin/python" -m playwright install chromium || \
    echo "    WARNING: 'playwright install chromium' failed — HTML text slides will be unavailable."

# 7. Provision + start the local Cobalt API (Instagram image/carousel ingest).
#    Cross-platform entrypoint; on Windows run this line manually after setup.
echo "==> Ensuring local Cobalt API (needs node + pnpm)"
if "$REPO_ROOT/.venv/bin/python" -m social_media_agent.cobalt ensure; then
    :
else
    echo "    WARNING: Cobalt not started. IG carousel ingest will be unavailable until you run:"
    echo "             .venv/bin/python -m social_media_agent.cobalt ensure"
fi

echo ""
echo "==> Done. Try Codex inside this repo, or Claude Code with /social-media-agent"
