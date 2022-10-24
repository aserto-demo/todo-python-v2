import os
from typing import Awaitable, Callable
from aserto.client import AuthorizerOptions, Identity
from aserto_idp.oidc import AccessTokenError, identity_provider as oidc_idp
from flask import request
from typing_extensions import TypedDict
from dotenv import load_dotenv

load_dotenv()

DEFAULT_AUTHORIZER_URL = "https://authorizer.prod.aserto.com"

__all__ = ["AsertoMiddlewareOptions", "load_options_from_environment"]


class AsertoMiddlewareOptions(TypedDict):
    authorizer_options: AuthorizerOptions
    policy_instance_name: str
    policy_instance_label: str
    policy_path_root: str
    identity_provider: Callable[[], Awaitable[Identity]]


def load_options_from_environment() -> AsertoMiddlewareOptions:
    missing_variables = []


    authorizer_service_url = os.getenv(
        "AUTHORIZER_SERVICE_URL", DEFAULT_AUTHORIZER_URL
    )

    policy_path_root = os.getenv("POLICY_ROOT", "")
    if not policy_path_root:
        missing_variables.append("POLICY_ROOT")

    cert_file_path = os.path.expandvars(os.getenv("AUTHORIZER_CERT_PATH", ""))

    oidc_issuer = os.getenv("OIDC_ISSUER", "")
    if not oidc_issuer:
        missing_variables.append("OIDC_ISSUER")

    oidc_client_id = os.getenv("OIDC_CLIENT_ID", "")
    if not oidc_client_id:
        missing_variables.append("OIDC_CLIENT_ID")

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
        service_type="gRPC",
    )

    idp = oidc_idp(issuer=oidc_issuer, client_id=oidc_client_id)

    async def identity_provider() -> Identity:
        authorization_header = request.headers.get("Authorization")

        if authorization_header is None:
            return Identity(type="NONE")

        try:
            identity = await idp.subject_from_jwt_auth_header(authorization_header)
        except AccessTokenError:
            return Identity(type="NONE")

        return Identity(type="SUBJECT", subject=identity)

    return AsertoMiddlewareOptions(
        authorizer_options=options,
        policy_instance_name=policy_instance_name,
        policy_instance_label=policy_instance_label,
        policy_path_root=policy_path_root,
        identity_provider=identity_provider,
    )
