import asyncio
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from models.user import User, RoleEnum
from models.group import Group, PartEnum
from models.attendance import Attendance, AttendanceStatus

async def seed_attendance(group_id: int, admin_count: int, member_count: int, db: AsyncSession) -> None:
    group = await db.get(Group, group_id)
    if not group:
        print(f"Group {group_id} not found")
        return

    admin_users = (
        await db.execute(
            select(User).where(User.role.in_([RoleEnum.leader, RoleEnum.admin]))
        )
    ).scalars().all()
    member_users = (
        await db.execute(select(User).where(User.role == RoleEnum.member))
    ).scalars().all()

    selected_admins = random.sample(admin_users, min(admin_count, len(admin_users)))
    selected_members = random.sample(member_users, min(member_count, len(member_users)))

    selected = selected_admins + selected_members

    for user in selected:
        part = random.choice([PartEnum.FIRST, PartEnum.SECOND])
        attendance = Attendance(
            group_id=group_id,
            user_id=user.id,
            part=part,
            status=AttendanceStatus.attending,
        )
        db.add(attendance)
        user.attendance_count = (user.attendance_count or 0) + 1
        if not user.last_attended or group.date > user.last_attended.date():
            user.last_attended = group.date

    await db.commit()
    print(
        f"✅ Attendance set: {len(selected_admins)} admins, {len(selected_members)} members for group {group_id}"
    )

async def main():
    async with AsyncSessionLocal() as db:
        await seed_attendance(group_id=1, admin_count=5, member_count=40, db=db)

if __name__ == "__main__":
    asyncio.run(main())
