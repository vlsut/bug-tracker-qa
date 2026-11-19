"""Bug list. Placeholder until the bug features are built."""

from flask import Blueprint, redirect, render_template, url_for
from werkzeug.wrappers import Response

bp = Blueprint("bugs", __name__)


@bp.get("/")
def index() -> Response:
    """The bug list is the start page."""
    return redirect(url_for("bugs.list_bugs"))


@bp.get("/bugs")
def list_bugs() -> str:
    """Bug list page."""
    return render_template("bugs.html")
