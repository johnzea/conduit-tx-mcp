# conduit-tx-mcp

MCP server for [Conduit TX](https://conduit-tx.com). Connects Claude to your Conduit TX environment so you can query jobs, inspect flow runs, trigger executions, and author flows using natural language.

Runs locally as a stdio process — no extra infrastructure required.

## Installation

```bash
pip install git+https://github.com/johnzea/conduit-tx-mcp.git
```

Or with `uv`:

```bash
uv pip install git+https://github.com/johnzea/conduit-tx-mcp.git
```

## Setup

### 1. Generate an API token

Log in to the Conduit TX web app and go to **Settings → API Tokens**. Create a new token (e.g. `MCP - Claude Desktop`). Copy it immediately — it is shown only once.

### 2. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "conduit-tx": {
      "command": "conduit-tx-mcp",
      "env": {
        "CONDUIT_TX_API_URL": "https://staging.conduit-tx.com",
        "CONDUIT_TX_API_TOKEN": "<your-token>"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

#### Keeping the token out of the config file (recommended)

The config above puts `CONDUIT_TX_API_TOKEN` in plaintext in `claude_desktop_config.json`. Instead, you can store it in your OS credential store — macOS Keychain, Windows Credential Manager, or the Linux Secret Service/KWallet — and the server will find it automatically when the env var isn't set, via the [`keyring`](https://pypi.org/project/keyring/) package (installed as a dependency, works the same on every OS):

```bash
python3 -m keyring set conduit-tx-mcp-api-token <your-os-username>
# prompts for the token value
```

Then drop `CONDUIT_TX_API_TOKEN` from `env` entirely (`CONDUIT_TX_API_URL` isn't a secret, so it stays) — `command` goes back to plain `conduit-tx-mcp`, no wrapper script needed:

```json
{
  "mcpServers": {
    "conduit-tx": {
      "command": "conduit-tx-mcp",
      "env": {
        "CONDUIT_TX_API_URL": "https://staging.conduit-tx.com"
      }
    }
  }
}
```

This only protects the token from anything reading the config file at rest — it doesn't help if your OS login itself is compromised, since the credential store unlocks with that.

See [docs/desktop-token-keychain.md](docs/desktop-token-keychain.md) for how this works in detail, including a packaging gotcha if your clone lives on a non-boot volume (macOS).

### 3. Configure Claude Code

```bash
CONDUIT_TX_API_URL=https://staging.conduit-tx.com \
CONDUIT_TX_API_TOKEN=<your-token> \
claude mcp add conduit-tx -- conduit-tx-mcp
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `CONDUIT_TX_API_URL` | Base URL of your Conduit TX instance |
| `CONDUIT_TX_API_TOKEN` | Long-lived API token from Settings → API Tokens. Optional if one is stored in your OS credential store — see above. |

## Available tools

### Monitoring
`list_tenants` · `get_tenant` · `list_jobs` · `get_job` · `list_job_runs` · `get_job_run` · `list_flows` · `get_flow` · `list_flow_runs` · `get_flow_run` · `list_connector_configs` · `get_ref_cache_status`

### Control
`trigger_job` · `create_job` · `update_job` · `refresh_ref_cache`

### Flow authoring
`list_connectors` · `get_connector` · `save_flow_graph` · `preview_transform` · `list_destination_schemas`

## Example prompts

```
List all jobs for tenant acme-corp
Show me the last 5 runs for the WF Account Balances job — did any fail?
Trigger the WF Account Balances job for tenant acme-corp
List all connectors and their fetch parameter schemas
Help me build a map_fields config for a new balance flow
```

## Revoking a token

Go to **Settings → API Tokens** in the Conduit TX web app and click **Revoke**. The token is invalidated immediately.
