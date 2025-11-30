from flask import render_template, request, redirect, url_for
from requests import RequestException
from werkzeug.exceptions import BadRequestKeyError

from app.config import STATUS_SUCCESS, STATUS_ERROR, Config
from app.services import create_purchase, fetch_catalog


def render_index(error=None, success=None, catalog=None):
    """Centralized way to render the index page."""
    if catalog is None:
        try:
            catalog = fetch_catalog()
        except RequestException:
            return render_template(
                "index.html",
                products=[],
                supermarkets=[],
                users=[],
                error=error or "Failed to load data",
            )

    context = {
        "products": catalog.get("products", []),
        "supermarkets": catalog.get("supermarkets", []),
        "users": catalog.get("users", []),
    }
    if success:
        context["success"] = success
    if error:
        context["error"] = error

    return render_template("index.html", **context)


def register_routes(app):
    @app.route("/", methods=["GET"])
    def index():
        status = request.args.get("status")  # "success" or "error" or None
        error_msg = None
        success_msg = None

        if status == STATUS_SUCCESS:
            success_msg = Config.MESSAGES[STATUS_SUCCESS]
        elif status == STATUS_ERROR:
            error_msg = Config.MESSAGES[STATUS_ERROR]

        return render_index(error=error_msg, success=success_msg)



    @app.route("/make_purchase", methods=["POST"])
    def make_purchase():
        try:
            is_new_user = request.form["is_new_user"] == '1'
            supermarket_id = request.form["supermarket_id"]
            user_id = request.form["user_id"]
            item_list = list(request.form["item_list"])
            total_amount = float(request.form["total_amount"])
            create_purchase(is_new_user, user_id, supermarket_id, item_list, total_amount)
            status_key = STATUS_SUCCESS
        except (ValueError, TypeError, BadRequestKeyError):
            status_key = STATUS_ERROR
        except RequestException:
            status_key = STATUS_ERROR
        return redirect(url_for("index", status=status_key))
