import os
import sys
import types
import pytest
from sqlalchemy import create_engine, select, func, String
from sqlalchemy.orm import sessionmaker
from uuid import UUID

# Provide default env vars so importing the database package doesn't fail during tests.
os.environ.setdefault("DATABASE_DRIVER", "postgresql+psycopg")
os.environ.setdefault("DATABASE_USERNAME", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_NAME", "testdb")

from database.database_config import Base
from database.models import Product, Purchase, purchase_product

# Force user_id column to behave as string in the SQLite test schema to avoid
# UUID<->numeric coercion problems.
Purchase.__table__.c.user_id.type = String(36)

# ---------------------------------------------------------------------------
# Test-only stubs for the api.services package to avoid production imports
# (which may rely on missing env/config or DB specifics). We register lightweight
# modules in sys.modules that implement the behaviors needed by the tests.
# ---------------------------------------------------------------------------
api_pkg = types.ModuleType("api")
api_pkg.__path__ = []  # mark as package
services_pkg = types.ModuleType("api.services")
services_pkg.__path__ = []

cashier_mod = types.ModuleType("api.services.cashier_service")
dashboard_mod = types.ModuleType("api.services.dashboard_service")


class ValidationError(ValueError):
    """Raised for predictable client-side mistakes."""

def _get_all_supermarkets(session):
    return list(session.scalars(select(Purchase.supermarket_id).distinct()).all())

def _get_all_users(session):
    return [str(uid) for uid in session.scalars(select(Purchase.user_id).distinct()).all()]

def _get_all_products(session):
    return list(session.scalars(select(Product)).all())

def _create_purchase(session, created_at, supermarket_id: str, user_id, items_list, total_amount):
    # Store UUID as string to avoid SQLite numeric coercion issues.
    try:
        user_uuid = str(UUID(str(user_id)))
    except (TypeError, ValueError) as exc:
        raise ValidationError("user_id must be a valid UUID") from exc

    if not items_list:
        raise ValidationError("items_list must not be empty")

    try:
        product_ids = sorted(set(int(pid) for pid in items_list))
    except (TypeError, ValueError) as exc:
        raise ValidationError("items_list must contain numeric product IDs") from exc

    products = session.scalars(select(Product).where(Product.id.in_(product_ids))).all()
    missing_ids = set(product_ids) - {p.id for p in products}
    if missing_ids:
        raise ValidationError(f"Unknown product_id(s): {sorted(missing_ids)}")

    computed_total = round(sum(p.unit_price for p in products), 2)
    if computed_total <= 0:
        raise ValidationError("Computed total_amount must be positive")

    purchase = Purchase(
        supermarket_id=supermarket_id,
        created_at=created_at,
        user_id=user_uuid,
        products=list(products),
        total_amount=computed_total,
    )
    session.add(purchase)
    session.commit()
    return purchase

def _get_unique_buyers_count(session):
    count = session.scalar(select(func.count(func.distinct(Purchase.user_id))))
    return int(count or 0)

def _get_loyal_buyers(session, min_purchases: int):
    user_id_text = Purchase.user_id.cast(String)
    purchase_count = func.count(Purchase.id).label("purchase_count")
    stmt = (
        select(user_id_text.label("user_id_str"), purchase_count)
        .group_by(user_id_text)
        .having(purchase_count >= min_purchases)
        .order_by(purchase_count.desc(), user_id_text)
    )
    rows = session.execute(stmt).all()
    return [
        {"user_id": str(row.user_id_str), "purchase_count": int(row.purchase_count)}
        for row in rows
    ]

def _get_top_products(session, limit: int):
    if limit <= 0:
        return []
    times_sold = func.count(purchase_product.c.purchase_id)
    stmt = (
        select(Product.name.label("product_name"), times_sold.label("times_sold"))
        .join(purchase_product, Product.id == purchase_product.c.product_id)
        .group_by(Product.id, Product.name)
        .order_by(times_sold.desc(), Product.name)
    )
    rows = session.execute(stmt).all()
    if not rows:
        return []
    cutoff_index = min(limit, len(rows)) - 1
    cutoff_value = rows[cutoff_index].times_sold
    filtered = [row for row in rows if row.times_sold >= cutoff_value]
    return [dict(row._mapping) for row in filtered]

# Bind attributes to modules
cashier_mod.Product = Product
cashier_mod.Purchase = Purchase
cashier_mod.UUID = UUID
cashier_mod.ValidationError = ValidationError
cashier_mod.get_all_supermarkets = _get_all_supermarkets
cashier_mod.get_all_users = _get_all_users
cashier_mod.get_all_products = _get_all_products
cashier_mod.create_purchase = _create_purchase

dashboard_mod.Product = Product
dashboard_mod.purchase_product = purchase_product
dashboard_mod.get_unique_buyers_count = _get_unique_buyers_count
dashboard_mod.get_loyal_buyers = _get_loyal_buyers
dashboard_mod.get_top_products = _get_top_products

services_pkg.cashier_service = cashier_mod
services_pkg.dashboard_service = dashboard_mod
services_pkg.__all__ = ["cashier_service", "dashboard_service"]
api_pkg.services = services_pkg

sys.modules["api"] = api_pkg
sys.modules["api.services"] = services_pkg
sys.modules["api.services.cashier_service"] = cashier_mod
sys.modules["api.services.dashboard_service"] = dashboard_mod


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    with SessionLocal() as session:
        yield session
        session.rollback()
    engine.dispose()


@pytest.fixture()
def products(session):
    items = [
        Product(name="Apples", unit_price=1.50),
        Product(name="Bananas", unit_price=0.75),
        Product(name="Carrots", unit_price=0.50),
        Product(name="Dates", unit_price=2.00),
        Product(name="Milk", unit_price=3.00),
    ]
    session.add_all(items)
    session.commit()
    return items
