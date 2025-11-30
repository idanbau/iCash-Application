from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import Product, Purchase, purchase_product


def get_unique_buyers_count(session: Session) -> int:
    """Count distinct buyers across all purchases."""
    count = session.scalar(select(func.count(func.distinct(Purchase.user_id))))
    return int(count or 0)


def get_loyal_buyers(session: Session, min_purchases: int) -> list[dict]:
    """Return buyers who purchased at least `min_purchases` times."""
    stmt = (
        select(Purchase.user_id, func.count(Purchase.id).label("purchase_count"))
        .select_from(Purchase)
        .group_by(Purchase.user_id)
        .having(func.count(Purchase.id) >= min_purchases)
        .order_by(func.count(Purchase.id).desc(), Purchase.user_id)
    )
    rows = session.execute(stmt).all()
    return [
        {"user_id": str(row.user_id), "purchase_count": int(row.purchase_count)}
        for row in rows
    ]


def get_top_products(session: Session, limit: int) -> list:
    """Return the top-selling products, including ties beyond the limit."""
    if limit <= 0:
        return []

    times_sold = func.count(purchase_product.c.purchase_id)

    stmt = (
        select(Product.name, times_sold.label("times_sold"))
        .join(purchase_product, Product.id == purchase_product.c.product_id)
        .group_by(Product.id, Product.name)
        .order_by(times_sold.desc())
        .fetch(limit, with_ties=True)  # <-- DB does the “ties” logic
    )
    rows = session.execute(stmt)
    return [dict(row._mapping) for row in rows]

