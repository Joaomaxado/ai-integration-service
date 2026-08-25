import httpx
from fastapi import HTTPException

JAVA_BASE_URL = "https://api.pmlex.com.br/"

class JavaBackendClient:
    def __init__(self):
        self.cliente = httpx.AsynClient(base_url=JAVA_BASE_URL,
        timeout=10.0,
        headers={'Content-Type': 'application/json'}
)

    