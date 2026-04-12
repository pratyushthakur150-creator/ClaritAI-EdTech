from fastapi import APIRouter
from . import (
    auth, leads, calls, demos, enrollments, analytics,
    teaching, context, attribution,
    chatbot, confusion, nudges, risk, heatmap,
    voice, assistant, content,
    teaching_assistant,
    usage, workflows, test_minimal,
    dashboard, students, courses,
)

# Verify routers loaded correctly
print(f"✓ Usage router loaded with {len(usage.router.routes)} routes")
print(f"✓ Workflows router loaded with {len(workflows.router.routes)} routes")

api_router = APIRouter()

# Existing routers
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(leads.router, tags=["Leads"])
api_router.include_router(calls.router, tags=["Calls"])
api_router.include_router(demos.router, tags=["Demos"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(teaching.router, prefix="/teaching", tags=["Teaching"])
api_router.include_router(context.router, prefix="/context", tags=["Context"])
api_router.include_router(attribution.router, prefix="/attribution", tags=["Attribution"])

# NEW: Teaching Assistant Module Routers
api_router.include_router(chatbot.router, tags=["Chatbot"])
api_router.include_router(confusion.router, tags=["Confusion Tracking"])
api_router.include_router(nudges.router, tags=["Nudges"])
api_router.include_router(risk.router, tags=["Risk Scoring"])
api_router.include_router(heatmap.router, tags=["Heatmap"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"])
api_router.include_router(content.router, prefix="/content", tags=["Content Indexing"])
api_router.include_router(teaching_assistant.router, tags=["Teaching Assistant"])

# NEW: Dashboard & Students
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(students.router, tags=["Students"])
api_router.include_router(courses.router, tags=["Courses"])

# NEW: Usage & Workflows
api_router.include_router(usage.router, prefix="/usage", tags=["Usage"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

# Test minimal router
api_router.include_router(test_minimal.router, prefix="/test", tags=["Test"])