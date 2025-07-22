import logging
from typing import List

import httpx
from fastapi import HTTPException, status

from relife_service_template.models.auth import KeycloakRole

_logger = logging.getLogger("uvicorn")


async def get_keycloak_token(
    keycloak_url: str, client_id: str, client_secret: str
) -> str:
    """Obtain an admin access token from Keycloak using client credentials flow.
    Raises HTTPException if token request fails."""

    token_url = f"{keycloak_url}/protocol/openid-connect/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

        return response.json()["access_token"]


async def get_keycloak_user_roles(
    keycloak_url: str, admin_token: str, user_id: str
) -> List[KeycloakRole]:
    """Fetch a user's realm roles from Keycloak's admin API.
    Requires an admin token with appropriate permissions."""

    role_mapper_base_url = keycloak_url.replace("/realms", "/admin/realms").rstrip("/")
    role_mapper_url = f"{role_mapper_base_url}/users/{user_id}/role-mappings/realm"

    async with httpx.AsyncClient() as client:
        _logger.debug("Requesting roles for user %s from %s", user_id, role_mapper_url)

        response = await client.get(
            role_mapper_url, headers={"Authorization": f"Bearer {admin_token}"}
        )

        response.raise_for_status()
        return [KeycloakRole(**role) for role in response.json()]
