from fastapi import HTTPException
from fastcrud import FastCRUD

from backend.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession

class UsersService:
    """Бизнес-логика работы с пользователями"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_crud = FastCRUD(User)

    async def get_user_by_tg_id(
        self,
        tg_id: int
    ) -> dict:
        """Получение пользователя по tg id"""
        
        user = await self.user_crud.get(db=self.db, tg_id=tg_id)
    
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
        return user