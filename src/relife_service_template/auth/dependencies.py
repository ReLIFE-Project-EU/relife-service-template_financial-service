from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AsyncClient, create_async_client
from supabase.client import ClientOptions

from relife_service_template.auth.keycloak import (
    get_keycloak_token,
    get_keycloak_user_roles,
)
from relife_service_template.config.settings import SettingsDep
from relife_service_template.models.auth import AuthenticatedUser

security = HTTPBearer()


async def get_service_client(settings: SettingsDep) -> AsyncClient:
    """Create a Supabase client with service role (admin) privileges.
    This client bypasses Row Level Security and has full database access.
    Should only be used for admin/service operations."""

    client = await create_async_client(
        settings.supabase_url,
        settings.supabase_key,
        options=ClientOptions(),
    )

    return client


async def _get_authenticated_user(
    settings: SettingsDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    fetch_roles: bool = False,
) -> AuthenticatedUser:
    """Authenticates user and optionally fetches their Keycloak roles."""

    try:
        token = credentials.credentials
        client = await get_service_client(settings)
        user = await client.auth.get_user(token)
        result = AuthenticatedUser(token=token, user=user)

        if not fetch_roles:
            return result

        user_metadata = user.user.user_metadata
        keycloak_user_id = user_metadata["provider_id"]
        keycloak_url = user_metadata["iss"]

        realm_client_token = await get_keycloak_token(
            keycloak_url,
            settings.keycloak_client_id,
            settings.keycloak_client_secret,
        )

        roles = await get_keycloak_user_roles(
            keycloak_url, realm_client_token, keycloak_user_id
        )

        result.keycloak_roles = roles

        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def get_authenticated_user_without_roles(
    settings: SettingsDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """Authenticates user without fetching Keycloak roles."""

    return await _get_authenticated_user(
        settings=settings, credentials=credentials, fetch_roles=False
    )


async def get_authenticated_user_with_roles(
    settings: SettingsDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """Authenticates user and fetches their Keycloak roles."""

    return await _get_authenticated_user(
        settings=settings, credentials=credentials, fetch_roles=True
    )


AuthenticatedUserDep = Annotated[
    AuthenticatedUser, Depends(get_authenticated_user_without_roles)
]
"""Dependency that provides an authenticated user without Keycloak roles.
Use this dependency when basic user authentication is needed but role information is not required.
"""

AuthenticatedUserWithRolesDep = Annotated[
    AuthenticatedUser, Depends(get_authenticated_user_with_roles)
]
"""Dependency that provides an authenticated user with their Keycloak roles.
Use this dependency when both user authentication and role-based access control are needed.
"""


async def get_user_client(
    current_user: AuthenticatedUserDep, settings: SettingsDep
) -> AsyncClient:
    """Create a Supabase client with user context.
    This client respects Row Level Security policies based on the user's token."""

    client = await create_async_client(
        settings.supabase_url,
        settings.supabase_key,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {current_user.token}"}
        ),
    )

    return client


ServiceClientDep = Annotated[AsyncClient, Depends(get_service_client)]
"""Dependency that provides a Supabase client with service role (admin) privileges.
Use this dependency for operations that require bypassing Row Level Security and need full database access.
It should only be used for admin or service-level operations.
Note: This dependency does not authenticate the remote user; it only provides a client with admin privileges.
To authenticate the remote user, use this dependency together with `AuthenticatedUserWithRolesDep`."""

UserClientDep = Annotated[AsyncClient, Depends(get_user_client)]
"""Dependency that provides a Supabase client with user context.
Use this dependency when operations must respect Row Level Security policies based on the authenticated user's token.
This dependency authenticates the remote user against the Supabase service. If no error is raised, the user is considered authenticated."""
