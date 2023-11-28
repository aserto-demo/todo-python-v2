import os
from typing import TypedDict

from dotenv import load_dotenv
from flask import g, request
from flask_aserto import AuthorizerOptions, Identity, IdentityMapper, IdentityType
import jwt

load_dotenv()

DEFAULT_AUTHORIZER_URL = "authorizer.prod.aserto.com:8443"

__all__ = ["AsertoMiddlewareOptions", "load_options_from_environment"]


class AccessTokenError(Exception):
    pass


class AsertoMiddlewareOptions(TypedDict):
    authorizer_options: AuthorizerOptions
    policy_instance_name: str
    policy_instance_label: str
    policy_path_root: str
    identity_provider: IdentityMapper


def load_options_from_environment() -> AsertoMiddlewareOptions:
    missing_variables = []

    authorizer_service_url = os.getenv(
        "ASERTO_AUTHORIZER_SERVICE_URL", DEFAULT_AUTHORIZER_URL
    )

    policy_path_root = os.getenv("ASERTO_POLICY_ROOT", "")
    if not policy_path_root:
        missing_variables.append("ASERTO_POLICY_ROOT")

    cert_file_path = (
        os.path.expandvars(os.getenv("ASERTO_AUTHORIZER_CERT_PATH", "")) or None
    )

    oidc_issuer = os.getenv("ISSUER", "")
    if not oidc_issuer:
        missing_variables.append("ISSUER")

    oidc_client_id = os.getenv("AUDIENCE", "")
    if not oidc_client_id:
        missing_variables.append("AUDIENCE")

    tenant_id = os.getenv("ASERTO_TENANT_ID", None)
    authorizer_api_key = os.getenv("ASERTO_AUTHORIZER_API_KEY", "")
    policy_instance_name = os.getenv("ASERTO_POLICY_INSTANCE_NAME", "")
    policy_instance_label = os.getenv("ASERTO_POLICY_INSTANCE_LABEL", "")

    if missing_variables:
        raise EnvironmentError(
            f"environment variables not set: {', '.join(missing_variables)}",
        )

    options = AuthorizerOptions(
        url=authorizer_service_url,
        tenant_id=tenant_id,
        api_key=authorizer_api_key,
        cert_file_path=cert_file_path,
    )

    def identity_provider() -> Identity:
        authorization_header = request.headers.get("Authorization")

        if authorization_header is None:
            return Identity(IdentityType.IDENTITY_TYPE_NONE)

        try:
            parts = authorization_header.split()
            if not parts:
                raise AccessTokenError("Authorization header missing")
            elif parts[0].lower() != "bearer":
                raise AccessTokenError("Authorization header must start with 'Bearer'")
            elif len(parts) == 1:
                raise AccessTokenError("Bearer token not found")
            elif len(parts) > 2:
                raise AccessTokenError(
                    "Authorization header must be a valid Bearer token"
                )

            decoded = jwt.decode(
                parts[1], algorithms=["RS256"], options={"verify_signature": False}
            )
            identity = decoded["sub"]
        except AccessTokenError:
            return Identity(IdentityType.IDENTITY_TYPE_NONE)

        g.identity = identity
        return Identity(type=IdentityType.IDENTITY_TYPE_SUB, value=identity)

    return AsertoMiddlewareOptions(
        authorizer_options=options,
        policy_instance_name=policy_instance_name,
        policy_instance_label=policy_instance_label,
        policy_path_root=policy_path_root,
        identity_provider=identity_provider,
    )
