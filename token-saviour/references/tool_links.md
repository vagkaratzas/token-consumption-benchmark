# Tool Links And Install Commands

Use this file when `SKILL.md` selects a tool that is missing locally. Install only the chosen
tool or smallest chosen stack, then verify it before using it.

Prerequisites by installer: `serena` and `graphify` need `uv`; `codegraph` needs Node >=18
(`npm`); `rtk` needs Homebrew or Cargo unless using the upstream shell installer; `caveman` and
`ponytail` need Node >=18 for some agent targets.

## Defaults

The three code-read tools (`serena` / `graphify` / `codegraph`) target the **same** layer —
install at most one. `rtk`, `caveman`, and `ponytail` each own a distinct layer and stack
cleanly on top.

| Tool | Layer / use for | Recommended install | Verify | Notes |
|------|-----------------|---------------------|--------|-------|
| [serena](https://github.com/oraios/serena) | code-read input — symbol comprehension **and edits** | `uv tool install -p 3.13 serena-agent` then `serena init` | `serena --help` | Requires `uv`; language-server deps may be needed per language. Configure the MCP client after install. The only code-read tool that also does semantic edits/renames. |
| [graphify](https://github.com/safishamsi/graphify) | code-read input — navigation, call paths, impact | `uv tool install graphifyy` then `graphify install` | `graphify --help` | PyPI package is `graphifyy` (double `y`); CLI is `graphify`. Best at call-path tracing. |
| [codegraph](https://github.com/colbymchenry/codegraph) | code-read input — indexed graph, returns source inline | `npm i -g @colbymchenry/codegraph` then `codegraph init <path>` | `codegraph --help` | Single CLI, local SQLite index, no API key. `node`/`callers`/`impact`/`explore`. Best at pinpoint caller lookups; `explore` returns verbatim source (heavier per call, saves follow-up reads). **Skip `codegraph install`** unless you want it to auto-wire MCP into your agent configs. Set `CODEGRAPH_TELEMETRY=0` to disable telemetry. |
| [rtk](https://github.com/rtk-ai/rtk) | command-output input — compress verbose stdout | `brew install rtk`, otherwise `cargo install --git https://github.com/rtk-ai/rtk` | `rtk --help` | Upstream quick installer: `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh \| sh`; only use curl-to-shell with explicit approval. |
| [caveman](https://github.com/juliusbrussee/caveman) | prose output — terse replies | `curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh \| bash` | Start a new session and trigger `/caveman` | Installs agent skills/commands, not a dev CLI. Compresses prose; leaves code blocks ~unchanged. Use only with explicit approval for curl-to-shell. |
| [ponytail](https://github.com/DietrichGebert/ponytail) | code output — minimal/YAGNI code generation | Claude Code: `/plugin marketplace add DietrichGebert/ponytail` then `/plugin install ponytail@ponytail` | `/ponytail` in-session | Behavioural plugin (no dev CLI). Biases the agent toward minimal code; bites only when you generate/edit code, ~0 on prose. Levels `lite\|full\|ultra`. |

## Optional variants

- `graphify`: install extras only when needed, for example
  `uv tool install "graphifyy[mcp]"`, `uv tool install "graphifyy[sql]"`, `uv tool install "graphifyy[office]"`.
- `codegraph`: one-liner installer (bundles its own runtime, no system Node) is
  `curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh`
  (Windows: `irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex`);
  use curl-to-shell only with explicit approval.
- `rtk`: on Linux/macOS without Homebrew or Cargo, use the upstream quick installer above (with
  approval). It installs to `~/.local/bin`; add that to `PATH` only if verification can't find `rtk`.
- `caveman`: Windows PowerShell installer is
  `irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex`.
- `ponytail`: also installable for Codex / Copilot CLI / Gemini / OpenCode — see the repo README.

## Selection rule

Do not install every tool. Choose **one** code-read tool (`serena` for broad reading + edits,
`graphify` for navigation/call-paths, `codegraph` for a single-binary indexed graph that returns
source inline), then add `rtk` (command-heavy work), `caveman` (chatty prose output), and/or
`ponytail` (code-generation work) only when their layer is the bottleneck.
