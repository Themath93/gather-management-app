from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from models.base import Base
import enum


class RoleEnum(str, enum.Enum):
    leader = "모임장"
    admin = "운영진"
    member = "회원"

class GenderEnum(str, enum.Enum):
    male = "남"
    female = "여"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    role = Column(Enum(RoleEnum), default=RoleEnum.member)
    gender = Column(Enum(GenderEnum), nullable=False)
    interests = Column(String)
    attendance_count = Column(Integer, default=0)
    last_attended = Column(DateTime)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # 싫어하는 사람
    hate_users = relationship(
        "User",
        secondary="hate_list",
        primaryjoin="User.id==HateList.user_id",
        secondaryjoin="User.id==HateList.hated_user_id",
        backref="hated_by"
    )


class HateList(Base):
    __tablename__ = "hate_list"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    hated_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)