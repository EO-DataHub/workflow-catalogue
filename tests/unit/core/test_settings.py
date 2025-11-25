from __future__ import annotations

from unittest.mock import patch

from workflow_catalogue.core.settings import current_settings


@patch.dict(
    "os.environ",
    {
        "ENVIRONMENT": "test",
        "EODH__BASE_URL": "https://test.eodatahub.org.uk/",
        "EODH__REALM": "eodh",
        "EODH__USERNAME": "test_username",
        "EODH__PASSWORD": "test_password",
        "EODH__CLIENT_ID": "test_client_id",
        "EODH__WORKSPACE_SERVICES_ENDPOINT_PATH": "/workspace-services/v1",
        "EODH__STAC_API_ENDPOINT_PATH": "/stac/v1",
        "EODH__ADES_ENDPOINT_PATH": "/ades/v1",
        "EODH__TMP_S3_CREDENTIALS_ENDPOINT_PATH": "/s3/credentials/v1",
    },
)
def test_settings() -> None:
    settings = current_settings()
    assert settings is not None
    assert settings.environment == "test"

    assert settings.eodh.base_url == "https://test.eodatahub.org.uk/"
    assert settings.eodh.workspace_services_endpoint_path == "/workspace-services/v1"
    assert settings.eodh.stac_api_endpoint_path == "/stac/v1"
    assert settings.eodh.ades_endpoint_path == "/ades/v1"
    assert settings.eodh.tmp_s3_credentials_endpoint_path == "/s3/credentials/v1"

    assert (
        settings.eodh.workspace_tokens_url
        == "https://test.eodatahub.org.uk/workspace-services/v1/test_username/me/tokens"
    )
    assert (
        settings.eodh.workspace_session_tokens_url
        == "https://test.eodatahub.org.uk/workspace-services/v1/test_username/me/sessions"
    )
    assert settings.eodh.workspace_services_url == "https://test.eodatahub.org.uk/workspace-services/v1"
    assert settings.eodh.stac_url == "https://test.eodatahub.org.uk/stac/v1"
    assert settings.eodh.ades_url == "https://test.eodatahub.org.uk/ades/v1"
    assert settings.eodh.tmp_s3_credentials_url == "https://test.eodatahub.org.uk/s3/credentials/v1"

    assert settings.eodh.realm == "eodh"
    assert settings.eodh.username == "test_username"
    assert settings.eodh.password == "test_password"  # noqa: S105
    assert settings.eodh.client_id == "test_client_id"
    assert (
        settings.eodh.token_url == "https://test.eodatahub.org.uk/keycloak/realms/eodh/protocol/openid-connect/token"  # noqa: S105
    )
    assert settings.eodh.auth_url == "https://test.eodatahub.org.uk/keycloak/realms/eodh/protocol/openid-connect/auth"
    assert (
        settings.eodh.introspect_url
        == "https://test.eodatahub.org.uk/keycloak/realms/eodh/protocol/openid-connect/token/introspect"
    )
    assert settings.eodh.certs_url == "https://test.eodatahub.org.uk/keycloak/realms/eodh/protocol/openid-connect/certs"
    assert settings.eodh.oid_url == "https://test.eodatahub.org.uk/keycloak/realms/eodh/protocol/openid-connect"
