import httpx

class JuditCliente:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def consult_process(self, cnj: str) -> dict:
        headers = {"d844f22a-00bf-4ff9-a401-dbba96011c24": self.api_key}
        params = {"cnj": cnj}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/https://tracking.production.judit.io"
                headers=headers,
                params=params,
                )

        response.raise_for_status()
        return response.json()