"""Login, logout and access control (R1–R6, R8)."""

from flask import (
    Blueprint,
    Flask,
    current_app,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.wrappers import Response

from app import sessions, users
from app.db import get_db

SESSION_COOKIE = "bt_session"
LOGIN_ERROR = "Invalid username or password"
# R5: everything else requires a session. "static" serves CSS for the login page.
PUBLIC_ENDPOINTS = {"auth.login", "health", "static"}

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login() -> str | Response | tuple[str, int]:
    """Show the login form and handle a login attempt."""
    if request.method == "GET":
        return render_template("login.html")

    # Taken as sent: no trimming, the username comparison is exact (R1).
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    field_errors = {}
    if not username.strip():
        field_errors["username"] = "Username is required"
    if not password.strip():
        field_errors["password"] = "Password is required"
    if field_errors:  # R4.2
        return render_template("login.html", username=username, field_errors=field_errors), 400

    user = users.authenticate(get_db(), username, password)
    if user is None:  # R3: one message for unknown user and wrong password
        return render_template("login.html", username=username, error=LOGIN_ERROR), 401

    token = sessions.create(get_db(), user["id"])
    response = redirect(url_for("bugs.list_bugs"))  # R2: always /bugs
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="Lax")
    return response


@bp.post("/logout")
def logout() -> Response:
    """End the session on the server and go to the login page (R6)."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sessions.delete(get_db(), token)
    response = redirect(url_for("auth.login"))
    response.delete_cookie(SESSION_COOKIE)
    return response


def load_user() -> Response | None:
    """Attach the session's user to the request; send anonymous users to /login (R5)."""
    g.user = None
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        g.user = sessions.resolve(get_db(), token, current_app.config["SESSION_IDLE_TIMEOUT"])
    # Unknown URLs have no endpoint and are protected too.
    if g.user is None and request.endpoint not in PUBLIC_ENDPOINTS:
        return redirect(url_for("auth.login"))
    return None


def no_store_for_users(response: Response) -> Response:
    """Keep authenticated pages out of the browser cache: Back after logout shows nothing (R6.2)."""
    if g.get("user") is not None:
        response.headers["Cache-Control"] = "no-store"
    return response


def init_app(app: Flask) -> None:
    """Register the blueprint and the access-control hooks."""
    app.register_blueprint(bp)
    app.before_request(load_user)
    app.after_request(no_store_for_users)
