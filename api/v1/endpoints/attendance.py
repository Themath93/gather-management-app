from sqlalchemy import func, select
from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from models.attendance import Attendance, AttendanceStatus
from models.group import PartEnum
from models.user import User
from models.group import Group

router = APIRouter()


@router.post("/set")
async def set_attendance(
    group_id: int = Form(...),
    user_id: int = Form(...),
    part: PartEnum = Form(...),
    status: AttendanceStatus = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # 기존 출석 기록 조회
    stmt = select(Attendance).where(
        Attendance.group_id == group_id,
        Attendance.user_id == user_id,
        Attendance.part == part
    )
    result = await db.execute(stmt)
    record = result.scalars().first()

    # 유저와 모임 정보
    user = await db.get(User, user_id)
    group = await db.get(Group, group_id)
    if not user or not group:
        raise HTTPException(status_code=404, detail="유저 또는 모임을 찾을 수 없습니다.")

    # 출석 상태 변경 로직
    if record:
        previous_status = record.status
        record.status = status

        if previous_status != status:
            # 참석 ➡ 불참
            if previous_status == AttendanceStatus.attending and status == AttendanceStatus.absent:
                user.attendance_count = max(0, (user.attendance_count or 1) - 1)

                # 최신 참석일 재계산
                subq = (
                    select(func.max(Group.date))
                    .join(Attendance, Attendance.group_id == Group.id)
                    .where(
                        Attendance.user_id == user_id,
                        Attendance.status == AttendanceStatus.attending
                    )
                )
                result = await db.execute(subq)
                user.last_attended = result.scalar_one_or_none()

            # 불참 ➡ 참석
            elif previous_status == AttendanceStatus.absent and status == AttendanceStatus.attending:
                user.attendance_count = (user.attendance_count or 0) + 1
                if not user.last_attended or group.date > user.last_attended:
                    user.last_attended = group.date

    else:
        # 신규 등록
        record = Attendance(
            group_id=group_id,
            user_id=user_id,
            part=part,
            status=status
        )
        db.add(record)

        if status == AttendanceStatus.attending:
            user.attendance_count = (user.attendance_count or 0) + 1
            if not user.last_attended or group.date > user.last_attended:
                user.last_attended = group.date

    await db.commit()
    return {"message": "출석 상태가 저장되었습니다."}


@router.get("/get")
async def get_attendance(
    group_id: int = Query(...),
    user_id: int = Query(...),
    part: PartEnum = Query(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Attendance).where(
            Attendance.group_id == group_id,
            Attendance.user_id == user_id,
            Attendance.part == part
        )
    )
    record = result.scalars().first()
    return {"status": record.status if record else None}