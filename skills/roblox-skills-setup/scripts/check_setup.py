"""Check this machine for everything the Roblox skills use, and report what is missing.

    python check_setup.py           # human-readable table
    python check_setup.py --json    # for the setup skill to read

Reads only. Installs nothing, changes nothing. Secret values are NEVER printed:
for an API key it reports only whether the environment variable is set.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import tomllib
from pathlib import Path

HOME = Path.home()
CODEX_HOME = Path(os.environ.get("CODEX_HOME") or HOME / ".codex")
SKILLS_DIR = Path(os.environ.get("ROBLOX_SKILLS_DIR") or Path(__file__).resolve().parents[2])
AGENTS_DIR = CODEX_HOME / "agents"

SKILLS = [
    "roblox-skills-setup", "create-roblox-game", "roblox-build-orchestrator", "roblox-code", "roblox-map", "roblox-ui",
    "roblox-vfx", "roblox-sfx", "roblox-animation", "roblox-3d-model", "roblox-texture-gen",
]

# tool -> (needed by, how to get it)
TOOLS = {
    "python": ("everything", "https://www.python.org/downloads/ (3.11 or newer)"),
    "rojo": ("roblox-code, create-roblox-game", "https://rojo.space (or install with rokit/aftman)"),
    "wally": ("roblox-code (packages such as Knit)", "https://wally.run"),
    "lune": ("roblox-code (headless tests)", "https://lune-org.github.io/docs"),
    "selene": ("roblox-code (lint)", "https://github.com/Kampfkarren/selene"),
    "stylua": ("roblox-code (format)", "https://github.com/JohnnyMorganz/StyLua"),
    "blender": ("roblox-3d-model, roblox-animation", "https://www.blender.org/download/ (4.x)"),
    "node": ("roblox-3d-model hard-surface route only", "https://nodejs.org (optional)"),
    "ffmpeg": ("contact sheets / previews (optional)", "https://ffmpeg.org (optional)"),
}

# env var -> (needed by, required?)
ENV = {
    "ROBLOX_API_KEY": ("permanent uploads of meshes/images/animations (Open Cloud key, free)", False),
    "ROBLOX_USER_ID": ("Open Cloud uploads go to this creator", False),
    "ROBLOX_GROUP_ID": ("upload to a group instead of a user (optional)", False),
    "HF_TOKEN": ("roblox-3d-model on a Hugging Face Space", False),
    "CF_ACCOUNT_ID": ("concept images / icons via Cloudflare Workers AI (free tier)", False),
    "CF_API_TOKEN": ("pairs with CF_ACCOUNT_ID", False),
    "KILN_HOME": ("roblox-3d-model hard-surface route (optional)", False),
}


def find_tool(name: str) -> str | None:
    hit = shutil.which(name) or shutil.which(name + ".exe")
    if hit:
        return hit
    extra = [HOME / ".rokit" / "bin", HOME / ".aftman" / "bin", HOME / ".cargo" / "bin"]
    if name == "blender":
        roots = [Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blender Foundation",
                 Path("/Applications/Blender.app/Contents/MacOS")]
        for r in roots:
            if r.exists():
                found = sorted(r.rglob("blender.exe")) + sorted(r.glob("Blender"))
                if found:
                    return str(found[-1])
    if name == "python":
        return sys.executable
    for d in extra:
        for cand in (d / name, d / (name + ".exe")):
            if cand.exists():
                return str(cand)
    return None


def studio_mcp(configs: list[Path] | None = None) -> str:
    """Inspect Codex TOML registrations, reporting server names only, never values."""
    if configs is None:
        configs = [CODEX_HOME / "config.toml"]
        for folder in (*reversed(Path.cwd().parents), Path.cwd()):
            configs.append(folder / ".codex" / "config.toml")
    registered = {}
    for cfg in dict.fromkeys(configs):
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        servers = data.get("mcp_servers", {})
        if not isinstance(servers, dict):
            continue
        for name, settings in servers.items():
            if isinstance(settings, dict):
                registered.setdefault(name, {}).update(settings)
    hits = sorted(name for name, settings in registered.items()
                  if ("roblox" in name.lower() or "studio" in name.lower())
                  and settings.get("enabled", True))
    if hits:
        return (f"registered as {', '.join(hits)} (in config.toml); registration is not a "
                "connection test. Confirm with `codex mcp list` and a live Studio state call")
    return ("not found in local Codex TOML config. A desktop connector or plugin may provide it: "
            "discover the current tools, call list_roblox_studios, then get_studio_state. "
            "If unavailable, enable Studio's MCP server and connect it in Codex")


def main() -> int:
    rows = {"platform": f"{platform.system()} {platform.release()}", "python": sys.version.split()[0],
            "tools": {}, "env": {}, "skills": {}, "agents": [], "studio_mcp": studio_mcp()}
    for t, (need, how) in TOOLS.items():
        rows["tools"][t] = {"path": find_tool(t), "needed_by": need, "get": how}
    for k, (need, _) in ENV.items():
        rows["env"][k] = {"set": bool(os.environ.get(k)), "needed_by": need}
    for s in SKILLS:
        d = SKILLS_DIR / s
        tpl = d / "LOCAL.template.md"
        text = tpl.read_text(encoding="utf-8", errors="replace").lower() if tpl.exists() else ""
        rows["skills"][s] = {"installed": (d / "SKILL.md").exists(),
                             "LOCAL.md": (d / "LOCAL.md").exists(),
                             "template": tpl.exists(),
                             # a template that says it needs nothing is ready as installed
                             "needs_settings": s != "roblox-skills-setup" and (not tpl.exists() or not any(
                                 k in text for k in ("needs no machine-specific", "needs nothing machine-specific")))}
    rows["agents"] = sorted(p.stem for p in AGENTS_DIR.glob("roblox-*.toml")) if AGENTS_DIR.exists() else []

    if "--json" in sys.argv:
        print(json.dumps(rows, indent=1))
        return 0
    print(f"Platform: {rows['platform']}   Python: {rows['python']}")
    print(f"Roblox Studio MCP: {rows['studio_mcp']}\n")
    print("TOOLS")
    for t, r in rows["tools"].items():
        mark = "ok " if r["path"] else "-- "
        print(f"  {mark}{t:8s} {r['path'] or 'missing  -> ' + r['get']}   ({r['needed_by']})")
    print("\nENV VARS (values never shown)")
    for k, r in rows["env"].items():
        print(f"  {'set' if r['set'] else '-- '} {k:16s} {r['needed_by']}")
    print("\nSKILLS")
    for s, r in rows["skills"].items():
        state = ("missing" if not r["installed"] else "configured" if r["LOCAL.md"]
                 else "needs LOCAL.md" if r["needs_settings"] else "ready (no settings needed)")
        print(f"  {s:28s} {state}")
    print(f"\nAGENTS: {', '.join(rows['agents']) or 'none installed'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
