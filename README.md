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

#### macOS: keeping the token out of the config file (recommended)

The config above puts `CONDUIT_TX_API_TOKEN` in plaintext in `claude_desktop_config.json`. On macOS you can keep it in the Keychain instead and have a wrapper script inject it at launch:

```bash
security add-generic-password -a "$(whoami)" -s "conduit-tx-mcp-api-token" -w "<your-token>"
```

Then point `command` at `scripts/keychain-wrapper.sh` (absolute path to your clone) instead of `conduit-tx-mcp`, and drop `CONDUIT_TX_API_TOKEN` from `env` (`CONDUIT_TX_API_URL` isn't a secret, so it stays):

```json
{
  "mcpServers": {
    "conduit-tx": {
      "command": "/absolute/path/to/conduit-tx-mcp/scripts/keychain-wrapper.sh",
      "env": {
        "CONDUIT_TX_API_URL": "https://staging.conduit-tx.com"
      }
    }
  }
}
```

This only protects the token from anything reading the config file at rest — it doesn't help if your Mac login itself is compromised, since the Keychain unlocks with that.

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
| `CONDUIT_TX_API_TOKEN` | Long-lived API token from Settings → API Tokens |

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
