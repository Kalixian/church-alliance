# church-alliance

A project created with FastAPI CLI.

## Quick Start

### With Docker (API + React app together)

```bash
cp example.env .env                     # then fill in
cp frontend/example.env frontend/.env   # then fill in
docker compose -f docker-compose.dev.yml up --build

# once, in another terminal while it runs: add the starter courses
docker compose -f docker-compose.dev.yml exec api python -m app.db.certification.seed
```

React app on http://localhost:5173, API docs on http://localhost:8000/docs.
Production deployment: see `deploy/README.md`.

### Start the development server without Docker

```bash
uv run python -m app.db.certification.seed   # once: add the starter courses
uv run fastapi dev
```

Visit http://localhost:8000

The seed adds the courses from the old static Courses page, skipping any
whose names already exist, so it is safe to re-run.

### Deploy to FastAPI Cloud

> FastAPI Cloud is currently in private beta. Join the waitlist at https://fastapicloud.com

```bash
uv run fastapi deploy
```

## Project Structure

- `main.py` - Your FastAPI application
- `pyproject.toml` - Project dependencies

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [FastAPI Cloud](https://fastapicloud.com)
