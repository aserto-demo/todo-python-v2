import os
from typing import TypedDict

from dotenv import load_dotenv
from flask import g
from flask_aserto import AuthorizerOptions, Identity, IdentityMapper, IdentityType

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
    authorizer_service_url = os.getenv(
        "ASERTO_AUTHORIZER_SERVICE_URL", DEFAULT_AUTHORIZER_URL
    )

    policy_path_root = os.getenv("ASERTO_POLICY_ROOT", "")
    if not policy_path_root:
        raise EnvironmentError(
            "environment variable not set: ASERTO_POLICY_ROOT",
        )

    cert_file_path = (
        os.path.expandvars(
            os.getenv(
                "ASERTO_AUTHORIZER_GRPC_CA_CERT_PATH",
                os.getenv("ASERTO_GRPC_CA_CERT_PATH", ""),
            )
        )
        or None
    )

    tenant_id = os.getenv("ASERTO_TENANT_ID", None)
    authorizer_api_key = os.getenv("ASERTO_AUTHORIZER_API_KEY", "")
    policy_instance_name = os.getenv("ASERTO_POLICY_INSTANCE_NAME", "")
    policy_instance_label = os.getenv("ASERTO_POLICY_INSTANCE_LABEL", "")

    options = AuthorizerOptions(
        url=authorizer_service_url,
        tenant_id=tenant_id,
        api_key=authorizer_api_key,
        cert_file_path=cert_file_path,
    )

    return AsertoMiddlewareOptions(
        authorizer_options=options,
        policy_instance_name=policy_instance_name,
        policy_instance_label=policy_instance_label,
        policy_path_root=policy_path_root,
        identity_provider=identity_provider,
    )


def identity_provider() -> Identity:
    identity = g.identity

    if identity is None:
        return Identity(IdentityType.IDENTITY_TYPE_NONE)

    return Identity(type=IdentityType.IDENTITY_TYPE_SUB, value=identity)
