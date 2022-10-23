from flask import Flask, g, jsonify, request
from flask_cors import CORS

from .directory import user_from_identity
from .db import list_todos, insert_todo, update_todo, delete_todo
from flask_aserto import AsertoMiddleware, AuthorizationError
from .aserto_options import load_aserto_options_from_environment

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CORS(app, headers=["Content-Type", "Authorization"])

aserto_options = load_aserto_options_from_environment()
aserto = AsertoMiddleware(**aserto_options)


@app.errorhandler(AuthorizationError)
def authorization_error(e):
    app.logger.info("authorization error: %s", e)
    return "Unauthorized", 403

@app.errorhandler(ConnectionError)
def connection_error(e):
    app.logger.error("connection error: %s", e)
    return "Connection Error", 500


@app.route("/todos", methods=["GET"])
@aserto.authorize
def get_todos():
    results = list_todos()
    return jsonify(results)


@app.route("/todo", methods=["POST"])
@aserto.authorize
def post_todo():
    todo = request.get_json()
    insert_todo(todo)
    return jsonify(todo)


@app.route("/todo/<ownerID>", methods=["PUT"])
@aserto.authorize
def put_todo(ownerID):
    todo = request.get_json()
    update_todo(todo)
    return jsonify(todo)


@app.route("/todo/<ownerID>", methods=["DELETE"])
@aserto.authorize
def remove_todo(ownerID):
    todo = request.get_json()
    delete_todo(todo)
    resp = jsonify(success=True)
    resp.status_code = 200
    return resp


@app.route("/user/<userID>", methods=["GET"])
@aserto.authorize
def get_user(userID):
    user= user_from_identity(userID)
    app.logger.warning("user: %s", user)
    return jsonify(user)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(host="localhost", port=3001, debug=True)
