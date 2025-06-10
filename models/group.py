from sqlalchemy import Column, Integer, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from models.base import Base
from models.user import User

class PartEnum(str, enum.Enum):
    FIRST = "first"   # or "1"
    SECOND = "second" # or "2"

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)  # 같은 날짜에 여러 조 존재 가능
    teams = relationship("Team", back_populates="group", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    part = Column(Enum(PartEnum), nullable=False)  # 1부 / 2부
    group = relationship("Group", back_populates="teams")
    members = relationship("TeamUser", back_populates="team", cascade="all, delete-orphan")

class TeamUser(Base):
    __tablename__ = "team_users"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_leader = Column(Boolean, default=False)

    team = relationship("Team", back_populates="members")
    user = relationship("User")