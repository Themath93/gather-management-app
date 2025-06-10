# db/init_db.py
import asyncio
from db.session import engine
from models import user, group, attendance

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(user.Base.metadata.create_all)
        await conn.run_sync(group.Base.metadata.create_all)
        await conn.run_sync(attendance.Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())