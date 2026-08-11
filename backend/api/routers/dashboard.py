from fastapi import APIRouter

from backend.api.services.dashboard_service import DashboardService
from backend.api.deps import DbDep

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: DbDep):
    """Получение статистики для дашборда"""
    return await DashboardService(db).get_dashboard_stats()