# Putting the MCP back (optional)

`Attrom/spine-mpc-attrom` is an MCP server around the Spine CLI. This skill does
not need an MCP host - every capability is a CLI that any agent can call - but if
your client is MCP-only, wrap these commands instead of running the upstream
server, which expects its own TypeScript build and ingestion corpus.

A minimal stdio wrapper, one tool per command:

| MCP tool | command |
| --- | --- |
| `spine_validate` | `python scripts/spine_toolkit.py validate <json> --atlas <atlas> --json` |
| `spine_inspect` | `python scripts/spine_toolkit.py inspect <json> --json` |
| `spine_doc` | `python scripts/spine_toolkit.py doc <json> --out <md>` |
| `spine_diff` | `python scripts/spine_toolkit.py diff <a.json> <b.json> --json` |
| `spine_transform` | `python scripts/spine_toolkit.py transform <json> --set <name>=<arg> --preview` |
| `spine_roundtrip` | `python scripts/spine_toolkit.py roundtrip <json> --gate --to-version 3.8.75` |
| `spine_report` | `python scripts/spine_toolkit.py report <dir> --json` |
| `spine_export` | `python scripts/spine_export.py --layout <layout.json> --out <dir> --gate --json` |
| `spine_preview` | `python scripts/make_preview.py --package <json> --reference <png> --json` |
| `spine_gen_parts` | `python scripts/gen_parts.py --reference <png> --parts <list> --out <dir> --json` |

Rules that keep the wrapper honest:

* Shell out with a list of arguments, never a shell string; paths contain spaces
  and CJK characters.
* Pass `--json` and forward the payload unchanged. Do not re-word it: the fields
  are the contract (`ok`, `errors`, `warnings`, `changes`, `positioning_score`).
* Return the process exit code. `0` pass, `2` a real finding, `1` a usage error.
* Give image-generating tools an explicit opt-in. `gen_parts.py --dry-run`
  prints the plan and spends nothing; a default-on MCP tool would burn quota on
  every call an agent makes.
* Never expose the image tool's API key through a tool argument, a log line or a
  result payload.

## Why this skill is CLI-first

* A text-only model driving a long task needs to re-run the same step with one
  changed parameter. That is a shell command, not a protocol round trip.
* Output is diffable: `--json`, plus reports written next to the artifacts.
* Every step is reproducible by a human without the agent, which is what makes
  the result reviewable.
* Failure is legible. `spine_cli.py` prints the CLI's own stderr, so the
  "welcome data download failed" noise and a genuine import error are separable.
