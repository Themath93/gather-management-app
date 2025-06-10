import asyncio
import random
from db.session import AsyncSessionLocal
from models.user import User, GenderEnum, RoleEnum
from sqlalchemy.ext.asyncio import AsyncSession

# 성과 이름 데이터
KOREAN_LAST_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권"]
MALE_FIRST_NAMES = ["민준", "서준", "도윤", "예준", "시우", "하준", "지후", "준서", "건우", "우진", "현우", "지호", "윤우", "준우", "유준"]
FEMALE_FIRST_NAMES = ["서연", "지우", "서윤", "하은", "지민", "수아", "지아", "지안", "하윤", "윤서", "채원", "예은", "다은", "민서", "소윤"]

INTERESTS_POOL = [
    "독서", "운동", "코딩", "영화", "음악", "요리", "여행", "사진", "등산", "캠핑",
    "드라이브", "게임", "보드게임", "패션", "인테리어", "반려동물", "재테크", "명상", "글쓰기", "블로그",
    "뜨개질", "그림", "영어회화", "스쿠버다이빙", "테니스", "클라이밍"
]

def random_interest():
    return ",".join(random.sample(INTERESTS_POOL, 2))

def random_gender():
    return random.choice([GenderEnum.male, GenderEnum.female])

def generate_unique_name(gender: GenderEnum, existing_names: set) -> str:
    while True:
        last = random.choice(KOREAN_LAST_NAMES)
        first = random.choice(MALE_FIRST_NAMES if gender == GenderEnum.male else FEMALE_FIRST_NAMES)
        name = last + first
        if name not in existing_names:
            existing_names.add(name)
            return name

async def seed_users(db: AsyncSession):
    users = []
    existing_names = set()

    # 모임장
    leader_name = generate_unique_name(GenderEnum.male, existing_names)
    users.append(User(
        username=leader_name,
        email="leader@example.com",
        password="leaderpass",
        role=RoleEnum.leader,
        gender=GenderEnum.male,
        interests=random_interest()
    ))

    # 운영진 8명
    for i in range(8):
        gender = random_gender()
        name = generate_unique_name(gender, existing_names)
        users.append(User(
            username=name,
            email=f"admin{i+1}@example.com",
            password="adminpass",
            role=RoleEnum.admin,
            gender=gender,
            interests=random_interest()
        ))

    # 회원 50명
    for i in range(50):
        gender = random_gender()
        name = generate_unique_name(gender, existing_names)
        users.append(User(
            username=name,
            email=f"user{i+1}@example.com",
            password="userpass",
            role=RoleEnum.member,
            gender=gender,
            interests=random_interest()
        ))

    db.add_all(users)
    await db.commit()
    print("✅ 유저 59명 생성 완료 (중복 없는 이름)")

async def main():
    async with AsyncSessionLocal() as db:
        await seed_users(db)

if __name__ == "__main__":
    asyncio.run(main())