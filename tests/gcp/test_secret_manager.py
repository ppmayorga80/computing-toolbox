"""Test GCP Secret Manager"""
from unittest.mock import patch

import pytest

from computing_toolbox.gcp.secret_manager import SecretManager


class TestGcpSecretManager:
    """Class for testing gcp secret manager"""

    @patch("computing_toolbox.gcp.secret_manager.SecretManagerServiceClient")
    def test_get(self, mock_sm):
        """test how to get the secret"""
        # 1. define the mock value
        mock_sm.return_value.access_secret_version.return_value.payload.data = b'{"token":"abc123"}'

        # 2. get the secret value
        secret = SecretManager.get("PROJECT-ID", "SECRET-NAME")

        # 3. test if secret is OK
        assert isinstance(secret, dict)
        assert "token" in secret
        assert secret["token"] == "abc123"

    @patch("computing_toolbox.gcp.secret_manager.SecretManagerServiceClient")
    def test_get_with_no_json_secret(self, mock_sm):
        """test for invalid secret: secret must be a json string"""
        # 1. define the mock value as a single string
        mock_sm.return_value.access_secret_version.return_value.payload.data = b'This is not a json string'

        # 2. try to get a secret - but we know this raise an error
        with pytest.raises(Exception):
            _ = SecretManager.get("PROJECT-ID", "SECRET-NAME")
