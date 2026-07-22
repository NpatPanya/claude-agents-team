"""Synchronize role agent bodies from their canonical skill definitions."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]


def split_front_matter(text: str) -> tuple[str, str]:
    """Return the complete frontmatter block and the body after it."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("file does not start with YAML frontmatter")
    match = re.search(r"\n---\n", normalized[4:])
    if not match:
        raise ValueError("frontmatter closing delimiter is missing")
    end = 4 + match.end()
    return normalized[:end], normalized[end:]


def frontmatter_name(text: str) -> str:
    frontmatter, _ = split_front_matter(text)
    match = re.search(r"(?m)^name:\s*([^\n#]+?)\s*$", frontmatter)
    if not match:
        raise ValueError("frontmatter has no name")
    return match.group(1).strip().strip('"\'')


def canonical_body(skill_path: Path) -> str:
    _, body = split_front_matter(skill_path.read_text(encoding="utf-8"))
    return body.lstrip("\n")


def synchronized_content(agent_path: Path, skill_path: Path) -> str:
    frontmatter, _ = split_front_matter(agent_path.read_text(encoding="utf-8"))
    return frontmatter + canonical_body(skill_path)


def role_agents(root: Path = ROOT) -> list[tuple[Path, Path]]:
    skills = {
        frontmatter_name(path.read_text(encoding="utf-8")): path
        for path in (root / "skills").glob("*/SKILL.md")
    }
    pairs = []
    for agent_path in sorted((root / "agents").glob("**/*.md")):
        name = frontmatter_name(agent_path.read_text(encoding="utf-8"))
        if name in skills:
            pairs.append((agent_path, skills[name]))
    return pairs


def synchronize(root: Path = ROOT, check: bool = False) -> list[str]:
    differences: list[str] = []
    for agent_path, skill_path in role_agents(root):
        expected = synchronized_content(agent_path, skill_path)
        current = agent_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if current == expected:
            continue
        diff = "".join(difflib.unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=str(agent_path.relative_to(root)),
            tofile=f"{agent_path.relative_to(root)} (canonical skill)",
        ))
        differences.append(diff)
        if not check:
            agent_path.write_text(expected, encoding="utf-8", newline="\n")
    return differences


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without modifying files")
    args = parser.parse_args(argv)
    differences = synchronize(check=args.check)
    if differences:
        if args.check:
            print("Role agents are out of sync:")
            print("\n".join(differences))
            return 1
        print(f"Synchronized {len(differences)} role agent file(s).")
    else:
        print("Role agents are synchronized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
