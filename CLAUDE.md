# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An MCP (Model Context Protocol) server that exposes the Conduit TX REST API as tools for Claude. It runs locally as a stdio process (no extra infra) and lets an LLM query jobs/flows/runs, trigger executions, and author flow graphs against a Conduit TX tenant.

## Architecture

The whole server is two files:

- `conduit_tx_mcp/client.py` — `ConduitClient`, a thin async httpx wrapper around the Conduit TX REST API. One method per endpoint, grouped by resource (tenants, jobs, job runs, flows, flow runs, connectors, connector configs, reference cache, transform preview, destination schemas). All requests funnel through `_request()`, which raises `RuntimeError(f"HTTP {status}: {detail}")` on non-2xx responses, extracting `detail` from the response body's `message` or `detail` field (Conduit TX's unified error envelope) or falling back to raw text.
- `conduit_tx_mcp/server.py` — FastMCP server. One `@mcp.tool()` per client method, organized into three use-case tiers (comments in the file mark the boundaries):
  - **UC1 — monitoring** (read-only): `list_tenants`, `get_tenant`, `list_jobs`, `get_job`, `list_job_runs`, `get_job_run`, `list_flows`, `get_flow`, `list_flow_runs`, `get_flow_run`, `list_connector_configs`, `get_ref_cache_status`
  - **UC2 — control** (read/write): `trigger_job`, `create_job`, `update_job`, `refresh_ref_cache`
  - **UC3 — flow authoring**: `list_connectors`, `get_connector`, `save_flow_graph`, `preview_transform`, `list_destination_schemas`

Every tool follows the same shape: call the matching `ConduitClient` method and return its result (`dict`/`list`) directly. Because the return type is a plain `dict`/`list` rather than a pre-serialized string, FastMCP auto-generates each tool's `outputSchema` and populates `CallToolResult.structuredContent`, instead of the model having to parse a JSON blob out of text content. On failure, catch `RuntimeError` and re-raise as `fastmcp.exceptions.ToolError(str(exc))`, which FastMCP converts into a proper `isError: true` tool result — errors are protocol-level, not a string convention the model has to pattern-match on. When adding a new endpoint, add the method to `client.py` first, then a corresponding tool in `server.py` using this same try/except/raise pattern.

Tools that take structured input the API expects as JSON (`save_flow_graph`'s `nodes_json`/`edges_json`, `preview_transform`'s `input_records_json`) accept it as a **JSON string parameter**, not a nested object — this is a FastMCP/tool-schema constraint (applies to inputs only; outputs are structured, see above). Each such tool does its own `json.loads` and raises `ToolError(f"invalid JSON — {exc}")` on parse failure, separate from the API-error path.

`create_job`/`update_job` build their request payload by conditionally including only non-empty/non-None fields — `update_job` explicitly rejects an all-empty call before hitting the API (`raise ToolError("no fields provided to update")`).

## Configuration

The server reads config at import time (`server.py` top level, not lazily), not via `.env` loading. `CONDUIT_TX_API_URL` is a required env var — missing it raises `KeyError` on startup. `CONDUIT_TX_API_TOKEN` is checked in the env first; if unset, it falls back to `keyring.get_password("conduit-tx-mcp-api-token", getpass.getuser())` (macOS Keychain / Windows Credential Manager / Linux Secret Service, via the `keyring` package). If neither source has a value, startup raises with a message naming the exact `keyring set` command to run — see `docs/desktop-token-keychain.md`. The entry point is `conduit_tx_mcp.server:main`, registered as the `conduit-tx-mcp` console script in `pyproject.toml`.

## Running / testing locally

There is no test suite, lint config, or CI in this repo yet.

Install in editable mode and run directly:

```bash
pip install -e .
CONDUIT_TX_API_URL=https://staging.conduit-tx.com CONDUIT_TX_API_TOKEN=<token> conduit-tx-mcp
```

To exercise it from Claude Code against a real Conduit TX instance:

```bash
CONDUIT_TX_API_URL=https://staging.conduit-tx.com CONDUIT_TX_API_TOKEN=<token> claude mcp add conduit-tx -- conduit-tx-mcp
```

Since this is a stdio MCP server with no HTTP surface of its own, the practical way to verify a change is to add it as above and drive it through natural-language prompts in a Claude session (see README's "Example prompts"), or call `ConduitClient` methods directly in a Python REPL against a real/staging Conduit TX instance.
