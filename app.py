from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_aserto import AsertoMiddleware, AuthorizationError, ResourceContext
from flask_cors import CORS

from authn import requires_auth
from db import Store, Todo
from directory import (
    UserNotFoundError,
    delete_todo,
    insert_todo,
    user_from_id,
    user_from_identity,
)
from options import load_options_from_environment

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    headers=("Content-Type", "Authorization"),
    origins=["http://localhost:*", "https://todo.demo.aserto.com"],
)

store = Store()


def owner_id_resource_mapper() -> ResourceContext:
    resource = {}

    if request.view_args and "id" in request.view_args:
        resource["object_id"] = request.view_args["id"]

    return resource


aserto_options = load_options_from_environment()
aserto = AsertoMiddleware(
    resource_context_provider=owner_id_resource_mapper,
    **aserto_options,
)


@app.errorhandler(AuthorizationError)
def authorization_error(e):
    app.logger.info("authorization error: %s", e)
    return "Unauthorized", 403


@app.errorhandler(ConnectionError)
def connection_error(e):
    app.logger.error("connection error: %s", e)
    return "Connection Error", 500


@app.route("/todos", methods=["GET"])
@requires_auth
@aserto.authorize
def get_todos():
    results = store.list()
    return jsonify(results)


@app.route("/todos", methods=["POST"])
@requires_auth
@aserto.check(
    policy_root="rebac",
    object_type="resource-creator",
    object_id="resource-creators",
    relation="member",
).authorize
def post_todo():
    todo = Todo.from_json(request.get_json())
    todo.ID = uuid4().hex
    todo.OwnerID = user_from_identity(g.identity)["id"]
    store.insert(todo)
    insert_todo(todo)

    return jsonify(todo)


@app.route("/todos/<id>", methods=["PUT"])
@requires_auth
@aserto.authorize
def put_todo(id: str):
    todo = Todo.from_json(request.get_json())
    todo.ID = id

    store.update(todo)
    return jsonify(todo)


@app.route("/todos/<id>", methods=["DELETE"])
@requires_auth
@aserto.authorize
def remove_todo(id: str):
    store.delete(id)
    delete_todo(id)
    resp = jsonify(success=True)
    resp.status_code = 200
    return resp


@app.route("/users/<userID>", methods=["GET"])
@requires_auth
@aserto.authorize
def get_user(userID):
    try:
        user = (
            user_from_identity(userID) if userID == g.identity else user_from_id(userID)
        )
        return jsonify(user)
    except UserNotFoundError:
        return "user not found", 401


@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(host="localhost", port=3001, debug=True)
