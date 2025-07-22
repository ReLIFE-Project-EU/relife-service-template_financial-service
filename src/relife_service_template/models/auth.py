from fastapi import HTTPException, status
from gotrue.types import UserResponse
from pydantic import BaseModel

from relife_service_template.config.settings import get_settings


class KeycloakRole(BaseModel):
    """Representation of a Keycloak role with its attributes.

    This model represents role information retrieved from Keycloak's identity provider.
    """

    id: str
    name: str
    description: str | None = None
    composite: bool | None = None
    clientRole: bool | None = None
    containerId: str | None = None


class AuthenticatedUser(BaseModel):
    """Authenticated user model containing both Supabase user data and Keycloak roles.

    This model brings together authentication information from multiple sources
    and provides helper methods for checking permissions.
    """

    token: str  # Authentication token from Supabase/GoTrue
    user: UserResponse  # User information from Supabase's GoTrue auth service
    keycloak_roles: list[KeycloakRole] | None = None  # User roles from Keycloak

    @property
    def has_admin_role(self) -> bool:
        """Check if the user has the admin role defined in settings."""

        if not self.keycloak_roles:
            return False

        settings = get_settings()

        return any(
            role.name == settings.admin_role_name for role in self.keycloak_roles
        )

    @property
    def user_id(self) -> str:
        """Get the unique identifier for the user."""

        return self.user.user.id

    @property
    def email(self) -> str | None:
        """Get the user's email address."""

        return self.user.user.email

    @property
    def is_keycloak_provider(self) -> bool:
        """Check whether the user has logged in via the Keycloak social login provider."""

        if not self.user.user.identities:
            return False

        return any(
            identity.provider == "keycloak" for identity in self.user.user.identities
        )

    def raise_if_not_admin(self):
        """Verify the user has admin privileges or raise an exception."""

        if not self.has_admin_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have admin role",
            )
