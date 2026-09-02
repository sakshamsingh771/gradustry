from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401 - ensures all models are registered on Base
from app.routers import auth, students, gap, assessments, opportunities, college, admin, ai as ai_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # For the hackathon MVP we auto-create tables; use Alembic migrations
    # (see /alembic) for anything beyond local/demo use.
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(students.router)
app.include_router(gap.router)
app.include_router(assessments.router)
app.include_router(opportunities.router)
app.include_router(college.router)
app.include_router(admin.router)
app.include_router(ai_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
