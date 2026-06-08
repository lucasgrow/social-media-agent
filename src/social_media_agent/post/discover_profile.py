"""Profile discovery — find profile by name, list profiles, handle ambiguity."""
from pathlib import Path


class ProfileNotFound(Exception):
    """Raised when no matching profile exists."""


class ProfileAmbiguous(Exception):
    """Raised when no name given and multiple profiles exist."""

    def __init__(self, candidates: list[str]):
        self.candidates = candidates
        super().__init__(f"Multiple profiles found; specify one of: {', '.join(candidates)}")


def list_profiles(profiles_dir: Path) -> list[str]:
    """Return sorted list of valid profile names under profiles_dir.

    A valid profile has brand-kit/DESIGN.md.
    """
    if not profiles_dir.is_dir():
        return []
    result = []
    for child in profiles_dir.iterdir():
        if not child.is_dir():
            continue
        if (child / "brand-kit" / "DESIGN.md").is_file():
            result.append(child.name)
    return sorted(result)


def discover_profile(profiles_dir: Path, name: str | None) -> Path:
    """Resolve a profile name (or None) to a profile directory.

    Args:
        profiles_dir: the profiles/ root directory
        name: profile name, or None to auto-pick when exactly one exists

    Returns:
        Path to the profile directory.

    Raises:
        ProfileNotFound: name given but no match, OR no profiles at all
        ProfileAmbiguous: no name given AND multiple profiles exist
    """
    profiles = list_profiles(profiles_dir)
    if name is not None:
        if name in profiles:
            return profiles_dir / name
        raise ProfileNotFound(f"Profile '{name}' not found. Available: {profiles or '(none)'}")
    if not profiles:
        raise ProfileNotFound("No profiles exist yet. Run /social-media-agent new-profile <name>.")
    if len(profiles) == 1:
        return profiles_dir / profiles[0]
    raise ProfileAmbiguous(profiles)
