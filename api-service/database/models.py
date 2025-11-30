from datetime import datetime
import uuid
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from database import Base, db

purchase_product = Table(
    "purchase_product",
    Base.metadata,
    Column("purchase_id", ForeignKey("purchase.id"), primary_key=True),
    Column("product_id", ForeignKey("product.id"), primary_key=True),
)

Index("ix_purchase_product_product_id", purchase_product.c.product_id)

class Purchase(db.Model):
    __tablename__ = "purchase"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    supermarket_id: Mapped[str] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # store timezone-aware timestamps
        server_default=func.now(),  # DB sets it on INSERT
        nullable=False,
    )
    products: Mapped[List["Product"]] = relationship(
        secondary=purchase_product,
        back_populates="purchases",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    total_amount: Mapped[float] = mapped_column(nullable=False)

    __table_args__ = (
        # Disallow free purchases; amount must be strictly positive.
        CheckConstraint("total_amount > 0", name="ck_purchase_total_amount_positive"),
    )

class Product(db.Model):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    unit_price: Mapped[float] = mapped_column(nullable=False)

    purchases: Mapped[List["Purchase"]] = relationship(
        secondary=purchase_product,
        back_populates="products",
        init=False,
    )

    __table_args__ = (
        CheckConstraint("unit_price > 0", name="ck_product_price_positive"),
    )
