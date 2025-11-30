"""Shared frontend assets (templates + static) for iCash services."""
from flask import Blueprint

frontend_bp = Blueprint(
    "icash_common",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/common-static",
)


def register_frontend(app):
    """Register the shared frontend blueprint on a Flask app."""
    app.register_blueprint(frontend_bp)


__all__ = ["frontend_bp", "register_frontend"]
