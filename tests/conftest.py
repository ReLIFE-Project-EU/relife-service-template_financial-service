import os
from unittest.mock import Mock

import pytest

# Set test environment variables to avoid validation errors
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test_key_123")
os.environ.setdefault("KEYCLOAK_CLIENT_ID", "test_client")
os.environ.setdefault("KEYCLOAK_CLIENT_SECRET", "test_secret")


@pytest.fixture
def mock_settings():
    """Create a mock settings object."""

    mock = Mock()
    mock.bucket_name = "test-bucket"
    mock.admin_role_name = "admin"
    mock.supabase_url = "https://test.supabase.co"
    mock.supabase_key = "test_key"
    mock.keycloak_client_id = "test_client"
    mock.keycloak_client_secret = "test_secret"
    return mock
