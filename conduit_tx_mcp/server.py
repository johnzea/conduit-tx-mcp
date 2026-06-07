"""Conduit TX MCP server.

Exposes Conduit TX REST API operations as Claude tools via the MCP stdio transport.

Environment variables (required):
    CONDUIT_TX_API_URL    Base URL of your Conduit TX instance
                          e.g. https://staging.conduit-tx.com
    CONDUIT_TX_API_TOKEN  Long-lived API token from Settings → API Tokens
"""

import json
import os

from fastmcp import FastMCP

from conduit_tx_mcp.client import ConduitClient

API_URL = os.environ["CONDUIT_TX_API_URL"]
API_TOKEN = os.environ["CONDUIT_TX_API_TOKEN"]

mcp = FastMCP("conduit-tx")
client = ConduitClient(API_URL, API_TOKEN)


def _ok(data) -> str:
    return json.dumps(data, default=str, indent=2)


def _err(exc: Exception) -> str:
    return f"Error: {exc}"


# ===========================================================================
# UC1 — Operational monitoring (read-only)
# ===========================================================================


@mcp.tool()
async def list_tenants() -> str:
    """List all tenants."""
    try:
        return _ok(await client.list_tenants())
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_tenant(tenant_id: str) -> str:
    """Get a single tenant by ID."""
    try:
        return _ok(await client.get_tenant(tenant_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def list_jobs(tenant_id: str) -> str:
    """List all job definitions for a tenant."""
    try:
        return _ok(await client.list_jobs(tenant_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_job(tenant_id: str, job_id: str) -> str:
    """Get a job definition by ID."""
    try:
        return _ok(await client.get_job(tenant_id, job_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def list_job_runs(tenant_id: str, job_id: str, limit: int = 10) -> str:
    """List recent runs for a job. Returns up to `limit` runs (default 10)."""
    try:
        return _ok(await client.list_job_runs(tenant_id, job_id, limit=limit))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_job_run(tenant_id: str, run_id: str) -> str:
    """Get a job run by ID, including all node run outputs."""
    try:
        return _ok(await client.get_job_run(tenant_id, run_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def list_flows(tenant_id: str, job_id: str) -> str:
    """List all flows for a job."""
    try:
        return _ok(await client.list_flows(tenant_id, job_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_flow(tenant_id: str, job_id: str, flow_id: str) -> str:
    """Get a flow with its full node/edge graph."""
    try:
        return _ok(await client.get_flow(tenant_id, job_id, flow_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def list_flow_runs(tenant_id: str, run_id: str) -> str:
    """List all flow runs for a job run."""
    try:
        return _ok(await client.list_flow_runs(tenant_id, run_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_flow_run(tenant_id: str, flow_run_id: str) -> str:
    """Get a flow run by ID, including per-node status and output_json."""
    try:
        return _ok(await client.get_flow_run(tenant_id, flow_run_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def list_connector_configs(tenant_id: str) -> str:
    """List all connector configurations for a tenant."""
    try:
        return _ok(await client.list_connector_configs(tenant_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_ref_cache_status(tenant_id: str) -> str:
    """Get the reference data cache status for a tenant."""
    try:
        return _ok(await client.get_ref_cache_status(tenant_id))
    except RuntimeError as exc:
        return _err(exc)


# ===========================================================================
# UC2 — Operational control (read + write)
# ===========================================================================


@mcp.tool()
async def trigger_job(tenant_id: str, job_id: str) -> str:
    """Trigger an immediate job run. Returns the new run ID and status."""
    try:
        return _ok(await client.trigger_job(tenant_id, job_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def create_job(
    tenant_id: str,
    name: str,
    description: str = "",
    schedule_cron: str = "",
    schedule_timezone: str = "America/New_York",
    source_connector_config_ids: list[str] | None = None,
    dest_connector_config_id: str = "",
    environment: str = "test",
) -> str:
    """Create a new job definition.

    Args:
        tenant_id: Tenant UUID
        name: Job name
        description: Optional description
        schedule_cron: Cron expression (e.g. "0 9 * * 1-5"); leave empty for manual-only
        schedule_timezone: Timezone for cron (default America/New_York)
        source_connector_config_ids: List of source connector config UUIDs
        dest_connector_config_id: Destination connector config UUID (or empty)
        environment: "test" or "production"
    """
    payload: dict = {
        "name": name,
        "schedule_timezone": schedule_timezone,
        "environment": environment,
        "source_connector_config_ids": source_connector_config_ids or [],
    }
    if description:
        payload["description"] = description
    if schedule_cron:
        payload["schedule_cron"] = schedule_cron
    if dest_connector_config_id:
        payload["dest_connector_config_id"] = dest_connector_config_id
    try:
        return _ok(await client.create_job(tenant_id, payload))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def update_job(
    tenant_id: str,
    job_id: str,
    name: str = "",
    description: str = "",
    schedule_cron: str = "",
    schedule_timezone: str = "",
    is_active: bool | None = None,
    environment: str = "",
) -> str:
    """Update fields on a job definition. Only non-empty values are sent.

    Args:
        tenant_id: Tenant UUID
        job_id: Job definition UUID
        name: New name (optional)
        description: New description (optional)
        schedule_cron: New cron expression (optional)
        schedule_timezone: New timezone (optional)
        is_active: Set active/inactive (optional)
        environment: "test" or "production" (optional)
    """
    payload: dict = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if schedule_cron:
        payload["schedule_cron"] = schedule_cron
    if schedule_timezone:
        payload["schedule_timezone"] = schedule_timezone
    if is_active is not None:
        payload["is_active"] = is_active
    if environment:
        payload["environment"] = environment
    if not payload:
        return "Error: no fields provided to update"
    try:
        return _ok(await client.update_job(tenant_id, job_id, payload))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def refresh_ref_cache(tenant_id: str, data_type: str) -> str:
    """Refresh a specific reference data cache type for a tenant.

    Args:
        tenant_id: Tenant UUID
        data_type: Cache type to refresh (e.g. "bank_accounts", "cost_centers")
    """
    try:
        return _ok(await client.refresh_ref_cache(tenant_id, data_type))
    except RuntimeError as exc:
        return _err(exc)


# ===========================================================================
# UC3 — AI-assisted flow authoring
# ===========================================================================


@mcp.tool()
async def list_connectors() -> str:
    """List all registered connectors, including their fetch parameter schemas."""
    try:
        return _ok(await client.list_connectors())
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def get_connector(connector_id: str) -> str:
    """Get a connector's full schema including FETCH_PARAMS_SCHEMA and REQUIRED_CREDENTIALS."""
    try:
        return _ok(await client.get_connector(connector_id))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def save_flow_graph(
    tenant_id: str,
    job_id: str,
    flow_id: str,
    nodes_json: str,
    edges_json: str,
) -> str:
    """Save a complete flow graph (nodes + edges).

    Args:
        tenant_id: Tenant UUID
        job_id: Job definition UUID
        flow_id: Flow UUID
        nodes_json: JSON array of node objects
        edges_json: JSON array of edge objects
    """
    try:
        nodes = json.loads(nodes_json)
        edges = json.loads(edges_json)
    except json.JSONDecodeError as exc:
        return f"Error: invalid JSON — {exc}"
    try:
        return _ok(await client.save_flow_graph(tenant_id, job_id, flow_id, {"nodes": nodes, "edges": edges}))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def preview_transform(
    tenant_id: str,
    job_id: str,
    flow_id: str,
    node_id: str,
    input_records_json: str,
) -> str:
    """Preview the output of a transform node against sample input records.

    Args:
        tenant_id: Tenant UUID
        job_id: Job definition UUID
        flow_id: Flow UUID
        node_id: Transform node UUID
        input_records_json: JSON array of sample input records
    """
    try:
        records = json.loads(input_records_json)
    except json.JSONDecodeError as exc:
        return f"Error: invalid JSON — {exc}"
    try:
        return _ok(await client.preview_transform(tenant_id, job_id, flow_id, node_id, {"records": records}))
    except RuntimeError as exc:
        return _err(exc)


@mcp.tool()
async def list_destination_schemas() -> str:
    """List all destination endpoint schemas (payload shapes for destination connectors)."""
    try:
        return _ok(await client.list_destination_schemas())
    except RuntimeError as exc:
        return _err(exc)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
