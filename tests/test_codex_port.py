"""Offline port checks: python -m unittest discover -s tests -v."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("pack_installer", ROOT / "scripts/install.py")
setup = load("pack_setup", ROOT / "skills/roblox-skills-setup/scripts/check_setup.py")


class CodexPortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-port-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skills = self.root / ".agents/skills"
        self.agents = self.root / ".codex/agents"

    def install(self):
        with redirect_stdout(io.StringIO()):
            installer.install(self.skills, self.agents)

    def test_reinstall_preserves_settings_and_backs_up_agents_outside_discovery(self):
        self.install()
        self.assertEqual(len(list(self.skills.glob("*/SKILL.md"))), 11)
        agents = list(self.agents.glob("*.toml"))
        self.assertEqual(len(agents), 7)
        for agent in agents:
            data = tomllib.loads(agent.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], agent.stem)
            self.assertEqual(set(data), {"name", "description", "developer_instructions"})
        local = self.skills / "roblox-map/LOCAL.md"
        contents = b"# My settings\r\nmap path: D:/my maps\r\n"
        local.write_bytes(contents)
        agents[0].write_text("# personal agent edit", encoding="utf-8")
        unrelated = self.skills / "my-other-skill"
        unrelated.mkdir()
        (unrelated / "custom.txt").write_text("keep me")
        self.install()
        self.assertEqual(local.read_bytes(), contents)
        self.assertEqual((unrelated / "custom.txt").read_text(), "keep me")
        self.assertEqual(len(list(self.skills.rglob("SKILL.md"))), 11)
        backup = list(self.agents.parent.glob("roblox-skills-backup-*/agents/" + agents[0].name))
        self.assertEqual(len(backup), 1)
        self.assertEqual(backup[0].read_text(), "# personal agent edit")
        self.assertEqual(len(list(self.skills.parent.glob("roblox-skills-backup-*/skills/*/SKILL.md"))), 11)

    def test_copy_failure_restores_previous_install(self):
        self.install()
        first = sorted(self.skills.iterdir())[0]
        (first / "LOCAL.md").write_text("previous settings")
        with patch.object(installer.shutil, "copytree", side_effect=OSError("disk full")):
            with self.assertRaises(OSError), redirect_stdout(io.StringIO()):
                installer.install(self.skills, self.agents)
        self.assertTrue((first / "SKILL.md").is_file())
        self.assertEqual((first / "LOCAL.md").read_text(), "previous settings")

    def test_source_overlap_is_rejected_before_any_write(self):
        with self.assertRaises(ValueError):
            installer.install(ROOT / "skills", self.agents)
        self.assertFalse(self.agents.exists())

    def test_setup_reads_codex_toml_without_reporting_secrets(self):
        config = self.root / "config.toml"
        config.write_text('[mcp_servers.Roblox_Studio]\ncommand = "studio"\n'
                          'env = { SECRET = "never-print-this" }\n', encoding="utf-8")
        result = setup.studio_mcp([config])
        self.assertIn("Roblox_Studio", result)
        self.assertNotIn("never-print-this", result)
        config.write_text('[mcp_servers.Roblox_Studio]\nenabled = false\n')
        self.assertIn("not found", setup.studio_mcp([config]))
        parent = self.root / "parent.toml"
        parent.write_text('[mcp_servers.Roblox_Studio]\ncommand = "studio"\n')
        self.assertIn("not found", setup.studio_mcp([parent, config]))
        config.write_text("invalid toml [")
        self.assertIn("not found", setup.studio_mcp([config]))

    def test_installed_checker_and_scaffold_use_the_installed_pack(self):
        self.install()
        env = dict(os.environ, CODEX_HOME=str(self.agents.parent), ROBLOX_SKILLS_DIR=str(self.skills))
        result = subprocess.run([sys.executable, str(self.skills / "roblox-skills-setup/scripts/check_setup.py"), "--json"],
                                env=env, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertTrue(all(row["installed"] for row in report["skills"].values()))
        self.assertEqual(len(report["agents"]), 7)
        game = self.root / "Game With Spaces"
        result = subprocess.run([sys.executable, str(self.skills / "create-roblox-game/scripts/new_game.py"),
                                 "Port Smoke Test", "--dir", str(game)],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((game / "default.project.json").is_file())
        self.assertEqual(json.loads((game / "design/game.json").read_text())["title"], "Port Smoke Test")
        self.assertIn("~/.agents/skills/", (game / "BUILD.md").read_text())

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell"), "Windows PowerShell unavailable")
    def test_powershell_entrypoint(self):
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                 str(ROOT / "install.ps1"), "-SkillsDir", str(self.skills),
                                 "-AgentsDir", str(self.agents)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(list(self.skills.glob("*/SKILL.md"))), 11)
        self.assertEqual(len(list(self.agents.glob("*.toml"))), 7)

    def test_bash_entrypoint(self):
        bash = Path("C:/Program Files/Git/bin/bash.exe") if os.name == "nt" else Path(shutil.which("bash") or "/missing")
        if not bash.is_file():
            self.skipTest("Bash unavailable")
        result = subprocess.run([str(bash), str(ROOT / "install.sh"), "--skills-dir", str(self.skills),
                                 "--agents-dir", str(self.agents)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(list(self.skills.glob("*/SKILL.md"))), 11)
        self.assertEqual(len(list(self.agents.glob("*.toml"))), 7)


if __name__ == "__main__":
    unittest.main()
