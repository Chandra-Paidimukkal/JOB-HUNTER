from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, profile, resumes, jobs, ai, applications,
    outreach, analytics, notifications, email_integration
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(ai.router)
api_router.include_router(applications.router)
api_router.include_router(outreach.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(email_integration.router)
