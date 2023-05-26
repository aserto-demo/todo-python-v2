import os

from typing import Any, Dict, Optional, Tuple

import grpc

from google.protobuf.json_format import MessageToDict

from aserto.directory.common.v2 import ObjectIdentifier, RelationIdentifier, RelationTypeIdentifier
from aserto.directory.reader.v2 import GetObjectRequest, GetObjectResponse, GetRelationRequest, ReaderStub

DEFAULT_DIRECTORY_ADDRESS = "directory.prod.aserto.com:8443"


address = os.getenv("ASERTO_DIRECTORY_SERVICE_URL", DEFAULT_DIRECTORY_ADDRESS)
cert = os.path.expandvars(os.getenv("DIRECTORY_GRPC_CERT_PATH", ""))
api_key = os.getenv("ASERTO_DIRECTORY_API_KEY")
tenant_id = os.getenv("ASERTO_TENANT_ID")


def user_from_identity(sub) -> Dict[str, Any]:
    with grpc.secure_channel(target=address, credentials=_channel_credentials()) as channel:
        reader = ReaderStub(channel)

        relationResp = reader.GetRelation(
            GetRelationRequest(
                param=RelationIdentifier(
                    subject=ObjectIdentifier(type="user"),
                    relation=RelationTypeIdentifier(name="identifier", object_type="identity"),
                    object=ObjectIdentifier(type="identity", key=sub),
                ),
            ),
            metadata=_metadata(api_key, tenant_id)
        )

        return _get_object(reader, relationResp.results[0].subject)

def user_from_key(key) -> Dict[str, Any]:
    with grpc.secure_channel(target=address, credentials=_channel_credentials()) as channel:
        reader = ReaderStub(channel)

        return _get_object(reader, ObjectIdentifier(type="user", key=key))

def _channel_credentials() -> grpc.ChannelCredentials:
    if cert:
        with open(cert, "rb") as f:
            return grpc.ssl_channel_credentials(f.read())
    else:
        return grpc.ssl_channel_credentials()



def _metadata(api_key: Optional[str], tenant_id: Optional[str]) -> Tuple:
    md = ()
    if api_key:
        md += (("authorization", f"basic {api_key}"),)
    if tenant_id:
        md += (("aserto-tenant-id", tenant_id),)

    return md

def _get_object(reader: ReaderStub, identifier: ObjectIdentifier) -> Dict[str, Any]:
    userResp = reader.GetObject(
        GetObjectRequest(param=identifier), metadata=_metadata(api_key, tenant_id)
    )

    print("userResp: ", userResp)

    props = MessageToDict(userResp.result.properties)

    return dict(
        key=userResp.result.key,
        name=userResp.result.display_name,
        **props
    )
