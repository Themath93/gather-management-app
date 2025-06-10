from sqlalchemy import Column, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from models.base import Base
from models.group import PartEnum  # ✅ 1부/2부를 위한 열거형 불러오기
import enum


class AttendanceStatus(str, enum.Enum):
    attending = "참석"
    absent = "불참"


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    part = Column(Enum(PartEnum), nullable=False)  # ✅ 1부/2부 구분 필드 추가
    status = Column(Enum(AttendanceStatus), nullable=False)

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", "part", name="_group_user_part_uc"),  # ✅ 동일 모임-유저-부 중복 방지
    )

    user = relationship("User")
    group = relationship("Group")