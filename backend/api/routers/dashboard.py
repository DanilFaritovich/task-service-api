from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import and_, func, select

from backend.api.deps import DbDep
from backend.database.models import Log, Service, Task, User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: DbDep):
    """Получение статистики для дашборда"""

    # Количество пользователей
    users_count = (
        await db.execute(select(func.count()).select_from(User))
    ).scalar() or 0

    # Количество задач по статусам
    tasks_by_status = {}
    for status in ["pending", "running", "completed", "failed", "cancelled"]:
        count = (
            await db.execute(
                select(func.count()).select_from(Task).where(Task.status == status)
            )
        ).scalar() or 0
        tasks_by_status[status] = count

    # Последние логи
    recent_logs = (
        (await db.execute(select(Log).order_by(Log.timestamp.desc()).limit(10)))
        .scalars()
        .all()
    )

    # Статистика по сервисам
    services_count = (
        await db.execute(select(func.count()).select_from(Service))
    ).scalar() or 0
    active_services = (
        await db.execute(
            select(func.count())
            .select_from(Service)
            .where(and_(Service.is_active, ~Service.is_blocked))
        )
    ).scalar() or 0

    return {
        "total_users": users_count,
        "total_services": services_count,
        "active_services": active_services,
        "tasks_by_status": tasks_by_status,
        "total_tasks": sum(tasks_by_status.values()),
        "recent_logs": [
            {
                "id": log.id,
                "level": log.level,
                "message": log.message[:100] + "..."
                if len(log.message) > 100
                else log.message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in recent_logs
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
