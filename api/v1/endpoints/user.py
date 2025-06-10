from sqlalchemy import func, select
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from models.user import User, RoleEnum, GenderEnum
from models.group import Group
from models.attendance import Attendance
from sqlalchemy.future import select

router = APIRouter()

@router.post("/register_user")
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    role: RoleEnum = Form(...),
    gender: GenderEnum = Form(...),
    interests: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")

    new_user = User(
        username=username,
        password=password,
        email=email,
        role=role,
        gender=gender,
        interests=interests
    )
    db.add(new_user)
    await db.commit()
    return {"message": "유저가 성공적으로 추가되었습니다."}

@router.get("/get_users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        User.__table__.select()
    )
    return result.mappings().all()




@router.get("/get_users_detail")
async def get_users_detail(db: AsyncSession = Depends(get_db)):
    attendance_subquery = (
        select(
            Attendance.user_id,
            func.count().label("total_attendance"),
            func.max(Group.date).label("last_attended_date"),
        )
        .join(Group, Group.id == Attendance.group_id)
        .group_by(Attendance.user_id)
        .subquery()
    )

    stmt = (
        select(
            User.id,
            User.username,
            User.gender,
            User.email,
            User.role,
            User.interests,
            User.created_at,
            func.coalesce(attendance_subquery.c.total_attendance, 0).label("attendance_count"),
            attendance_subquery.c.last_attended_date,
        )
        .outerjoin(attendance_subquery, User.id == attendance_subquery.c.user_id)
        .order_by(User.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.mappings().all()


@router.post("/update_user")
async def update_user(
    user_id: int = Form(...),
    email: str = Form(...),
    gender: GenderEnum = Form(...),
    interests: str = Form(""),
    role: RoleEnum = Form(None),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    user.email = email
    user.gender = gender
    user.interests = interests

    if role is not None:
        user.role = role  # 모임장만 허용하도록 추후 인증체크 가능

    await db.commit()
    return {"message": "유저가 성공적으로 수정되었습니다."}