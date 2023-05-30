"""This script creates a class able to get secret value from gcp

    First: You should have configured your environment (gcloud) and have permissions to access the secret
    Second: Have values for
        - project id or project name
        - secret id or secret name
        - version (optional)
"""
import json
import logging

from google.cloud.secretmanager import SecretManagerServiceClient


class SecretManager:
    """Secret manager class for aws and gcp"""
    URI_FORMAT = "projects/{project_id}/secrets/{secret_id}/versions/{version}"

    @classmethod
    def get(cls,
            project_id: str = "",
            secret_id: str = "",
            version: str = "latest"):
        """get a secret value from gcp"""
        client = SecretManagerServiceClient()
        name = cls.URI_FORMAT.format(project_id=project_id,
                                     secret_id=secret_id,
                                     version=version)
        try:
            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            secret_value = json.loads(payload)
        except Exception as error:
            comments = [
                "can't get/parse secret value for:",
                f"\tproject_id = '{project_id}'",
                f"\tsecret_id  = '{secret_id}'",
                f"\tversion    = '{version}'",
            ]
            logging.error("\n".join(comments))
            raise error

        return secret_value
