from functools import cache
import os
from typing import Any, Dict

from aserto.client.directory.v3 import Directory, NotFoundError, Object
from google.protobuf.json_format import MessageToDict

DEFAULT_DIRECTORY_ADDRESS = "directory.prod.aserto.com:8443"


@cache
def ds() -> Directory:
    address = os.getenv("ASERTO_DIRECTORY_SERVICE_URL", DEFAULT_DIRECTORY_ADDRESS)
    cert = os.path.expandvars(os.getenv("ASERTO_DIRECTORY_GRPC_CERT_PATH", ""))
    api_key = os.getenv("ASERTO_DIRECTORY_API_KEY", "")
    tenant_id = os.getenv("ASERTO_TENANT_ID", "")

    return Directory(
        api_key=api_key, tenant_id=tenant_id, address=address, ca_cert_path=cert
    )


class UserNotFoundError(Exception):
    pass


def user_from_identity(sub) -> Dict[str, Any]:
    try:
        relationResp = ds().get_relation(
            object_type="identity",
            object_id=sub,
            subject_type="user",
            relation="identifier",
        )

        user = ds().get_object(
            object_type=relationResp.subject_type,
            object_id=relationResp.subject_id,
        )
        return _get_object_dict(user)
    except NotFoundError:
        raise UserNotFoundError


def user_from_id(id) -> Dict[str, Any]:
    user = ds().get_object(object_type="user", object_id=id)
    return _get_object_dict(user)


def _get_object_dict(object: Object) -> Dict[str, Any]:
    props = MessageToDict(object.properties)
    return dict(key=object.id, name=object.display_name, **props)
