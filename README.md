# Python Todo App with Authorization

This app uses `pipenv`. Follow [these instructions](https://pipenv.pypa.io/en/latest/#install-pipenv-today) to install it.

## Configure

### ENV
```
JWKS_URI=https://citadel.authzen-interop.net/dex/keys
ISSUER=https://citadel.authzen-interop.net/dex
AUDIENCE=citadel-app

ASERTO_POLICY_ROOT="todoApp"

# Topaz
#
# This configuration targets a Topaz instance running locally.
# To target an Aserto hosted authorizer, comment out the lines below and uncomment the section
# at the bottom of this file.
ASERTO_AUTHORIZER_SERVICE_URL=localhost:8282
ASERTO_DIRECTORY_SERVICE_URL=localhost:9292
ASERTO_GRPC_CA_CERT_PATH=$HOME/.config/topaz/certs/grpc-ca.crt

# Aserto hosted authorizer
#
# To run the server using an Aserto hosted authorizer, the following variables are required:
# ASERTO_AUTHORIZER_SERVICE_URL=https://authorizer.prod.aserto.com
# ASERTO_DIRECTORY_SERVICE_URL=directory.prod.aserto.com:8443
# ASERTO_TENANT_ID={Your Aserto Tenant ID UUID}
# ASERTO_AUTHORIZER_API_KEY={Your Authorizer API Key}
# ASERTO_DIRECTORY_API_KEY={Your Directory (read-only) API Key}
# ASERTO_POLICY_INSTANCE_NAME=todo
# ASERTO_POLICY_INSTANCE_LABEL=todo
```

## Install Dependencies

```sh
pipenv install
```

## Run

```sh
pipenv run flask run
```
