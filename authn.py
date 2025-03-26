import os

from dataclasses import dataclass
from functools import cache, wraps
from typing import Dict, List, Union
from urllib.parse import urlparse

import requests

from flask import g, request
from jose import jwt


OidcConfig = Dict[str, Union[str, List[str]]]
Key = Dict[str, str]
KeySet = Dict[str, List[Key]]


@dataclass(frozen=True)
class AuthError(Exception):
    description: str
    code: int


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError("Authorization header is expected", 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError("Authorization header must start with Bearer", 401)

    if len(parts) == 1:
        raise AuthError("Token not found", 401)

    if len(parts) > 2:
        raise AuthError("Authorization header must be Bearer token", 401)

    token = parts[1]
    return token


def requires_auth(f):
    """Determines if the Access Token is valid"""
    missing_variables = []
    oidc_issuer = os.getenv("ISSUER", "")
    if not oidc_issuer:
        missing_variables.append("ISSUER")

    oidc_client_id = os.getenv("AUDIENCE", "")
    if not oidc_client_id:
        missing_variables.append("AUDIENCE")

    if missing_variables:
        raise EnvironmentError(
            f"environment variables not set: {', '.join(missing_variables)}"
        )

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        key_id = get_key_id(token)
        discovery_url = os.path.join(oidc_issuer, ".well-known/openid-configuration")
        key = find_signing_key(discovery_url, key_id)

        options = {"verify_at_hash": None}
        claims = jwt.decode(token, key, options=options, audience=oidc_client_id)
        if "azp" in claims and claims["azp"] != oidc_client_id:
            raise AuthError(
                f"'azp' claim '{claims['azp']}' does not match client ID", 401
            )

        if not isinstance(claims["sub"], str):
            raise AuthError(
                f"'sub' claim '{claims['sub']}'is not a valid identity", 401
            )

        g.identity = claims["sub"]
        return f(*args, **kwargs)

    return decorated


def get_key_id(token: str) -> str:
    kid = jwt.get_unverified_header(token).get("kid")
    if not kid:
        raise AuthError("Bearer token does not have 'kid' claim", 401)

    return kid  # type: ignore


@cache
def find_signing_key(discovery_url: str, key_id: str) -> Key:
    """Find and return the signing key for the specified key ID.

    Args:
        key_id: The ID of the key used by the OIDC issuer to sign a JWT being verified.
                Key IDs are extracted from the "kid" JOSE header of a JWT
        (https://datatracker.ietf.org/doc/html/draft-ietf-jose-json-web-signature#section-4.1.4).

    Returns:
        A ``dict``
    """
    for _ in range(2):
        # If we can't find the key ID in the issuer's keyset, clear the cache and try again.
        keyset = download_keyset(discovery_url)
        keys = keyset.get("keys")
        if not keys:
            raise AuthError(f"Keyset missing required field 'keys': {keys}", 401)

        for key in keys:
            if key["kid"] == key_id:
                return key

    raise AuthError(f"RSA public key with ID '{key_id}' was not found.", 401)


def download_keyset(discovery_url: str) -> KeySet:
    """Downloads the OIDC issuer's signing key-set.

    The key-set URL is retrieved from the "jwks_uri" field in the issuer's OIDC configuration
    (https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata).

    Returns:
        A ``dict`` containing the downloaded JOSE key-set.
    """

    cfg = config(discovery_url)
    keyset_url = cfg.get("jwks_uri")
    if not keyset_url:
        raise AuthError("Issuer openid-configuration missing 'jwks_uri'", 401)
    if isinstance(keyset_url, list):
        keyset_url = keyset_url[0]

    return get_json(keyset_url)


def config(discovery_url) -> OidcConfig:
    return get_json(discovery_url)


def issuer_url(issuer: str) -> str:
    url = urlparse(issuer)
    if not url.scheme:
        # issuer is not a full URL
        return f"https://{issuer}"

    if url.scheme != "https":
        raise ValueError("OIDC issuer MUST use the 'https' scheme.")

    return issuer


def get_json(url: str) -> dict:
    return requests.get(url, timeout=10).json()
