import os

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

class Config:
    CATALOG_URL = os.getenv(
        "CATALOG_SERVICE_URL", "http://127.0.0.1:8001/cashier/catalog"
    )
    CREATE_PURCHASE_URL = os.getenv(
        "CREATE_PURCHASE_URL", "http://127.0.0.1:8001/cashier/create_purchase"
    )
    MESSAGES = {
        STATUS_SUCCESS: "Purchase created successfully!",
        STATUS_ERROR: "Failed to create purchase",
    }
