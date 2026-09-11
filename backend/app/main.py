from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings, assert_production_safe
from app.core.rate_limit import limiter
from app.routers import auth, students, gap, assessments, opportunities, college, admin, profile_extras, ai as ai_router, community, pulse, academician

assert_production_safe()

app = FastAPI(title=settings.APP_NAME)
app.state.limiter = limiter

# Exception Handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(profile_extras.router)
app.include_router(gap.router)
app.include_router(assessments.router)
app.include_router(opportunities.router)
app.include_router(college.router)
app.include_router(admin.router)
app.include_router(ai_router.router)
app.include_router(community.router)
app.include_router(pulse.router)
app.include_router(academician.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}