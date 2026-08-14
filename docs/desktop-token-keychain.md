# Desktop token setup: how the Keychain wrapper works

This documents the actual token setup running for Claude Desktop, beyond what the README's quickstart snippet shows — why it's structured this way, and a gotcha specific to machines where this repo's checkout lives on a non-boot volume.

## Why not just put the token in `claude_desktop_config.json`?

`claude_desktop_config.json` has no secret-store integration — whatever's in `mcpServers.conduit-tx.env` is static plaintext on disk, readable by anything that can read that file. `scripts/keychain-wrapper.sh` keeps `CONDUIT_TX_API_TOKEN` out of it: the token lives in the macOS Keychain instead, and the wrapper fetches it at launch.

## How it works

1. **One-time**, the token is stored in the Keychain as a generic password:
   ```bash
   security add-generic-password -a "$(whoami)" -s "conduit-tx-mcp-api-token" -w "<your-token>"
   ```
2. Claude Desktop's config points `command` at the wrapper script instead of `conduit-tx-mcp` directly, and drops `CONDUIT_TX_API_TOKEN` from `env` (`CONDUIT_TX_API_URL` stays — it isn't a secret).
3. At launch, the wrapper runs `security find-generic-password ... -w` to read the token back out of the Keychain, exports it as `CONDUIT_TX_API_TOKEN`, and `exec`s `conduit-tx-mcp`.

The script uses `whoami`, not the `$USER` env var — Claude Desktop launches MCP servers with only the specific env vars listed in its config, not a full inherited shell environment, so `$USER` is unset in that context and would make the Keychain lookup fail silently on account mismatch.

**What this does and doesn't protect against:** it protects the token from anything reading `claude_desktop_config.json` at rest. It does not protect against a fully compromised login session — the Keychain unlocks with your Mac account, same as the config file would be readable in that scenario.

## Gotcha: this repo's checkout lives on `/Volumes/Data`, a non-boot volume

If your `conduit-tx-mcp` clone is on a secondary/external volume (e.g. `/Volumes/Data/...` rather than under `/Users/<you>/...` or a Homebrew-managed path), Claude Desktop's spawned MCP processes cannot read or execute *anything* on that volume — confirmed by testing both a direct script exec and `/bin/bash <script-on-other-volume>` as the launcher; both failed with `Operation not permitted`. This isn't about which binary does the reading, and it can't be reproduced by testing from a Terminal session, since Terminal isn't sandboxed the same way Desktop's child processes are.

Two things follow from this, both already applied on this machine:

- **The wrapper script Desktop actually runs is a boot-volume copy**, not the one in this repo. It lives at `~/.local/bin/conduit-tx-mcp-keychain-wrapper.sh` and is functionally identical to `scripts/keychain-wrapper.sh` here — but it's a real copy, not a symlink (a symlink would still resolve reads through to the blocked volume). If you edit `scripts/keychain-wrapper.sh`, you have to manually re-copy it to the boot-volume location; it's intentionally not git-tracked from there.
- **`conduit-tx-mcp` must be installed non-editable** (`pip install /path/to/conduit-tx-mcp --break-system-packages`, no `-e`). An editable install's `.pth` link points straight back at this repo's `conduit_tx_mcp/` source — so even with the wrapper script relocated, `exec conduit-tx-mcp` would hit the same cross-volume block one import deeper. A regular install copies the actual `.py` files into `site-packages` on the boot volume, removing any runtime dependency on the other volume being reachable.

Practical consequence: after merging a `conduit-tx-mcp` PR, `git pull` alone doesn't update what Desktop is running. Re-run the non-editable install to refresh the boot-volume copy, and re-copy `scripts/keychain-wrapper.sh` to `~/.local/bin/` if it changed.

If your checkout is under your home directory or another boot-volume path, none of this section applies — point Desktop's `command` straight at `scripts/keychain-wrapper.sh` and use a normal (or editable, if you want live-reload during development) install.
