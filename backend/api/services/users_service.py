from typing import cast

from fastcrud import FastCRUD

from backend.database.models import User
from backend.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

class UsersService:
    """Бизнес-логика работы с пользователями"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_crud = FastCRUD(User)

    async def get_user_by_tg_id(
        self,
        tg_id: int
    ) -> User:
        """Получение пользователя по tg id"""
        
        user = cast( 
            User | None,
            await self.user_crud.get(
                db=self.db, 
                tg_id=tg_id,
                return_as_model=True
            )
        )
    
        if user is None:
            raise NotFoundError("User", tg_id, "Telegram ID")
    
        return user