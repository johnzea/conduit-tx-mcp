"""Async httpx wrapper around the Conduit TX REST API."""

import httpx


class ConduitClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        response = await self._http.request(method, path, **kwargs)
        if response.status_code == 204:
            return {}
        if not response.is_success:
            try:
                body = response.json()
                detail = body.get("message") or body.get("detail") or response.text
            except Exception:
                detail = response.text
            raise RuntimeError(f"HTTP {response.status_code}: {detail}")
        return response.json()

    # ------------------------------------------------------------------
    # Tenants
    # ------------------------------------------------------------------

    async def list_tenants(self) -> dict:
        return await self._request("GET", "/api/v1/tenants/")

    async def get_tenant(self, tenant_id: str) -> dict:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}")

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    async def list_jobs(self, tenant_id: str) -> list:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/jobs")

    async def get_job(self, tenant_id: str, job_id: str) -> dict:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/jobs/{job_id}")

    async def create_job(self, tenant_id: str, payload: dict) -> dict:
        return await self._request("POST", f"/api/v1/tenants/{tenant_id}/jobs", json=payload)

    async def update_job(self, tenant_id: str, job_id: str, payload: dict) -> dict:
        return await self._request("PATCH", f"/api/v1/tenants/{tenant_id}/jobs/{job_id}", json=payload)

    async def trigger_job(self, tenant_id: str, job_id: str) -> dict:
        return await self._request("POST", f"/api/v1/tenants/{tenant_id}/jobs/{job_id}/trigger")

    # ------------------------------------------------------------------
    # Job runs
    # ------------------------------------------------------------------

    async def list_job_runs(self, tenant_id: str, job_id: str, limit: int = 10) -> dict:
        return await self._request(
            "GET",
            f"/api/v1/tenants/{tenant_id}/jobs/{job_id}/runs",
            params={"limit": limit},
        )

    async def get_job_run(self, tenant_id: str, run_id: str) -> dict:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/runs/{run_id}")

    # ------------------------------------------------------------------
    # Flows
    # ------------------------------------------------------------------

    async def list_flows(self, tenant_id: str, job_id: str) -> list:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/jobs/{job_id}/flows")

    async def get_flow(self, tenant_id: str, job_id: str, flow_id: str) -> dict:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/jobs/{job_id}/flows/{flow_id}")

    async def save_flow_graph(self, tenant_id: str, job_id: str, flow_id: str, payload: dict) -> dict:
        return await self._request(
            "PUT",
            f"/api/v1/tenants/{tenant_id}/jobs/{job_id}/flows/{flow_id}/graph",
            json=payload,
        )

    # ------------------------------------------------------------------
    # Flow runs
    # ------------------------------------------------------------------

    async def list_flow_runs(self, tenant_id: str, run_id: str) -> list:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/runs/{run_id}/flow-runs")

    async def get_flow_run(self, tenant_id: str, flow_run_id: str) -> dict:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/flow-runs/{flow_run_id}")

    # ------------------------------------------------------------------
    # Connectors
    # ------------------------------------------------------------------

    async def list_connectors(self) -> dict:
        return await self._request("GET", "/api/v1/connectors/")

    async def get_connector(self, connector_id: str) -> dict:
        return await self._request("GET", f"/api/v1/connectors/{connector_id}")

    # ------------------------------------------------------------------
    # Connector configs
    # ------------------------------------------------------------------

    async def list_connector_configs(self, tenant_id: str) -> list:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/connector-configs")

    # ------------------------------------------------------------------
    # Reference cache
    # ------------------------------------------------------------------

    async def get_ref_cache_status(self, tenant_id: str) -> dict:
        return await self._request("GET", f"/api/v1/tenants/{tenant_id}/reference-cache")

    async def refresh_ref_cache(self, tenant_id: str, data_type: str) -> dict:
        return await self._request(
            "POST",
            f"/api/v1/tenants/{tenant_id}/reference-cache/{data_type}/refresh",
        )

    # ------------------------------------------------------------------
    # Transform preview
    # ------------------------------------------------------------------

    async def preview_transform(
        self, tenant_id: str, job_id: str, flow_id: str, node_id: str, payload: dict
    ) -> dict:
        return await self._request(
            "POST",
            f"/api/v1/tenants/{tenant_id}/jobs/{job_id}/flows/{flow_id}/nodes/{node_id}/transform/preview",
            json=payload,
        )

    # ------------------------------------------------------------------
    # Destination schemas
    # ------------------------------------------------------------------

    async def list_destination_schemas(self) -> list:
        return await self._request("GET", "/api/v1/destination-endpoint-schemas")
