# Python Todo App with Authorization

This app uses `pipenv`. Follow [these instructions](https://pipenv.pypa.io/en/latest/#install-pipenv-today) to install it.

## Configure

Copy `.env.example` as `.env` and fill in your `ASERTO_TENANT_ID` and `ASERTO_AUTHORIZER_API_KEY` if running against
Aserto's hosted authorizer.

If running against your own authorizer, fill in `ASERTO_AUTHORIZER_SERVICE_URL` and `ASERTO_AUTHORIZER_CERT_PATH`.

## Install Dependencies

```sh
pipenv install
```

## Run

```sh
pipenv run flask run
```
