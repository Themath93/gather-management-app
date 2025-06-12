# db/init_db.py
import asyncio
from db.session import engine
from models import user, group, attendance

async def init_db(reset: bool = False):
    """Initialise the database.

    Parameters
    ----------
    reset: bool
        Drop existing tables before creating them again.  Useful when the
        schema has changed and the SQLite file still exists.
    """

    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(attendance.Base.metadata.drop_all)
            await conn.run_sync(group.Base.metadata.drop_all)
            await conn.run_sync(user.Base.metadata.drop_all)
        await conn.run_sync(user.Base.metadata.create_all)
        await conn.run_sync(group.Base.metadata.create_all)
        await conn.run_sync(attendance.Base.metadata.create_all)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialise the database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables before creating them",
    )
    args = parser.parse_args()

    asyncio.run(init_db(reset=args.reset))
