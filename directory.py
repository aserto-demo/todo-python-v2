import os
from operator import itemgetter
import requests
import json

authorization_service_url = os.getenv("ASERTO_AUTHORIZER_SERVICE_URL")
api_key = os.getenv("ASERTO_AUTHORIZER_API_KEY")
tenant_id = os.getenv("ASERTO_TENANT_ID")


def resolve_identity(sub):
    response = requests.post(
        authorization_service_url + "/api/v1/dir/identities",
        headers={
            "Authorization": "basic " + api_key,
            "aserto-tenant-id": tenant_id,
            "Content-Type": "application/json",
        },
        data=json.dumps({"identity": sub}),
    )

    json_response = response.json()
    return itemgetter("id")(json_response)


def resolve_user(user_id):
    response = requests.get(
        authorization_service_url
        + "/api/v1/dir/users/"
        + user_id
        + "?fields.mask=id,display_name,picture,email",
        headers={
            "Authorization": "basic " + api_key,
            "aserto-tenant-id": tenant_id,
            "Content-Type": "application/json",
        },
    )

    json_response = response.json()
    return itemgetter("result")(json_response)

