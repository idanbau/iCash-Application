import logging
from typing import Any, Dict

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def fetch_analytics(min_purchases: int) -> Dict[str, Any]:
    """Fetch analytics snapshot from the API service."""
    url = current_app.config.get("ANALYTICS_URL")
    params = {"min_purchases": min_purchases}

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()
