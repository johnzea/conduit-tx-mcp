# Desktop token setup: how the OS credential store fallback works

This documents the actual token setup running for Claude Desktop, beyond what the README's quickstart snippet shows — why it's structured this way, and a packaging gotcha specific to machines where this repo's checkout lives on a non-boot volume (macOS).

## Why not just put the token in `claude_desktop_config.json`?

`claude_desktop_config.json` has no secret-store integration — whatever's in `mcpServers.conduit-tx.env` is static plaintext on disk, readable by anything that can read that file.

## How it works

`conduit_tx_mcp/server.py` reads `CONDUIT_TX_API_TOKEN` from the environment as before, but if it's unset, falls back to the [`keyring`](https://pypi.org/project/keyring/) package — which abstracts macOS Keychain, Windows Credential Manager, and the Linux Secret Service/KWallet behind one API — looking up the token under service `conduit-tx-mcp-api-token` and the current OS username (`getpass.getuser()`).

1. **One-time**, store the token in your OS credential store:
   ```bash
   python3 -m keyring set conduit-tx-mcp-api-token <your-os-username>   # macOS/Linux
   python -m keyring set conduit-tx-mcp-api-token <your-os-username>    # Windows
   ```
2. Drop `CONDUIT_TX_API_TOKEN` from Claude Desktop's `env` block entirely (`CONDUIT_TX_API_URL` stays — it isn't a secret). `command` is plain `conduit-tx-mcp`, same as the non-Keychain setup — no wrapper script involved.
3. At import time, `server.py` checks the env var first, then `keyring.get_password("conduit-tx-mcp-api-token", getpass.getuser())`. If neither has a value, it raises with a message telling you the exact `keyring set` command to run.

This works identically on macOS, Windows, and Linux — there's no per-OS wrapper script to maintain (an earlier version of this setup used a macOS-only bash script calling `security` directly; it's been replaced by this in-process fallback).

**What this does and doesn't protect against:** it protects the token from anything reading `claude_desktop_config.json` at rest. It does not protect against a fully compromised login session — the credential store unlocks with your OS account, same as the config file would be readable in that scenario.

## Packaging gotcha (macOS): non-boot-volume checkouts

This section only matters if your `conduit-tx-mcp` clone is on a secondary/external volume (e.g. mounted at `/Volumes/<name>` rather than under `/Users/<you>/...` or a Homebrew-managed path).

Claude Desktop's spawned MCP processes cannot read or execute *anything* on such a volume — confirmed by testing both a direct script exec and `/bin/bash <script-on-other-volume>` as the launcher; both failed with `Operation not permitted`. This isn't about which binary does the reading, and it can't be reproduced by testing from a Terminal session, since Terminal isn't sandboxed the same way Desktop's child processes are.

Consequence: **`conduit-tx-mcp` must be installed non-editable** (`pip install /path/to/conduit-tx-mcp --break-system-packages`, no `-e`). An editable install's `.pth` link points straight back at this repo's `conduit_tx_mcp/` source on the blocked volume; a regular install copies the actual `.py` files into `site-packages` on the boot volume, removing any runtime dependency on the other volume being reachable. `command` can then be plain `conduit-tx-mcp` (resolved via PATH to a boot-volume location like `/opt/homebrew/bin/conduit-tx-mcp`) with no wrapper script needed.

Practical consequence: after merging a `conduit-tx-mcp` PR, `git pull` alone doesn't update what Desktop is running — re-run the non-editable install to refresh the boot-volume copy.

If your checkout is under your home directory or another boot-volume path, none of this applies — a normal (or editable, for live-reload during development) install works fine.
