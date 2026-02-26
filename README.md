# HR Employee Search Microservice

Microservice tìm kiếm nhân viên trong organization. Chỉ triển khai **Search API**, không có CRUD, import/export.

## Cách chạy app

### Local (virtual environment)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Truy cập:
- API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker

```bash
# Build image
docker build -t hr-employee-search .

# Chạy container
docker run -p 8000:8000 hr-employee-search
```

API: http://localhost:8000/docs

### Docker Compose (tùy chọn)

```yaml
services:
  hr-search:
    build: .
    ports:
      - "8000:8000"
```

## Cách chạy test

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

**Query params:**
- `org_id` (required): Organization ID
- `name` (optional): Partial match, case-insensitive
- `department`, `location`, `position` (optional): Exact match
- `limit` (default 20, max 100): Page size
- `offset` (default 0): Pagination offset

**Ví dụ:**
```
GET /api/v1/employees/search?org_id=org_a&name=john&limit=10
```

**Response:** JSON với `items`, `total`, `limit`, `offset`. Các field trong mỗi item phụ thuộc cấu hình organization.

## Kiến trúc tổng thể

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

- **API layer**: FastAPI routes, rate limit dependency
- **Service layer**: `EmployeeSearchService` – orchestrate search, apply column projection
- **Config**: `column_config` – org → danh sách cột, thứ tự
- **Storage**: `InMemoryEmployeeStore` – interface giống DB, dễ thay bằng PostgreSQL sau

## Thiết kế Rate Limiting

- **Algorithm**: Sliding window (deque timestamps)
- **Chuẩn library**: Chỉ dùng `threading`, `time`, `collections.deque`
- **Key**: `org:{org_id}` hoặc `ip:{ip}` khi không có org_id
- **Limit**: 100 requests / phút / key
- **Response**: HTTP 429, header `Retry-After: 60`
- **Vị trí**: FastAPI dependency `verify_rate_limit` trước route handler

## Dynamic Columns

1. **Config** (`app/services/column_config.py`): Dict `org_id → [column1, column2, ...]`
2. **Projection**: Trong `_project_employee()`, chỉ lấy các cột trong config, đúng thứ tự
3. **Whitelist**: `ALLOWED_COLUMNS` – chỉ cho phép các field an toàn
4. **Bảo mật**:
   - Không bao giờ trả `org_id` trong response
   - Không trả field ngoài config
   - Mỗi org chỉ thấy data của chính mình (filter `org_id` ở DB layer)

## Performance & Scalability

### Giả định
- Hàng triệu employee
- Filter và pagination phải xử lý ở DB layer

### Thiết kế hiện tại (in-memory)
- **Org index**: `_index_by_org` – chỉ scan employees của org đang query
- **Lazy filter**: Iterate + filter, không load toàn bộ vào memory
- **Pagination**: Skip offset, take limit trong vòng lặp

### Hướng scale khi chuyển sang DB thật
1. **PostgreSQL**: Thay `InMemoryEmployeeStore` bằng adapter gọi SQL
2. **Index**: `(org_id, department)`, `(org_id, location)`, full-text trên `name`
3. **Cursor pagination**: Có thể đổi từ offset sang cursor (keyset) cho dữ liệu lớn
4. **Rate limit**: Chuyển sang Redis để share state giữa nhiều instance
5. **Caching**: Cache kết quả search theo hash của params (TTL ngắn)

## Cấu trúc thư mục

```
hr_employee/
├── app/
│   ├── main.py           # FastAPI app, exception handlers
│   ├── config.py         # App config
│   ├── api/v1/
│   │   └── employees.py  # Search endpoint
│   ├── models/           # Employee entity
│   ├── schemas/          # Pydantic request/response
│   ├── services/         # Search, column config
│   ├── middleware/       # Rate limit logic
│   └── db/               # In-memory store (replaceable)
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```
## OpenAPI

FastAPI tự sinh OpenAPI tại `/docs` và `/redoc`. Schema có ví dụ request/response trong Pydantic `model_config`.

