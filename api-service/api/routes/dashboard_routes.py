from datetime import datetime, timezone
import logging

from flask import Blueprint, request, jsonify

from api import cache
from api.services.dashboard_service import get_unique_buyers_count, get_loyal_buyers, get_top_products
from database.database_config import db

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/analytics", methods=["GET"])
@cache.cached()
def analytics():
    min_purchases = request.args.get("min_purchases", type=int)
    logger.info("Dashboard analytics requested - Cache missed")
    unique_buyers = get_unique_buyers_count(db.session)
    loyal_buyers = get_loyal_buyers(db.session, min_purchases)
    top_products = get_top_products(db.session, 3)

    return jsonify(
        {
            "unique_buyers": unique_buyers,
            "loyal_buyers": loyal_buyers,
            "top_products": top_products,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
