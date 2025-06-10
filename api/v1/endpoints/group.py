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
        attendances = (await db.execute(
            select(User.role)
            .join(Attendance, Attendance.user_id == User.id)
            .where(Attendance.group_id == group.id)
            .where(Attendance.status == AttendanceStatus.attending)
        )).scalars().all()

        admin_count = sum(1 for role in attendances if role in [RoleEnum.admin, RoleEnum.leader])
        member_count = sum(1 for role in attendances if role == RoleEnum.member)

        result.append({
            "id": group.id,
            "date": group.date.isoformat(),
            "admin_count": admin_count,
            "member_count": member_count
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
async def shuffle_teams(group_id: int, db: AsyncSession = Depends(get_db)):
    # 1. 참석자만 가져오기
    result = await db.execute(
        select(User)
        .join(Attendance, Attendance.user_id == User.id)
        .where(Attendance.group_id == group_id)
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
    normal_users = [u for u in users if u not in leaders]

    # 4. 조 수 결정 (대략 5~6명 기준)
    total_count = len(users)
    team_count = max(1, total_count // 6)

    # 5. 기존 조 제거
    await db.execute(delete(TeamUser).where(TeamUser.team_id.in_(
        select(Team.id).where(Team.group_id == group_id)
    )))
    await db.execute(delete(Team).where(Team.group_id == group_id))

    # 6. 1부 조 편성
    part1_teams = [[] for _ in range(team_count)]
    part2_teams = [[] for _ in range(team_count)]

    # 남녀 균형 분배
    def balanced_distribute(members, targets):
        random.shuffle(members)
        for i, member in enumerate(members):
            targets[i % len(targets)].append(member)

    balanced_distribute(males, part1_teams)
    balanced_distribute(females, part1_teams)

    # 조장 배정
    part1_leaders = []
    for i in range(team_count):
        if i < len(leaders):
            part1_teams[i].insert(0, leaders[i])
            part1_leaders.append(leaders[i])
        else:
            random.shuffle(part1_teams[i])
            selected = part1_teams[i][0]
            part1_leaders.append(selected)

    # 2부는 같은 조장으로 시작
    for i in range(team_count):
        part2_teams[i].append(part1_leaders[i])

    # 나머지 인원 분배 (조장 제외)
    part1_assigned = set(u.id for team in part1_teams for u in team)
    remaining_users = [u for u in users if u.id not in part1_assigned]

    males2 = [u for u in remaining_users if u.gender == GenderEnum.male]
    females2 = [u for u in remaining_users if u.gender == GenderEnum.female]

    balanced_distribute(males2, part2_teams)
    balanced_distribute(females2, part2_teams)

    # 7. 저장 (1부/2부 모두)
    for part, team_users in [
        (PartEnum.FIRST, part1_teams),
        (PartEnum.SECOND, part2_teams),
    ]:
        for i, members in enumerate(team_users):
            team = Team(group_id=group_id, part=part)
            db.add(team)
            await db.flush()

            for user in members:
                is_leader = (user.id == part1_leaders[i].id)
                db.add(TeamUser(team_id=team.id, user_id=user.id, is_leader=is_leader))

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