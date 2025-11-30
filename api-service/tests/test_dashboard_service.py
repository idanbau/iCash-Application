from datetime import datetime, timezone
from uuid import UUID, uuid5, NAMESPACE_DNS

from api.services import dashboard_service, cashier_service

# Deterministic UUIDs for predictable ordering/assertions in tests
LOYAL_BUYER_ID = UUID("11111111-1111-1111-1111-111111111111")
STEADY_BUYER_ID = UUID("22222222-2222-2222-2222-222222222222")
OCCASIONAL_BUYER_ID = UUID("33333333-3333-3333-3333-333333333333")


def _record_sales(session, product, count: int, user_prefix: str = "user"):
    """Create `count` purchases each containing the given product."""
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(count):
        cashier_service.create_purchase(
            session=session,
            created_at=now,
            supermarket_id=f"store-{i % 2}",
            user_id=uuid5(NAMESPACE_DNS, f"{user_prefix}-{i}"),
            items_list=[str(product.id)],
            total_amount=product.unit_price,
        )


def test_get_unique_buyers_count(session, products):
    assert dashboard_service.get_unique_buyers_count(session) == 0

    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user_one = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    user_two = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    cashier_service.create_purchase(session, now, "S1", user_one, [str(products[0].id)], 10)
    cashier_service.create_purchase(session, now, "S1", user_one, [str(products[1].id)], 12)
    cashier_service.create_purchase(session, now, "S2", user_two, [str(products[2].id)], 5)
    session.commit()

    assert dashboard_service.get_unique_buyers_count(session) == 2


def test_get_loyal_buyers_sorted_and_threshold(session, products):
    now = datetime(2024, 1, 2, tzinfo=timezone.utc)
    for _ in range(3):
        cashier_service.create_purchase(session, now, "S1", LOYAL_BUYER_ID, [str(products[0].id)], 5)
    for _ in range(2):
        cashier_service.create_purchase(session, now, "S2", STEADY_BUYER_ID, [str(products[1].id)], 7)
    cashier_service.create_purchase(session, now, "S3", OCCASIONAL_BUYER_ID, [str(products[2].id)], 3)
    session.commit()

    result = dashboard_service.get_loyal_buyers(session, min_purchases=2)
    assert result == [
        {"user_id": str(LOYAL_BUYER_ID), "purchase_count": 3},
        {"user_id": str(STEADY_BUYER_ID), "purchase_count": 2},
    ]
    assert dashboard_service.get_loyal_buyers(session, min_purchases=4) == []


def test_get_top_products_includes_ties_at_limit_one(session, products):
    _record_sales(session, products[0], count=3, user_prefix="apple")
    _record_sales(session, products[1], count=3, user_prefix="banana")
    _record_sales(session, products[2], count=1, user_prefix="carrot")
    session.commit()

    top = dashboard_service.get_top_products(session, limit=1)

    assert len(top) == 2
    assert {item["product_name"] for item in top} == {products[0].name, products[1].name}
    assert all(item["times_sold"] == 3 for item in top)


def test_get_top_products_returns_ties_beyond_limit(session, products):
    _record_sales(session, products[0], count=3, user_prefix="apple")
    _record_sales(session, products[1], count=2, user_prefix="banana")
    _record_sales(session, products[2], count=2, user_prefix="carrot")
    _record_sales(session, products[3], count=1, user_prefix="dates")
    session.commit()

    top = dashboard_service.get_top_products(session, limit=2)

    assert [item["product_name"] for item in top] == [
        products[0].name,
        products[1].name,
        products[2].name,
    ]
    assert [item["times_sold"] for item in top] == [3, 2, 2]


def test_get_top_products_with_zero_limit_returns_empty(session):
    assert dashboard_service.get_top_products(session, limit=0) == []


def test_get_top_products_ties_extend_past_limit(session, products):
    """When limit cuts through a tie, all tied products should be returned."""
    _record_sales(session, products[0], count=5, user_prefix="p0")  # top seller
    _record_sales(session, products[1], count=4, user_prefix="p1")
    _record_sales(session, products[2], count=3, user_prefix="p2")
    _record_sales(session, products[3], count=3, user_prefix="p3")
    _record_sales(session, products[4], count=2, user_prefix="p4")
    session.commit()

    top = dashboard_service.get_top_products(session, limit=3)

    # Expect 4 entries because positions 3 and 4 are tied on times_sold.
    assert len(top) == 4
    assert [item["product_name"] for item in top] == [
        products[0].name,
        products[1].name,
        products[2].name,
        products[3].name,
    ]
    assert [item["times_sold"] for item in top] == [5, 4, 3, 3]