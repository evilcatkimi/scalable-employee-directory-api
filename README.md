# HR Employee Search Microservice

This microservice provides employee search within an organization. It implements only the **Search API** — there is no CRUD or import/export functionality.

## How to run the app

### Local (virtual environment)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Access:

- API: http://localhost:8000
- OpenAPI (Swagger UI): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker

```bash
# Build image
docker build -t hr-employee-search .

# Run container
docker run -p 8000:8000 hr-employee-search
```

Open the API docs at: http://localhost:8000/docs

### Docker Compose (optional)

```yaml
services:
  hr-search:
    build: .
    ports:
      - "8000:8000"
```

## How to run tests

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

## API

### Search Employees

```
GET /api/v1/employees/search
```

Query parameters:

- `org_id` (required): Organization ID
- `name` (optional): Partial match, case-insensitive
- `department`, `location`, `position` (optional): Exact match
- `limit` (default 20, max 100): Page size
- `offset` (default 0): Pagination offset

Example:

```
GET /api/v1/employees/search?org_id=org_a&name=john&limit=10
```

Response: JSON containing `items`, `total`, `limit`, and `offset`. The fields included in each item depend on the organization's column configuration.

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│   FastAPI App    │────▶│  Search Service │
└─────────────┘     │  - Rate limit    │     │  - Filter       │
                    │  - Routing       │     │  - Project cols │
                    └──────────────────┘     └────────┬────────┘
                                                      │
                                                      ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │ Column Config    │     │  In-Memory DB   │
                    │ (org → columns)  │     │  - org index    │
                    └──────────────────┘     │  - filter/paginate│
                                             └─────────────────┘
```

- API layer: FastAPI routes and the rate limit dependency
- Service layer: `EmployeeSearchService` — orchestrates searching and applies column projection
- Config: `column_config` — maps `org_id` to a list of columns and their order
- Storage: `InMemoryEmployeeStore` — an in-memory store with an interface that can be replaced by PostgreSQL later

## Rate Limiting Design

- Algorithm: Sliding window using a deque of timestamps
- Standard library only: `threading`, `time`, `collections.deque`
- Key: `org:{org_id}` or `ip:{ip}` when `org_id` is not provided
- Limit: 100 requests per minute per key
- Response: HTTP 429 with header `Retry-After: 60`
- Location: FastAPI dependency `verify_rate_limit` applied before route handlers

## Dynamic Columns

1. Config (`app/services/column_config.py`): a dict mapping `org_id` → `[column1, column2, ...]`
2. Projection: In `_project_employee()`, only columns listed in the org's config are returned, in the configured order
3. Whitelist: `ALLOWED_COLUMNS` — only safe fields are allowed
4. Security:
   - Never return `org_id` in responses
   - Do not return fields outside the configured columns
   - Each org only sees its own data (filter by `org_id` at the DB layer)

## Performance & Scalability

### Assumptions

- Millions of employees
- Filtering and pagination must be handled at the DB/storage layer

### Current (in-memory) design

- Org index: `_index_by_org` — only scans employees for the queried org
- Lazy filtering: iterate and filter without loading everything into memory
- Pagination: skip `offset`, take `limit` during iteration

### Scaling to a real DB

1. PostgreSQL: replace `InMemoryEmployeeStore` with a SQL adapter
2. Indexes: `(org_id, department)`, `(org_id, location)`, and full-text search on `name`
3. Cursor pagination: switch from offset to keyset (cursor) pagination for large datasets
4. Rate limit: move to Redis to share rate limit state across instances
5. Caching: cache search results keyed by a hash of the parameters (short TTL)

## Project Structure

```
hr_employee/
├── app/
│   ├── main.py           # FastAPI app, exception handlers
│   ├── config.py         # App config
│   ├── api/v1/
│   │   └── employees.py  # Search endpoint
│   ├── models/           # Employee entity
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Search and column configuration
│   ├── middleware/       # Rate limit logic
│   └── db/               # In-memory store (replaceable)
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

## OpenAPI

FastAPI automatically generates OpenAPI documentation at `/docs` and `/redoc`. The Pydantic models include example request/response data in their `model_config`.
