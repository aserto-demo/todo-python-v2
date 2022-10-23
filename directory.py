import os

from typing import Any, Dict, Optional, Tuple

import grpc

from google.protobuf.json_format import MessageToDict

from aserto.directory.common.v2 import ObjectIdentifier, RelationIdentifier, RelationTypeIdentifier
from aserto.directory.reader.v2 import GetObjectRequest, GetObjectResponse, GetRelationsRequest, ReaderStub

DEFAULT_DIRECTORY_ADDRESS = "directory.prod.aserto.com:8443"


address = os.getenv("ASERTO_DIRECTORY_GRPC_ADDRESS", DEFAULT_DIRECTORY_ADDRESS)
cert = os.getenv("ASERTO_DIRECTORY_CERT_PATH")
api_key = os.getenv("ASERTO_DIRECTORY_API_KEY")
tenant_id = os.getenv("ASERTO_TENANT_ID")


def user_from_identity(sub) -> Dict[str, Any]:
    with grpc.secure_channel(target=address, credentials=_channel_credentials()) as channel:
        reader = ReaderStub(channel)

        identityResp = _get_object(reader, ObjectIdentifier(key=sub, type="identity"))

        relationResp = reader.GetRelations(
            GetRelationsRequest(
                param=RelationIdentifier(
                    subject=ObjectIdentifier(type="user"),
                    relation=RelationTypeIdentifier(name="identifier", object_type="identity"),
                    object=ObjectIdentifier(id=identityResp.result.id),
                ),
            ),
            metadata=_metadata(api_key, tenant_id)
        )

        userResp = _get_object(reader, ObjectIdentifier(id=relationResp.results[0].subject.id))
        props = MessageToDict(userResp.result.properties)

        return dict(
            id=userResp.result.id,
            name=userResp.result.display_name,
            **props
        )

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

def _get_object(reader: ReaderStub, identifier: ObjectIdentifier) -> GetObjectResponse:
    return reader.GetObject(
        GetObjectRequest(param=identifier), metadata=_metadata(api_key, tenant_id)
    )
