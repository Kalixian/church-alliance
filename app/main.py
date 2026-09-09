from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import create_tables
from app.api.v1.auth import router as auth_router
from app.api.v1.events import router as events_router
from app.api.v1.certifications import router as certifications_router
from app.api.v1.assets import router as assets_router
from app.api.v1.galleries import router as galleries_router, pictures_router
from app.api.v1.users import router as users_router
from app.api.v1.articles import router as articles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Church Alliance API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://192.168.4.84:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://192.168.4.84:5173',
        'http://church-alliance.com',
        'http://newton.jpoley.com:5173',
        'http://newton.jpoley.com:8000'
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['X-Total-Count'],
)


app.include_router(auth_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(certifications_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(galleries_router, prefix="/api/v1")
app.include_router(pictures_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(articles_router, prefix="/api/v1")

@app.get("/")
def main():
    return {"message": "Church Alliance API"}
