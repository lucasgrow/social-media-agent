"""Smoke tests — confirm repo layout + skill discoverability."""
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "social-media-agent"
CODEX_SKILL_DIR = REPO_ROOT / ".codex" / "skills" / "social-media-agent"
# Tool-agnostic implementation package — neither .claude nor .codex owns it.
PKG_DIR = REPO_ROOT / "src" / "social_media_agent"


def test_repo_has_expected_directories():
    """Repo has the canonical top-level directories."""
    assert (REPO_ROOT / "profiles").is_dir()
    assert (REPO_ROOT / "docs").is_dir()
    assert (REPO_ROOT / "tests").is_dir()
    assert SKILL_DIR.is_dir()
    assert CODEX_SKILL_DIR.is_dir()


def test_skill_has_skill_md():
    """Claude-compatible SKILL.md exists and is non-empty."""
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.is_file()
    content = skill_md.read_text()
    assert len(content) > 100, "SKILL.md is suspiciously short"
    assert "social-media-agent" in content


def test_codex_context_files_exist():
    """Codex has project context plus a synced skill."""
    agents_md = REPO_ROOT / "AGENTS.md"
    codex_skill_md = CODEX_SKILL_DIR / "SKILL.md"

    assert agents_md.is_file()
    assert codex_skill_md.is_file()
    assert "social-media-agent" in agents_md.read_text()

    content = codex_skill_md.read_text()
    assert "name: social-media-agent" in content
    assert "social_media_agent" in content


def test_codex_skill_matches_claude_skill():
    """Claude is the canonical operational skill; Codex must not drift."""
    claude_skill = SKILL_DIR / "SKILL.md"
    codex_skill = CODEX_SKILL_DIR / "SKILL.md"
    assert codex_skill.read_text() == claude_skill.read_text()


def test_package_has_adapter_dirs():
    """Implementation package has the 4 adapter concern subpackages."""
    assert (PKG_DIR / "ingest").is_dir()
    assert (PKG_DIR / "engines").is_dir()
    assert (PKG_DIR / "render").is_dir()
    assert (PKG_DIR / "brand").is_dir()


def test_package_is_importable():
    """The implementation is installed as a tool-agnostic package."""
    import social_media_agent  # noqa: F401


def test_pyproject_toml_present():
    """pyproject.toml exists and declares the package."""
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.is_file()
    content = pyproject.read_text()
    assert 'name = "social-media-agent"' in content


def test_install_sh_executable():
    """install.sh is present and executable."""
    install = REPO_ROOT / "install.sh"
    assert install.is_file()
    assert install.stat().st_mode & 0o111, "install.sh is not executable"


def test_check_sh_executable():
    """`scripts/check.sh` is present and executable."""
    check = REPO_ROOT / "scripts" / "check.sh"
    assert check.is_file()
    assert check.stat().st_mode & 0o111, "scripts/check.sh is not executable"


def test_env_example_present():
    """`.env.example` template exists with expected keys."""
    env_example = REPO_ROOT / ".env.example"
    assert env_example.is_file()
    content = env_example.read_text()
    assert "OPENAI_API_KEY" in content
    assert "GEMINI_API_KEY" in content
