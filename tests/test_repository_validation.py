import unittest
from pathlib import Path

import yaml

from scripts import validate_repo
from scripts.sync_role_agents import role_agents, synchronized_content


ROOT = Path(__file__).resolve().parents[1]


class RepositoryValidationTests(unittest.TestCase):
    def test_repository_is_valid(self):
        self.assertEqual(validate_repo.collect_errors(ROOT), [])

    def test_role_agents_match_canonical_skills(self):
        pairs = role_agents(ROOT)
        self.assertEqual(len(pairs), 15)
        for agent_path, skill_path in pairs:
            self.assertEqual(
                agent_path.read_text(encoding="utf-8").replace("\r\n", "\n"),
                synchronized_content(agent_path, skill_path),
            )

    def test_codex_metadata_schema_and_prompts(self):
        metadata = list((ROOT / "skills").glob("*/agents/openai.yaml"))
        self.assertEqual(len(metadata), 17)
        for path in metadata:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertIn("interface", data)
            interface = data["interface"]
            name = path.parent.parent.name
            self.assertEqual(interface["default_prompt"].split()[1], "$" + name)
            self.assertTrue(interface["default_prompt"].startswith("Use $" + name))

    def test_high_risk_gate_order(self):
        text = (ROOT / "skills/engineering-flows-and-gates/SKILL.md").read_text(encoding="utf-8")
        text = text.split("HIGH-risk work (required order):", 1)[1].split("LOW/MEDIUM new feature:", 1)[0]
        sequence = [
            "research",
            "security-analyst (GATE-0 threat model)",
            "system-design",
            "architecture-engineer/api-design",
            "task-planner",
            "implementation",
            "tester",
            "QA",
            "security-analyst (GATE-3)",
        ]
        positions = [text.index(item) for item in sequence]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
