from flask import Flask

from api.extensions import cache
from api.routes.cashier_routes import cashier_bp
from api.routes.dashboard_routes import dashboard_bp
from database.database_config import init_app as init_db
from icash_common import setup_logging

def create_app() -> Flask:
    setup_logging()
    app = Flask(__name__)
    app.config.update(
        CACHE_TYPE="SimpleCache",        # per-process memory
        CACHE_DEFAULT_TIMEOUT=60,        # seconds
    )
    cache.init_app(app)
    init_db(app)
    app.register_blueprint(cashier_bp, url_prefix=f"/{cashier_bp.name}")
    app.register_blueprint(dashboard_bp, url_prefix=f"/{dashboard_bp.name}")
    return app
