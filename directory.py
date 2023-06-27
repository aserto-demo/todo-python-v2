import os
from functools import cache
from typing import Any, Dict

from aserto.client.directory import Directory, Object
from google.protobuf.json_format import MessageToDict

DEFAULT_DIRECTORY_ADDRESS = "directory.prod.aserto.com:8443"


@cache
def ds() -> Directory:
    address = os.getenv("ASERTO_DIRECTORY_SERVICE_URL", DEFAULT_DIRECTORY_ADDRESS)
    cert = os.path.expandvars(os.getenv("DIRECTORY_GRPC_CERT_PATH", ""))
    api_key = os.getenv("ASERTO_DIRECTORY_API_KEY")
    tenant_id = os.getenv("ASERTO_TENANT_ID")

    return Directory.connect(
        api_key=api_key, tenant_id=tenant_id, address=address, ca_cert=cert
    )


def user_from_identity(sub) -> Dict[str, Any]:
    relationResp = ds().get_relation(
        subject_type="user",
        object_key=sub,
        object_type="identity",
        relation_type="identifier",
    )["relation"]

    user = ds().get_object(
        key=relationResp.subject.key,
        type=relationResp.subject.type,
    )

    return _get_object_dict(user)


def user_from_key(key) -> Dict[str, Any]:
    user = ds().get_object(key=key, type="user")
    return _get_object_dict(user)


def _get_object_dict(object: Object) -> Dict[str, Any]:
    props = MessageToDict(object.properties)
    return dict(key=object.key, name=object.display_name, **props)
