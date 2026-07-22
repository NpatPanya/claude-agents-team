"""Validate skill, agent, metadata, reference, synchronization, and release invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - gives a useful CLI error
    raise SystemExit("PyYAML is required; install requirements-dev.txt") from exc

try:
    from .sync_role_agents import frontmatter_name, role_agents, split_front_matter, synchronized_content
except ImportError:  # direct script execution
    from sync_role_agents import frontmatter_name, role_agents, split_front_matter, synchronized_content


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILL_KEYS = {"name", "description"}
EXPECTED_AGENT_KEYS = {"name", "description", "model", "effort", "tools", "skills"}
OPENAI_TOP_LEVEL_KEYS = {"interface", "dependencies", "policy"}
OPENAI_INTERFACE_KEYS = {"display_name", "short_description", "default_prompt", "icon_small", "icon_large"}
ALLOWED_MODELS = {"haiku", "sonnet", "opus"}
ALLOWED_EFFORTS = {"low", "medium", "high", "xhigh", "max"}

DISPLAY_NAMES = {
    "agent-handoff-protocol": "Agent Handoff Protocol",
    "api-design": "API Design",
    "architecture-engineer": "Architecture Engineer",
    "backend-developer": "Backend Developer",
    "codebase-researcher": "Codebase Researcher",
    "devops": "DevOps",
    "document-researcher": "Document Researcher",
    "engineering-flows-and-gates": "Engineering Flows and Gates",
    "frontend-developer": "Frontend Developer",
    "project-manager": "Project Manager",
    "qa": "QA",
    "root-cause-analyst": "Root Cause Analyst",
    "safe-refactor": "Safe Refactor",
    "security-analyst": "Security Analyst",
    "system-design": "System Design",
    "task-planner": "Task Planner",
    "tester": "Tester",
}

SHORT_DESCRIPTIONS = {
    "agent-handoff-protocol": "Structure agent dispatches, completions, blocks, and escalations.",
    "api-design": "Define precise API contracts, errors, auth, and versioning.",
    "architecture-engineer": "Turn approved designs into implementable technical specifications.",
    "backend-developer": "Implement server-side code against approved specifications.",
    "codebase-researcher": "Trace existing code and assess the blast radius of changes.",
    "devops": "Handle CI/CD, infrastructure, deployment, and environment configuration.",
    "document-researcher": "Gather reliable documentation and external references for the team.",
    "engineering-flows-and-gates": "Classify work, sequence agents, and enforce quality gates.",
    "frontend-developer": "Implement client-side UI against approved designs and specifications.",
    "project-manager": "Scope, classify, delegate, and reconcile multi-agent engineering work.",
    "qa": "Review deliverables against requirements before work is considered complete.",
    "root-cause-analyst": "Investigate bugs and incidents to identify their actual root cause.",
    "safe-refactor": "Perform scoped, behavior-preserving mechanical refactors.",
    "security-analyst": "Threat-model and review authentication, input, secrets, and data exposure.",
    "system-design": "Define high-level architecture, boundaries, data flow, and tradeoffs.",
    "task-planner": "Break approved work into ordered, dependency-aware implementation tasks.",
    "tester": "Write and run automated tests, including relevant edge cases.",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    frontmatter, body = split_front_matter(path.read_text(encoding="utf-8"))
    payload = yaml.safe_load(frontmatter[4:-5]) or {}
    if not isinstance(payload, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return payload, body


def _error(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def validate_skills(errors: list[str]) -> dict[str, Path]:
    skills: dict[str, Path] = {}
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        path = skill_dir / "SKILL.md"
        if not path.exists():
            _error(errors, skill_dir, "missing SKILL.md")
            continue
        try:
            data, _ = parse_frontmatter(path)
        except Exception as exc:
            _error(errors, path, f"invalid frontmatter: {exc}")
            continue
        if set(data) != EXPECTED_SKILL_KEYS:
            _error(errors, path, f"top-level keys must be {sorted(EXPECTED_SKILL_KEYS)}; got {sorted(data)}")
        name = data.get("name")
        if not isinstance(name, str) or name != skill_dir.name:
            _error(errors, path, "name must match its skill directory")
        if not isinstance(data.get("description"), str) or not data["description"].strip():
            _error(errors, path, "description must be a non-empty string")
        if isinstance(name, str):
            if name in skills:
                _error(errors, path, f"duplicate skill name {name!r}")
            skills[name] = path
        metadata = skill_dir / "agents" / "openai.yaml"
        if not metadata.exists():
            _error(errors, metadata, "missing Codex metadata")
    return skills


def declared_dependency_plugins() -> set[str]:
    """Plugin names declared under `dependencies` in plugin.json."""
    plugin_path = ROOT / ".claude-plugin" / "plugin.json"
    try:
        data = json.loads(plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    names: set[str] = set()
    for dep in data.get("dependencies", []) or []:
        if isinstance(dep, dict) and isinstance(dep.get("name"), str):
            names.add(dep["name"])
    return names


def validate_agents(errors: list[str], skills: dict[str, Path]) -> dict[str, Path]:
    agents: dict[str, Path] = {}
    dependency_plugins = declared_dependency_plugins()
    for path in sorted((ROOT / "agents").glob("**/*.md")):
        try:
            data, _ = parse_frontmatter(path)
        except Exception as exc:
            _error(errors, path, f"invalid frontmatter: {exc}")
            continue
        missing = EXPECTED_AGENT_KEYS - set(data)
        if missing:
            _error(errors, path, f"missing frontmatter keys: {sorted(missing)}")
        name = data.get("name")
        if not isinstance(name, str) or not name:
            _error(errors, path, "name must be a non-empty string")
            continue
        if name in agents:
            _error(errors, path, f"duplicate agent name {name!r}")
        agents[name] = path
        for key in ("description", "model", "effort"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                _error(errors, path, f"{key} must be a non-empty string")
        model = data.get("model")
        if isinstance(model, str) and model.strip() and model not in ALLOWED_MODELS:
            _error(errors, path, f"model must be one of {sorted(ALLOWED_MODELS)}; got {model!r}")
        effort = data.get("effort")
        if isinstance(effort, str) and effort.strip() and effort not in ALLOWED_EFFORTS:
            _error(errors, path, f"effort must be one of {sorted(ALLOWED_EFFORTS)}; got {effort!r}")
        tools = data.get("tools")
        if not ((isinstance(tools, list) and tools) or (isinstance(tools, str) and tools.strip())):
            _error(errors, path, "tools must be a non-empty list or comma-separated string")
        if not isinstance(data.get("skills"), list):
            _error(errors, path, "skills must be a list")
        else:
            for skill_ref in data["skills"]:
                if not isinstance(skill_ref, str):
                    _error(errors, path, f"skill reference must be a string; got {skill_ref!r}")
                    continue
                if skill_ref.startswith("agt:"):
                    skill_name = skill_ref[4:]
                    if skill_name not in skills:
                        _error(errors, path, f"unresolved local skill reference {skill_ref!r}")
                elif ":" in skill_ref:
                    namespace = skill_ref.split(":", 1)[0]
                    if namespace not in dependency_plugins:
                        _error(errors, path, f"external skill reference {skill_ref!r} requires plugin {namespace!r} to be declared in plugin.json dependencies")
                else:
                    _error(errors, path, f"skill reference {skill_ref!r} must be namespaced (agt:<name> or <plugin>:<name>)")
    for name, path in agents.items():
        if name not in skills:
            _error(errors, path, f"no matching canonical skill for agent {name!r}")
    for name, path in skills.items():
        if name not in agents and name not in {"agent-handoff-protocol", "engineering-flows-and-gates"}:
            _error(errors, path, f"role skill has no matching agent {name!r}")
    return agents


def validate_openai_metadata(errors: list[str], skills: dict[str, Path]) -> None:
    for name, skill_path in skills.items():
        path = skill_path.parent / "agents" / "openai.yaml"
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _error(errors, path, f"invalid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            _error(errors, path, "metadata root must be a mapping")
            continue
        if set(data) - OPENAI_TOP_LEVEL_KEYS:
            _error(errors, path, f"unsupported top-level keys: {sorted(set(data) - OPENAI_TOP_LEVEL_KEYS)}")
        interface = data.get("interface")
        if not isinstance(interface, dict):
            _error(errors, path, "interface must be a mapping")
            continue
        if set(interface) - OPENAI_INTERFACE_KEYS:
            _error(errors, path, f"unsupported interface keys: {sorted(set(interface) - OPENAI_INTERFACE_KEYS)}")
        for key in ("display_name", "short_description", "default_prompt"):
            if not isinstance(interface.get(key), str) or not interface[key].strip():
                _error(errors, path, f"interface.{key} must be a non-empty string")
        if interface.get("display_name") != DISPLAY_NAMES.get(name):
            _error(errors, path, f"display_name must be {DISPLAY_NAMES.get(name)!r}")
        if interface.get("short_description") != SHORT_DESCRIPTIONS.get(name):
            _error(errors, path, "short_description does not match the deterministic description")
        expected_token = f"${name}"
        prompt = interface.get("default_prompt", "")
        if expected_token not in prompt or not prompt.startswith(f"Use {expected_token}"):
            _error(errors, path, f"default_prompt must start with 'Use {expected_token}'")
        if re.search(r"\$[A-Za-z0-9_-]+", prompt.replace(expected_token, "")):
            _error(errors, path, "default_prompt contains an additional skill token")


def validate_sync(errors: list[str]) -> None:
    for agent_path, skill_path in role_agents(ROOT):
        expected = synchronized_content(agent_path, skill_path)
        actual = agent_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if actual != expected:
            _error(errors, agent_path, f"body is not synchronized with {skill_path.relative_to(ROOT)}")


def validate_high_flow(errors: list[str]) -> None:
    path = ROOT / "skills" / "engineering-flows-and-gates" / "SKILL.md"
    text = path.read_text(encoding="utf-8").replace("???", "->")
    section = text.split("HIGH-risk work (required order):", 1)[-1].split("LOW/MEDIUM new feature:", 1)[0]
    required = (
        "research",
        "security-analyst (GATE-0 threat model)",
        "system-design",
        "architecture-engineer/api-design",
        "task-planner",
        "implementation",
        "tester",
        "QA",
        "security-analyst (GATE-3)",
    )
    positions = [section.find(item) for item in required]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        _error(errors, path, "HIGH flow must order research, GATE-0, design, planning, implementation, tester, QA, and GATE-3")


def validate_manifests(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _error(errors, path, f"invalid JSON: {exc}")
    for path in sorted(ROOT.rglob("*.yaml")) + sorted(ROOT.rglob("*.yml")):
        if ".git" in path.parts:
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _error(errors, path, f"invalid YAML: {exc}")


def validate_versions(errors: list[str]) -> None:
    plugin_path = ROOT / ".claude-plugin" / "plugin.json"
    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    try:
        plugin_version = json.loads(plugin_path.read_text(encoding="utf-8"))["version"]
        marketplace_version = json.loads(marketplace_path.read_text(encoding="utf-8"))["metadata"]["version"]
        if plugin_version != marketplace_version:
            _error(errors, marketplace_path, f"version {marketplace_version!r} must match plugin version {plugin_version!r}")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        _error(errors, marketplace_path, f"could not read release versions: {exc}")


def collect_errors(root: Path = ROOT) -> list[str]:
    # ROOT is currently fixed for the CLI; accepting it makes unit tests able to use a copy.
    global ROOT
    original_root = ROOT
    ROOT = root
    errors: list[str] = []
    try:
        skills = validate_skills(errors)
        validate_agents(errors, skills)
        validate_openai_metadata(errors, skills)
        validate_sync(errors)
        validate_high_flow(errors)
        validate_manifests(errors)
        validate_versions(errors)
    finally:
        ROOT = original_root
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    errors = collect_errors()
    if errors:
        print("Repository validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
