# 표준 라이브러리
from datetime import datetime
import random

# 서드파티
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import delete, select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# 로컬 모듈
from db.session import get_db
from models.attendance import Attendance, AttendanceStatus
from models.group import Group, Team, TeamUser, PartEnum
from models.user import User, RoleEnum, GenderEnum

router = APIRouter()

@router.post("/create")
async def create_group(
    date: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")

    result = await db.execute(select(Group).where(Group.date == parsed_date))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 날짜입니다.")

    group = Group(date=parsed_date)
    db.add(group)
    await db.commit()
    return {"message": "모임이 성공적으로 생성되었습니다."}




# @router.get("/list")
# async def list_groups(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Group).order_by(desc(Group.date)))
#     groups = result.scalars().all()
#     return [{"id": g.id, "date": g.date.isoformat()} for g in groups]

@router.get("/list")
async def list_groups(db: AsyncSession = Depends(get_db)):
    groups = (await db.execute(select(Group).order_by(asc(Group.date)))).scalars().all()

    result = []
    for group in groups:
        attendance_rows = (await db.execute(
            select(User.role, Attendance.part)
            .join(Attendance, Attendance.user_id == User.id)
            .where(Attendance.group_id == group.id)
            .where(Attendance.status == AttendanceStatus.attending)
        )).all()

        counts = {
            PartEnum.FIRST.value: {"admin": 0, "member": 0},
            PartEnum.SECOND.value: {"admin": 0, "member": 0},
        }

        for role, part in attendance_rows:
            key = "admin" if role in [RoleEnum.admin, RoleEnum.leader] else "member"
            counts[part.value][key] += 1

        result.append({
            "id": group.id,
            "date": group.date.isoformat(),
            "part_counts": counts,
        })

    return result


@router.get("/{group_id}/my_team")
async def get_my_team(group_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamUser, Team)
        .join(Team, Team.id == TeamUser.team_id)
        .where(Team.group_id == group_id)
        .where(TeamUser.user_id == user_id)
    )
    row = result.first()
    if not row:
        return {"team": None}

    team_user, team = row
    return {
        "team_id": team.id,
        "part": team.part,
        "is_leader": team_user.is_leader
    }


@router.get("/{group_id}/teams")
async def get_group_teams(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Team)
        .options(
            selectinload(Team.members).selectinload(TeamUser.user)
        )
        .where(Team.group_id == group_id)
    )
    teams = result.scalars().all()

    return [
        {
            "team_id": team.id,
            "part": team.part,
            "members": [
                {
                    "username": member.user.username,
                    "is_leader": member.is_leader
                } for member in team.members
            ]
        }
        for team in teams
    ]
    
@router.post("/{group_id}/shuffle")
async def shuffle_teams(
    group_id: int,
    part: str = Form(...),
    team_size: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if team_size <= 0:
        raise HTTPException(status_code=400, detail="조당 인원 수가 올바르지 않습니다.")

    part_map = {
        "1부": PartEnum.FIRST,
        "FIRST": PartEnum.FIRST,
        "first": PartEnum.FIRST,
        "2부": PartEnum.SECOND,
        "SECOND": PartEnum.SECOND,
        "second": PartEnum.SECOND,
    }
    part_enum = part_map.get(part)
    if part_enum is None:
        raise HTTPException(status_code=400, detail="부 정보가 올바르지 않습니다.")

    # 1. 참석자만 가져오기 (선택한 부)
    result = await db.execute(
        select(User)
        .join(Attendance, Attendance.user_id == User.id)
        .where(Attendance.group_id == group_id)
        .where(Attendance.part == part_enum)
        .where(Attendance.status == AttendanceStatus.attending)
    )
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=400, detail="참석한 유저가 없습니다.")

    # 2. 남녀 분리
    males = [u for u in users if u.gender == GenderEnum.male]
    females = [u for u in users if u.gender == GenderEnum.female]

    # 3. 운영진 이상 = 조장 후보
    leaders = [u for u in users if u.role in [RoleEnum.leader, RoleEnum.admin]]

    # 4. 조 수 결정 (입력 값 기반)
    total_count = len(users)
    team_count = max(1, (total_count + team_size - 1) // team_size)

    # 5. 기존 조 제거 (해당 부만)
    team_ids_subq = select(Team.id).where(Team.group_id == group_id, Team.part == part_enum)
    await db.execute(delete(TeamUser).where(TeamUser.team_id.in_(team_ids_subq)))
    await db.execute(delete(Team).where(Team.group_id == group_id, Team.part == part_enum))

    # 6. 팀 목록 준비
    teams = [[] for _ in range(team_count)]

    def balanced_distribute(members, targets):
        random.shuffle(members)
        for i, member in enumerate(members):
            targets[i % len(targets)].append(member)

    balanced_distribute(males, teams)
    balanced_distribute(females, teams)

    team_leaders = []
    for i in range(team_count):
        if i < len(leaders):
            teams[i].insert(0, leaders[i])
            team_leaders.append(leaders[i])
        else:
            random.shuffle(teams[i])
            team_leaders.append(teams[i][0])

    # 7. 저장
    for i, members in enumerate(teams):
        team = Team(group_id=group_id, part=part_enum)
        db.add(team)
        await db.flush()
        for user in members:
            db.add(TeamUser(team_id=team.id, user_id=user.id, is_leader=(user.id == team_leaders[i].id)))

    await db.commit()
    return {"message": "조 편성이 완료되었습니다.", "조 수": team_count, "총원": total_count}


@router.get("/{group_id}/attendee_count")
async def group_attendee_count(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .join(Attendance, Attendance.user_id == User.id)
        .where(Attendance.group_id == group_id)
        .where(Attendance.status == AttendanceStatus.attending)
    )
    attendees = result.scalars().all()

    admin_count = sum(1 for u in attendees if u.role in [RoleEnum.admin, RoleEnum.leader])
    member_count = sum(1 for u in attendees if u.role == RoleEnum.member)
    total = len(attendees)

    return {
        "총참석": total,
        "운영진": admin_count,
        "회원": member_count
    }