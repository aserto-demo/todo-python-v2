import os

from functools import cache
from typing import Any, Dict

from aserto.client.directory.v3 import (
    Directory,
    NotFoundError,
    InvalidArgumentError,
    Object,
)
from google.protobuf.json_format import MessageToDict

from db import Todo

DEFAULT_DIRECTORY_ADDRESS = "directory.prod.aserto.com:8443"


@cache
def ds() -> Directory:
    address = os.getenv("ASERTO_DIRECTORY_SERVICE_URL", DEFAULT_DIRECTORY_ADDRESS)
    cert = os.path.expandvars(
        os.getenv(
            "ASERTO_DIRECTORY_GRPC_CA_CERT_PATH",
            os.getenv("ASERTO_GRPC_CA_CERT_PATH", ""),
        )
    )
    api_key = os.getenv("ASERTO_DIRECTORY_API_KEY", "")
    tenant_id = os.getenv("ASERTO_TENANT_ID", "")

    return Directory(
        api_key=api_key, tenant_id=tenant_id, address=address, ca_cert_path=cert
    )


class UserNotFoundError(Exception):
    pass


@cache
def is_legacy() -> bool:
    try:
        ds().get_relation(
            object_type="identity",
            object_id="todoDemoIdentity",
            subject_type="user",
            subject_id="todoDemoUser",
            relation="identifier",
        )
        return True
    except InvalidArgumentError:
        return False
    except NotFoundError:
        return True


def try_resolve_identity_legacy(sub) -> Any:
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
        return user
    except NotFoundError as err:
        raise UserNotFoundError from err


def try_resolve_identity(sub) -> Any:
    try:
        relationResp = ds().get_relation(
            object_type="user",
            subject_type="identity",
            subject_id=sub,
            relation="identifier",
        )

        user = ds().get_object(
            object_type=relationResp.object_type,
            object_id=relationResp.object_id,
        )
        return user
    except NotFoundError as err:
        raise UserNotFoundError from err


def user_from_identity(sub) -> Dict[str, Any]:
    try:
        user = (
            try_resolve_identity_legacy(sub)
            if is_legacy()
            else try_resolve_identity(sub)
        )
        return _get_object_dict(user)
    except NotFoundError as err:
        raise UserNotFoundError from err


def insert_todo(todo: Todo):
    ds().set_object(
        object_type="resource",
        object_id=todo.ID,
        display_name=todo.Title,
        properties={},
    )

    ds().set_relation(
        subject_id=todo.OwnerID,
        subject_type="user",
        object_id=todo.ID,
        object_type="resource",
        relation="owner",
    )


def delete_todo(todoId: str):
    ds().delete_object(object_type="resource", object_id=todoId, with_relations=True)


def user_from_id(id) -> Dict[str, Any]:
    user = ds().get_object(object_type="user", object_id=id)
    return _get_object_dict(user)


def _get_object_dict(object: Object) -> Dict[str, Any]:
    props = MessageToDict(object.properties)
    return {"id": object.id, "name": object.display_name, **props}
