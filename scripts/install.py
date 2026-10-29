#!/usr/bin/env python3
"""Install this pack for Codex, backing up replaced skills and custom agents."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def install(skills_dir: Path, agents_dir: Path) -> None:
    skills_dir = skills_dir.expanduser().resolve()
    agents_dir = agents_dir.expanduser().resolve()
    sources = [(p, skills_dir / p.name, True) for p in sorted((ROOT / "skills").iterdir())
               if (p / "SKILL.md").is_file()]
    sources += [(p, agents_dir / p.name, False) for p in sorted(
        (ROOT / "skills/roblox-build-orchestrator/agents").glob("*.toml"))]
    for src, dst, _ in sources:
        if dst.is_relative_to(ROOT) or ROOT.is_relative_to(dst):
            raise ValueError(f"Install destination overlaps the source repository: {dst}")
        if dst.is_symlink():
            raise ValueError(f"Refusing to replace a symlink: {dst}")
        if dst.exists() and dst.is_dir() != src.is_dir():
            raise ValueError(f"Destination has the wrong file type: {dst}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for src, dst, is_skill in sources:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Keep backups outside discovery directories so Codex cannot load old skills.
        backup = dst.parent.parent / ("roblox-skills-backup-" + stamp) / dst.parent.name / dst.name
        if dst.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            # Absolute children of the explicitly selected install root.
            shutil.move(str(dst), str(backup))
            print(f"  backed up {dst.name} to {backup}")
        try:
            if is_skill:
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    "LOCAL.md", "__pycache__", "*.pyc", "work"))
                if (backup / "LOCAL.md").is_file():
                    shutil.copy2(backup / "LOCAL.md", dst / "LOCAL.md")
            else:
                shutil.copy2(src, dst)
        except OSError:
            if dst.is_dir():
                shutil.rmtree(dst)
            elif dst.exists():
                dst.unlink()
            if backup.exists():
                shutil.move(str(backup), str(dst))
            raise
        print(f"  installed {'skill' if is_skill else 'agent'} {dst.name}")
    print("\nDone. In Codex, type: $roblox-skills-setup")
    print("Restart Codex if the skills or custom agents do not appear.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents/skills")
    parser.add_argument("--agents-dir", type=Path, default=Path(
        os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "agents")
    args = parser.parse_args()
    install(args.skills_dir, args.agents_dir)


if __name__ == "__main__":
    main()
