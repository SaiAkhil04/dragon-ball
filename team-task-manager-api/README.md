# Team Task Manager API

An AI-assisted backend portfolio project for demonstrating REST API design, relational data modeling, authentication, role-based authorization, SQL querying, data-quality checks, and automated tests.

**AI-use disclosure:** This starter project was created with AI assistance during portfolio/application preparation. Review the code, rerun the tests, make your own improvements, and understand each design choice before presenting it. Do not claim it was built earlier or unaided.

## Features
- FastAPI REST API with interactive docs at /docs.
- Registration and login with password hashing and JWT access tokens.
- Member/admin roles; members access their own tasks, admins can list users and all tasks.
- Task create, read, update, delete, and status filtering.
- SQLAlchemy ORM using SQLite by default.
- SQL examples for workload summaries and data-quality checks.
- 11 automated API tests and a GitHub Actions test workflow.

## Run locally
1. Create and activate a Python 3.11+ virtual environment.
2. Run: python -m pip install -r requirements.txt
3. Copy .env.example to .env and replace JWT_SECRET_KEY with a long random secret.
4. Run: uvicorn app.main:app --reload
5. Open http://127.0.0.1:8000/docs

## Run tests
Run: pytest -q

Tests use an isolated in-memory SQLite database and do not require a running server.

## Main endpoints
- GET /health
- POST /auth/register
- POST /auth/login
- GET /users/me
- GET /users (admin only)
- POST /tasks
- GET /tasks (optional task_status filter)
- GET /tasks/{task_id}
- PATCH /tasks/{task_id}
- DELETE /tasks/{task_id}

## Project structure
- app/: configuration, database, models, schemas, authentication, API routes, admin seeding.
- sql/analytics_queries.sql: task status summaries, counts by owner, and data-quality checks.
- tests/: API authentication, authorization, CRUD, and validation tests.
- .github/workflows/tests.yml: run pytest on push and pull request.

## Limitations
SQLite is the local default. Before production use, add migrations, rate limiting, audit logging, pagination, account lifecycle flows, stronger secret management, and operational monitoring. This project is a learning/demo API, not a production-ready service or a hosted web demo.

## Suggested walkthrough
Register and log in using the OpenAPI docs, create and update a task, filter by status, then create a second user and demonstrate that one user cannot read another user's task. Explain the tests in tests/test_api.py and SQL checks in sql/analytics_queries.sql.
