#!/usr/bin/env bash
# Launches conduit-tx-mcp with CONDUIT_TX_API_TOKEN pulled from the macOS
# Keychain instead of a plaintext env var in claude_desktop_config.json.
#
# One-time setup:
#   security add-generic-password -a "$USER" -s "conduit-tx-mcp-api-token" -w "<your-token>"
#
# Then point Claude Desktop's mcpServers.conduit-tx.command at this script's
# absolute path and drop CONDUIT_TX_API_TOKEN from its env block (keep
# CONDUIT_TX_API_URL there — it isn't a secret).
set -euo pipefail

CONDUIT_TX_API_TOKEN="$(security find-generic-password -a "$USER" -s "conduit-tx-mcp-api-token" -w)"
export CONDUIT_TX_API_TOKEN

exec conduit-tx-mcp
