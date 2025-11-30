# api/services/cashier_service.py
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, noload

from database.models import Product, Purchase

logger = logging.getLogger(__name__)

class ValidationError(ValueError):
    """Raised for predictable client-side mistakes."""


def get_all_supermarkets(session: Session) -> list[str]:
    return list(session.scalars(select(Purchase.supermarket_id).distinct()).all())

def get_all_users(session: Session) -> list[UUID]:
    return list(session.scalars(select(Purchase.user_id).distinct()).all())

def get_all_products(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).options(noload(Product.purchases))).all())

def create_purchase(session: Session, created_at, supermarket_id: str, user_id, items_list: list[str], total_amount):
    try:
        user_uuid = UUID(str(user_id))
    except (ValueError, TypeError) as exc:
        raise ValidationError("user_id must be a valid UUID") from exc

    product_ids = [int(pid) for pid in items_list]
    products = session.scalars(
        select(Product).where(Product.id.in_(product_ids))
    ).all()
    logger.info(
        "Creating purchase: supermarket_id=%s user_id=%s items_count=%d total_amount=%s created_at=%s",
        supermarket_id,
        user_uuid,
        len(items_list),
        total_amount,
        created_at,
    )

    purchase = Purchase(
        supermarket_id=supermarket_id,
        created_at=created_at,
        user_id=user_uuid,
        products=list(products),
        total_amount=total_amount,
    )
    session.add(purchase)
    try:
        session.commit()
        logger.info(
            "Purchase created successfully: purchase_id=%s supermarket_id=%s user_id=%s products_count=%d total_amount=%s",
            purchase.id,
            supermarket_id,
            user_uuid,
            len(products),
            total_amount,
        )
    except Exception:
        logger.exception(
            "Failed to commit purchase for user_id=%s supermarket_id=%s product_ids=%s",
            user_uuid,
            supermarket_id,
            product_ids,
        )
        session.rollback()
        raise

