import logging
from datetime import datetime

from flask import render_template
from requests import RequestException

from app.config import Config
from app.services import fetch_analytics

log = logging.getLogger(__name__)

def register_routes(app):
    @app.route("/", methods=["GET"])
    def dashboard():
        analytics = {}
        error = None

        try:
            analytics = fetch_analytics(min_purchases=Config.MIN_PURCHASES)
        except RequestException as exc:
            log.exception("Analytics fetch failed: %s", exc)
            error = "Failed to load analytics"

        generated_at_str = analytics.get("generated_at")

        generated_at = (
            datetime.fromisoformat(generated_at_str)
            if generated_at_str is not None
            else None
        )

        return render_template(
            "dashboard.html",
            generated_at=generated_at,
            analytics=analytics,
            error=error,
            min_purchases=Config.MIN_PURCHASES,
        )
