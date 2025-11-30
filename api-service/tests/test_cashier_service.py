from datetime import datetime, timezone
from uuid import UUID

import pytest

from api.services import cashier_service
from database.models import Product, Purchase

USER_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1")
USER_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2")
USER_X = UUID("cccccccc-cccc-cccc-cccc-ccccccccccc3")


def test_get_all_supermarkets_and_users(session, products):
    now = datetime(2024, 2, 1, tzinfo=timezone.utc)
    cashier_service.create_purchase(session, now, "S1", USER_A, [str(products[0].id)], 4)
    cashier_service.create_purchase(session, now, "S2", USER_B, [str(products[1].id)], 6)
    cashier_service.create_purchase(session, now, "S1", USER_B, [str(products[2].id)], 8)
    session.commit()

    assert set(cashier_service.get_all_supermarkets(session)) == {"S1", "S2"}
    assert set(cashier_service.get_all_users(session)) == {str(USER_A), str(USER_B)}


def test_get_all_products(session, products):
    fetched = cashier_service.get_all_products(session)

    assert {p.name for p in fetched} == {"Apples", "Bananas", "Carrots", "Dates", "Milk"}
    assert all(isinstance(p, Product) for p in fetched)


def test_create_purchase_deduplicates_items(session, products):
    now = datetime(2024, 3, 1, tzinfo=timezone.utc)
    purchase = cashier_service.create_purchase(
        session,
        now,
        "S1",
        USER_X,
        [str(products[0].id), str(products[0].id), str(products[1].id)],
        total_amount=99.0,
    )
    session.commit()
    session.refresh(purchase)

    # total is recomputed from unique products, not client input
    assert purchase.total_amount == pytest.approx(products[0].unit_price + products[1].unit_price)
    assert sorted(p.id for p in purchase.products) == [products[0].id, products[1].id]
    assert session.get(Purchase, purchase.id) is not None


def test_create_purchase_overrides_client_total(session, products):
    now = datetime(2024, 4, 1, tzinfo=timezone.utc)
    purchase = cashier_service.create_purchase(
        session,
        now,
        "S2",
        USER_X,
        [str(products[2].id)],
        total_amount=-100,
    )
    assert purchase.total_amount == pytest.approx(products[2].unit_price)


def test_create_purchase_requires_items(session):
    now = datetime(2024, 5, 1, tzinfo=timezone.utc)
    with pytest.raises(cashier_service.ValidationError):
        cashier_service.create_purchase(
            session,
            now,
            "S1",
            USER_X,
            [],
            total_amount=0,
        )


def test_create_purchase_rejects_invalid_uuid(session, products):
    now = datetime(2024, 6, 1, tzinfo=timezone.utc)
    with pytest.raises(cashier_service.ValidationError):
        cashier_service.create_purchase(
            session,
            now,
            "S1",
            "not-a-uuid",
            [str(products[0].id)],
            total_amount=1,
        )


def test_create_purchase_rejects_non_numeric_product_id(session):
    now = datetime(2024, 7, 1, tzinfo=timezone.utc)
    with pytest.raises(cashier_service.ValidationError):
        cashier_service.create_purchase(
            session,
            now,
            "S1",
            USER_X,
            ["abc"],
            total_amount=1,
        )


def test_create_purchase_rejects_unknown_product(session, products):
    now = datetime(2024, 8, 1, tzinfo=timezone.utc)
    missing_id = max(p.id for p in products) + 1
    with pytest.raises(cashier_service.ValidationError):
        cashier_service.create_purchase(
            session,
            now,
            "S1",
            USER_X,
            [str(missing_id)],
            total_amount=1,
        )
