# iCash Microservices Playground

Interactive microservice demo for a supermarket chain with three branches, ten products, and one-unit-per-product purchases. The stack is **Python + Flask + SQLAlchemy** packaged with **Docker Compose**.

## System Diagram
```
[Cashier UI (Flask)] --> [API Service (Flask REST)] --> [PostgreSQL]
                                   ^
[Owner Dashboard (Flask)] ----------+

Shared assets: common/ (templates, CSS, logging)
```

## Services
- **db**: PostgreSQL 18-alpine.
- **api** (`api-service/`): REST backend; exposes cashier + analytics endpoints; Seeds products and historical purchases, loads CSV data at startup.
- **cashier** (`cashier-service/`): Clerk-facing UI to create purchases, supports new/existing users.
- **dashboard** (`dashboard-service/`): Owner-facing UI showing unique buyers, loyal buyers (≥3 by default), and top-selling products with ties.

## Data Model
- `product(id, name, unit_price)`
- `purchase(id, supermarket_id, created_at, user_id, total_amount)`
- `purchase_product(purchase_id, product_id)` many-to-many link

## Datasets
- `api-service/database/data/products_list.csv` – 10 products with prices.
- `api-service/database/data/purchases.csv` – historical purchases across 3 supermarkets.

## Prerequisites
- Docker + Docker Compose v2
- Make sure ports `8000` and `8002` are free.

## Quick Start
```bash
docker compose up
```
Then open:
- Cashier UI: http://localhost:8000/
- Owner Dashboard: http://localhost:8002/

Compose also exposes the API to other services on the internal network (`api:8001`). If you want host access to the API, add `ports: ["8001:8001"]` under the `api` service in `docker-compose.yml`.

## API Endpoints (served by api-service)
- `GET /cashier/catalog` – lists supermarkets, known users, and products (cached 60s).
- `POST /cashier/create_purchase` – body: `{supermarket_id, user_id, items_list:[product_id], total_amount}`; returns new object.
- `GET /dashboard/analytics?min_purchases=3` – returns `{unique_buyers, loyal_buyers, top_products, generated_at}`.

## Frontend Flows
- **Cashier**: choose supermarket → pick new/existing user → select products (one unit each) → submit; generates UUID for guests.
- **Dashboard**: shows unique buyers count, loyal buyers table, and top products (ties included) using owner-configured `MIN_PURCHASES` (default 3).

## Configuration
Environment variables are set in `docker-compose.yml`:
- `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_NAME` for the API service
- `CATALOG_SERVICE_URL`, `CREATE_PURCHASE_URL` for the Cashier UI
- `ANALYTICS_URL`, `SECRET_KEY`, `MIN_PURCHASES` for the Dashboard

## Caching
- Flask-Caching `SimpleCache` (per-container memory) fronts two endpoints: `GET /cashier/users_orders_purchases` and `GET /dashboard/analytics`. Default TTL is 60 seconds; disable or adjust via `CACHE_DEFAULT_TIMEOUT` in `api-service/api/__init__.py`.

## Runtime & Concurrency
- The API container starts via `entrypoint.sh`, then runs `gunicorn` with `-w 4 -k gthread -t 60 -b 0.0.0.0:8001`. Four worker processes with the threaded worker class allow handling multiple requests in parallel; adjust with the `GUNICORN_CMD_ARGS` env var if you need a different worker count or timeout.

## Seeding Logic
`api-service/entrypoint.sh` waits for Postgres, creates tables, and calls `database/seed.py` to load the CSVs (idempotent: skips if purchases already exist).

## Testing
Pytest suites live in `api-service/tests/`. From inside `api-service/` you can run:
```bash
pip install -r requirements.txt
pytest
```

## Troubleshooting
- **DB not ready**: the API container loops until Postgres accepts connections.
- **Port in use**: adjust the published ports in `docker-compose.yml`.
- **Seed not applied**: ensure `products_list.csv` and `purchases.csv` are present; delete the volume `pgdata` to reseed from scratch.
