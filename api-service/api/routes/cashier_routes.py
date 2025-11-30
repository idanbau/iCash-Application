import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from api import cache
from api.services.cashier_service import get_all_supermarkets, get_all_users, get_all_products, create_purchase
from database import db

cashier_bp = Blueprint("cashier", __name__)
logger = logging.getLogger(__name__)

@cashier_bp.route("/catalog")
@cache.cached()
def catalog():
    return jsonify({
        "supermarkets": get_all_supermarkets(db.session),
        "users": get_all_users(db.session),
        "products": get_all_products(db.session)
    })


@cashier_bp.route("/create_purchase", methods=["POST"])
def create_purchase_route():
    data = request.get_json()
    logger.info("Received create_purchase request", extra={
        "supermarket_id": data.get("supermarket_id"),
        "user_id": data.get("user_id"),
        "items_count": len(data.get("items_list") or []),
    })
    create_purchase(
        db.session,
        **data,
        created_at=datetime.now(timezone.utc)
    )
    return "success", 201
