import logging
from typing import Dict, List
from uuid import uuid4

import requests
from flask import current_app
from requests import RequestException

log = logging.getLogger(__name__)

def fetch_catalog() -> Dict[str, List]:
    url = current_app.config.get("CATALOG_URL")
    log.info("Fetching catalog from %s", url)
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        log.info("Catalog fetched successfully with %d products", len(payload.get("products", [])))
        return {
            "products": payload["products"],
            "supermarkets": payload["supermarkets"],
            "users": payload["users"],
        }
    except RequestException as e:
        log.exception("Catalog service failed in use: %s", e)
        raise e

def create_purchase(
        is_new_user: bool,
        user_id: str|None,
        supermarket_id: str,
        item_list: list,
        total_amount: float
) -> dict:
    try:
        payload = {
            "supermarket_id": supermarket_id,
            "user_id": user_id if not is_new_user and user_id else str(uuid4()),
            "items_list": item_list,
            "total_amount": total_amount,
        }
        url = current_app.config.get("CREATE_PURCHASE_URL")
        log.info("Creating purchase to %s", url)
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        log.info("purchase created successfully, user_id: %s", user_id)
    except RequestException as e:
        log.exception("Create purchase failed in use: %s", e)
        raise e
