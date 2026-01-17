from backend.database.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:  
    async with AsyncSessionLocal() as db: 
        try:
            yield db
        finally:
            await db.close() 