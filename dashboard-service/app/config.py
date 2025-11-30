import os


class Config:
    ANALYTICS_URL = os.getenv(
        "ANALYTICS_URL", "http://127.0.0.1:8001/dashboard/analytics"
    )
    MIN_PURCHASES = int(os.getenv("MIN_PURCHASES", 3))
