import csv
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Allow running as a script (python database/seed.py) by adding repo root to sys.path
if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[1]
    script_dir = str(Path(__file__).resolve().parent)
    sys.path.insert(0, str(repo_root))

from database.database_config import Base, SQLAlchemy_DATABASE
from database.models import Purchase, Product
from icash_common import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def seed_db(database_url: str | None = None):
    """Create tables and seed purchases from the CSV once, using plain SQLAlchemy."""
    products_path = Path(__file__).resolve().parents[0] / "data" / "products_list.csv"
    purchases_path = Path(__file__).resolve().parents[0] / "data" / "purchases.csv"
    if not products_path.exists() or not purchases_path.exists():
        logger.warning(
            "Seed skipped: CSV files not found",
            extra={"products_path": str(products_path), "purchases_path": str(purchases_path)},
        )
        return

    logger.info(
        "Seeding database from CSV files, products_path: %s, purchases_path: %s",
        str(products_path),
        str(purchases_path),
    )

    engine = create_engine(SQLAlchemy_DATABASE)
    Base.metadata.create_all(engine)
    logger.info("Ensured all tables exist")

    with Session(engine) as session:
        already_loaded = session.execute(select(Purchase.id).limit(1)).first()
        if already_loaded:
            logger.info("Seed skipped: purchases already present")
            return

        with products_path.open(newline="", encoding="utf-8-sig") as products_file:
            reader = csv.DictReader(products_file)
            product_rows = list(reader)
            for row in product_rows:
                product = Product(name=row["product_name"], unit_price=float(row["unit_price"]))
                session.add(product)

        # Make sure new products get ids
        session.flush()

        # Simple lookup from product name to Product object
        product_by_name: dict[str, Product] = {
            p.name: p for p in session.scalars(select(Product)).all()
        }

        with purchases_path.open(newline="", encoding="utf-8-sig") as purchases_file:
            reader = csv.DictReader(purchases_file)
            purchase_rows = list(reader)
            for row in purchase_rows:
                supermarket_code = row["supermarket_id"].strip()
                try:
                    user_uuid = uuid.UUID(row["user_id"])
                except (ValueError, TypeError) as exc:
                    logger.warning("Skipping row with invalid user_id: %s", row.get("user_id"))
                    continue

                product_names = [
                    name.strip()
                    for name in row["items_list"].split(",")
                    if name.strip()
                ]
                purchase_products = [
                    product_by_name[name]
                    for name in product_names
                ]

                purchase = Purchase(
                    supermarket_id=supermarket_code,
                    created_at=datetime.fromisoformat(row["timestamp"]),
                    user_id=user_uuid,
                    products=purchase_products,
                    total_amount=float(row["total_amount"]),
                )
                session.add(purchase)
        session.commit()
        logger.info(
            "Seed complete, products_loaded: %d, purchases_loaded: %d",
            len(product_rows),
            len(purchase_rows),
        )
if __name__ == "__main__":
    seed_db()
