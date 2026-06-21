# Tool Links And Install Commands

Use this file when `SKILL.md` selects a tool that is missing locally. Install only the chosen
tool or smallest chosen stack, then verify it before using it.

Prerequisites by installer: `serena` and `graphify` need `uv`; `rtk` needs Homebrew or Cargo
unless using the upstream shell installer; `caveman` needs Node >=18 for some agent targets.

## Defaults

| Tool | Use for | Recommended install | Verify | Notes |
|------|---------|---------------------|--------|-------|
| [serena](https://github.com/oraios/serena) | Symbol-aware code comprehension and edits | `uv tool install -p 3.13 serena-agent` then `serena init` | `serena --help` | Requires `uv`; language-server dependencies may be needed per language. Configure the MCP client after install. |
| [graphify](https://github.com/safishamsi/graphify) | Code graph navigation, call paths, impact analysis | `uv tool install graphifyy` then `graphify install` | `graphify --help` | PyPI package is `graphifyy` with double `y`; CLI is `graphify`. Use extras only for needed non-code inputs. |
| [rtk](https://github.com/rtk-ai/rtk) | Compressing verbose command output | `brew install rtk` on Homebrew systems, otherwise `cargo install --git https://github.com/rtk-ai/rtk` | `rtk --help` | The upstream quick installer is `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh \| sh`; only use curl-to-shell with explicit approval. |
| [caveman](https://github.com/juliusbrussee/caveman) | Output-token reduction | `curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh \| bash` | Start a new agent session and trigger `/caveman` | Installs agent skills/commands rather than a normal development CLI. Use only with explicit approval for curl-to-shell. |

## Optional variants

- `graphify`: install extras only when the task needs them, for example
  `uv tool install "graphifyy[mcp]"`, `uv tool install "graphifyy[sql]"`, or
  `uv tool install "graphifyy[office]"`.
- `rtk`: on Linux/macOS without Homebrew or Cargo, use the upstream quick installer above if
  the user approves network shell execution. It installs to `~/.local/bin`; add that to `PATH`
  only if verification cannot find `rtk`.
- `caveman`: Windows PowerShell installer is
  `irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex`.

## Selection rule

Do not install every tool. Choose one of `serena` or `graphify`, then add `rtk` and/or
`caveman` only when their layer is the bottleneck.
