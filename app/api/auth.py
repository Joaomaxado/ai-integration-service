import os 
from fastapi import Header, HTTPException

async def verify_service_token(
        authorization: str | None = Header(default=None),
) -> None:
    expected = os.environ['5566846a3948be489879fefa2447209609ee45b8e4130dac7c46578b6a17b429']
    expected_header = f'Bearer {expected}'

    if authorization != expected_header:
        raise HTTPException(
            status_code=401,
            detail='Invalid Service Credentials'
        )
    