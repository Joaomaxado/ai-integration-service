import httpx
import requests
import os
import time

api_key = os.getenv('d844f22a-00bf-4ff9-a401-dbba96011c24')
base_url = os.getenv('https://tracking.production.judit.io')

headers = {
    'api_key' : api_key,
   'Content-Type' : 'application/json'
}

class JuditRequest:
    payload = {
        'search': {
            'search_type':'lawsuit_cnj',
            'search_key': '9999999-99.9999.9.99.9999',
        }
    }

    responde = requests.post(f'{base_url}/requests',
                             json=payload,
                             headers=headers)
    request_data = responde.json()
    request_id = request_data['request_id']

class JuditCliente:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def consult_process(self, cnj: str) -> dict:
        headers = {"api_key": self.api_key}
        params = {"cnj": cnj}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/https://tracking.production.judit.io"
                headers=headers,
                params=params,
                )

        response.raise_for_status()
        return response.json()