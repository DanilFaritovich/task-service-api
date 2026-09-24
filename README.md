# Task Service API

**English** | [Русский](README.ru.md)

Async REST API microservice for managing **tasks, services, and users**.

Built with FastAPI, SQLAlchemy 2.x, PostgreSQL, Alembic, and Pydantic v2.

---

## Architecture

The project follows a layered architecture where HTTP handling, business logic, and data access are separated.

```text
                         ┌─────────────────────┐
                         │      HTTP Client     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI Router   │
                         │   HTTP / validation │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Service Layer    │
                         │    Business Logic   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   SQLAlchemy ORM    │
                         │   Async DB Access   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    PostgreSQL 16    │
                         └─────────────────────┘
```

### Request flow

```text
HTTP Request
     │
     ▼
FastAPI Router
     │
     ├── Request validation
     ├── Authentication / dependencies
     │
     ▼
Service Layer
     │
     ├── Business rules
     ├── Transaction management
     └── Database operations
     │
     ▼
SQLAlchemy AsyncSession
     │
     ▼
PostgreSQL
     │
     ▼
Pydantic Response Schema
     │
     ▼
HTTP Response
```

### Project structure

```text
.
├── backend/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── tasks.py
│   │   │   ├── users.py
│   │   │   └── services.py
│   │   │
│   │   ├── services/
│   │   │   ├── dashboard.py
│   │   │   ├── tasks.py
│   │   │   └── users.py
│   │   │
│   │   ├── deps.py
│   │   └── main.py
│   │
│   └── database/
│       ├── models.py
│       ├── schemas.py
│       ├── base.py
│       └── triggers/
│           └── ...
│
├── tests/
│   ├── test_tasks.py
│   ├── test_users.py
│   └── ...
│
├── alembic/
│   └── versions/
│
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── README.md
```

### Architecture layers

#### API Layer

Located in `backend/api/routers/`.

Responsible for:

* HTTP endpoints
* request/response handling
* dependency injection
* input validation
* HTTP status codes

Routers should contain minimal business logic.

```text
Router
  │
  └── delegates work to
          │
          ▼
      Service Layer
```

#### Service Layer

Located in `backend/api/services/`.

Contains application and business logic.

Examples:

* `TasksService`
* `UsersService`
* `DashboardService`

This layer is independent from HTTP-specific details, which makes the business logic easier to test and reuse.

#### Database Layer

Located in `backend/database/`.

Contains:

* SQLAlchemy ORM models
* Pydantic schemas
* async database engine
* session configuration
* PostgreSQL-specific database logic

Database migrations are managed through Alembic.

#### PostgreSQL Triggers

Database triggers are stored in:

```text
backend/database/triggers/
```

and managed through `alembic_utils`.

One of the triggers automatically assigns available services to newly created users.

This logic is intentionally implemented at the database level because it represents a database integrity/business rule that should also work outside the API.

---

## Key Architectural Decisions

### Service Layer

Business logic is isolated from FastAPI routers.

Instead of putting database operations and business rules directly inside endpoints:

```text
Router → Service → Database
```

This keeps controllers thin and makes the application easier to test and extend.

### Async Database Access

The application uses SQLAlchemy 2.x with asynchronous sessions.

```text
FastAPI
   │
   ▼
AsyncSession
   │
   ▼
PostgreSQL
```

This allows database operations to integrate naturally with FastAPI's async request handling.

### ContextVar Session Management

`ContextVar` is used to manage the database session within the current execution context.

This allows application components to access the current session without explicitly passing it through every layer.

### PostgreSQL Triggers

Some database-level rules are implemented using PostgreSQL triggers.

Migrations and trigger definitions are managed with Alembic and `alembic_utils`.

### IntegrityError Handling

Database integrity violations are converted into appropriate HTTP responses.

For example, a foreign-key violation is returned as:

```text
HTTP 400 Bad Request
```

instead of exposing an internal:

```text
HTTP 500 Internal Server Error
```

---

## Tech Stack

| Technology     | Purpose                              |
| -------------- | ------------------------------------ |
| Python 3.14    | Application runtime                  |
| FastAPI 0.129  | REST API framework                   |
| SQLAlchemy 2.x | ORM and async database access        |
| PostgreSQL 16  | Relational database                  |
| Alembic        | Database migrations                  |
| alembic_utils  | PostgreSQL database objects/triggers |
| Pydantic v2    | Data validation and serialization    |
| pytest         | Testing                              |
| pytest-asyncio | Async test support                   |
| httpx          | HTTP client for integration tests    |
| Docker         | Containerization                     |
| Docker Compose | Local development environment        |

---

## Features

* Async REST API
* CRUD operations for tasks, users, and services
* Service layer architecture
* Async SQLAlchemy 2.x
* PostgreSQL 16
* Alembic database migrations
* PostgreSQL triggers
* Pydantic v2 validation
* Centralized database integrity error handling
* Integration tests
* Docker-based PostgreSQL environment
* Automatic service assignment for new users

---

## Quick Start

### Prerequisites

* Docker
* Docker Compose
* Python 3.12+

> Python 3.14 is used for development. Python 3.12+ is currently required by the project setup.

### 1. Clone the repository

```bash
git clone <repo-url>
cd task-service-api
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Configure the required database settings in `.env`.

### 3. Start PostgreSQL

```bash
docker compose up -d
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply database migrations

```bash
alembic upgrade head
```

### 6. Run tests

```bash
pytest tests/ -v
```

### 7. Start the application

```bash
python main.py
```

The API will be available at:

```text
http://localhost:8000
```

---

## API Documentation

FastAPI automatically provides interactive API documentation.

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

---

## Testing

Run the complete test suite:

```bash
pytest tests/ -v
```

Run a specific test module:

```bash
pytest tests/test_tasks.py -v
```

Run tests with coverage:

```bash
pytest --cov=backend tests/
```

The test suite uses:

* `pytest`
* `pytest-asyncio`
* `httpx`

Integration tests interact with the API through HTTP requests and verify the complete request flow.

---

## Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback the latest migration:

```bash
alembic downgrade -1
```

Show the current migration:

```bash
alembic current
```

---

## Development Workflow

The typical development workflow is:

```text
1. Modify SQLAlchemy models
           │
           ▼
2. Generate Alembic migration
           │
           ▼
3. Apply migration
           │
           ▼
4. Implement Service Layer logic
           │
           ▼
5. Expose functionality through Router
           │
           ▼
6. Add integration tests
           │
           ▼
7. Run test suite
```

---

## Roadmap

Planned improvements:

* JWT authentication
* Unit tests for service layer
* GitHub Actions CI/CD
* Redis caching
* Structured logging with `structlog`
* Prometheus metrics
* Production Docker configuration
* Health checks
* API versioning

---

## License

This project is licensed under the MIT License.
