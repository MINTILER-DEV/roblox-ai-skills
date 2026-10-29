# SyphoDev Roblox Skills for Codex (free)

A set of Codex skills and agents for making Roblox games with AI: code,
UI, maps, 3D models, textures, VFX, SFX, animation, and a front door that
takes one game idea through research, design, build and playtest.

Free, as promised at 1,000 subscribers. Thank you for watching.

## What is in the pack

| Skill | What it does |
|---|---|
| `create-roblox-game` | The front door. One design file to a playable game, stage by stage |
| `roblox-build-orchestrator` | Runs the asset stages in parallel with sub-agents and logs the build |
| `roblox-code` | Scaffolds a Rojo + Knit project and proves code with 4 no-Studio gates |
| `roblox-ui` | Builds GUI from a JSON spec: PNG mockup, Rojo model file and Luau builder |
| `roblox-map` | Lays out maps from a spec and PROVES they are playable (reach, falls, sightlines) |
| `roblox-3d-model` | Text or image to a game-ready MeshPart, through Blender |
| `roblox-texture-gen` | Generates textures for your meshes and parts |
| `roblox-vfx` | Harvests particle effects from packs you own into a searchable library |
| `roblox-sfx` | Finds and wires sound effects |
| `roblox-animation` | Authors R15/R6 animations headlessly in Blender from a pose spec |
| `roblox-skills-setup` | Sets everything up on YOUR machine. Run this first |

Plus 7 native Codex custom agents (`skills/roblox-build-orchestrator/agents/*.toml`).

## Install

1. Install [Codex](https://developers.openai.com/codex/) and Roblox Studio.
2. Clone or unzip this folder anywhere. Install Python 3.11+ first.
3. Windows: run `powershell -ExecutionPolicy Bypass -File .\install.ps1`.
   macOS / Linux: run `bash install.sh`.
4. In Codex, type `$roblox-skills-setup`. Restart Codex if it does not appear.

The installers copy all 11 skills to `~/.agents/skills/` and the seven TOML
agents to `$CODEX_HOME/agents/` (default `~/.codex/agents/`). Existing versions
are backed up alongside the destination, and each skill's `LOCAL.md` is preserved.
Your Codex configuration and MCP registrations are left untouched.

For a repository-only installation, use:

```powershell
.\install.ps1 -SkillsDir "C:\path\to\game\.agents\skills" -AgentsDir "C:\path\to\game\.codex\agents"
```

```bash
bash install.sh --skills-dir /path/to/game/.agents/skills --agents-dir /path/to/game/.codex/agents
```

For manual installation, copy `skills/*` to the skills directory and
`skills/roblox-build-orchestrator/agents/*.toml` to the agents directory.
[Codex skill discovery](https://developers.openai.com/codex/skills/) and
[custom agent configuration](https://developers.openai.com/codex/multi-agent/)
describe these formats. Script examples use the default user skills directory;
for a custom location, substitute the path from Codex's skill catalog. Helpers
resolve sibling skills from their own installation; `ROBLOX_SKILLS_DIR` can
explicitly select an alternate pack root for setup and preflight.

The setup skill checks what you have installed, tells you what each missing
tool is for, and writes a `LOCAL.md` inside each skill with YOUR folders and
tool paths. You never have to edit a skill by hand. Run it again any time you
move things or install something new.

Then start a game: `$create-roblox-game make me a tycoon game`, or call any
single skill by name ("use roblox-ui to make a shop screen").

## Codex workflow

All original scripts, templates, references and Roblox asset pipelines are retained.
The Claude-specific agent metadata has been replaced by Codex TOML. Workers inherit
the parent model; no Anthropic model names or fixed Codex model are required.
The orchestrator uses native or generic subagents where available and falls back
to sequential stages when delegation is unavailable. It keeps one Studio writer.
Codex agents inherit MCP access: the file-only worker rule is an instruction,
not a tool sandbox. Studio-dependent fallbacks return to the manager.

Connect Roblox Studio through Codex's MCP settings or a Studio connector. For a
local server, use `codex mcp add <name> -- <server-command> [args...]` with the
command shown by Studio, then `codex mcp list`. The setup checker reads Codex
`config.toml` server names without showing credentials, but only a live Studio
call proves connectivity. No MCP server is bundled or automatically registered.
See [Codex MCP configuration](https://developers.openai.com/codex/mcp/).

Builds retain six-section handoffs and the original quality gates. This port does
not imply the external generation services or your Studio installation were tested.

## Validate the port

Run `python -m unittest discover -s tests -v`. The offline checks cover fresh and
repeat installation, settings preservation, backup placement, rollback after a
copy failure, Codex MCP configuration reporting, and scaffolding from an installed
pack. They also exercise PowerShell and Bash entry points when available.
These checks do not start Studio, call generation services, or upload assets.

## What you need

Not everything is needed for everything. The setup skill only asks about the
parts you want.

- **Always:** Codex, Roblox Studio with its official MCP enabled, Python 3.11+.
- **Code:** Rojo, Wally, Lune, Selene, StyLua (all free).
- **3D models and animation:** Blender 4.x, and a free Hugging Face account for
  the mesh-generation step. **Do not use Kaggle**: see below.
- **Permanent uploads (optional):** a free Roblox Open Cloud API key.

## Kaggle is off (2026-10-19)

Earlier versions of these skills ran the 3D mesh step (and an icon test) on free
Kaggle GPUs. **Don't.** Kaggle's Terms of Use only allow "internal, personal,
non-commercial use", and its Acceptable Use Policy (kaggle.com/aup) bans using its
resources for "server farming" or "activity unrelated to ML data science". Running
this pipeline there got my account banned for "resource abuse".

The Kaggle scripts now stop with a message instead of running. If you set Kaggle up
already, stop using it for your game, and don't make a second Kaggle account (the
Terms ban that too). For now, hard-surface props go through Kiln and organic meshes
through a Hugging Face Space, one at a time. Details at the top of
`skills/roblox-3d-model/SKILL.md`. A checked replacement for batches is coming.

## Things to know

- **Your keys stay yours.** Skills read API keys from environment variables.
  Nothing in this pack asks you to paste a key into a file or a chat.
- **VFX ships empty on purpose.** `roblox-vfx` is a harvester. You take free
  VFX packs into your own Roblox account and it builds your library from
  them. The setup skill walks you through it. Check each pack's terms before
  publishing a game with its effects.
- **Model licences matter.** Read `skills/roblox-3d-model/references/licences.md`
  before generating models; some AI model licences exclude some regions or uses.
- **`LOCAL.md` is personal.** If you share your own version of a skill, leave
  it out.

## Licence

See `LICENSE.txt`.
