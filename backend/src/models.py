from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(120),unique=True)
    password:Mapped[str]=mapped_column(String(256))
    role:Mapped[str]=mapped_column(String(20))
class Machine(Base):
    __tablename__='machines'
    __table_args__=(CheckConstraint('hours >= 0 AND warranty_hours > 0'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    serial:Mapped[str]=mapped_column(String(60),unique=True)
    model:Mapped[str]=mapped_column(String(60))
    purchase_date:Mapped[str]=mapped_column(String(10))
    warranty_hours:Mapped[int]=mapped_column(default=2000)
    hours:Mapped[int]=mapped_column(default=0)
class Claim(Base):
    __tablename__='claims'
    __table_args__=(CheckConstraint('hours_at_failure >= 0 AND age_days >= 0'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(60),unique=True)
    machine_id:Mapped[int]=mapped_column(ForeignKey('machines.id'))
    part:Mapped[str]=mapped_column(String(40))
    hours_at_failure:Mapped[int]
    age_days:Mapped[int]
    leak_flag:Mapped[bool]=mapped_column(Boolean)
    risk:Mapped[float|None]=mapped_column(Float,nullable=True)
    status:Mapped[str]=mapped_column(String(30),default='submitted')
    historical:Mapped[bool]=mapped_column(Boolean,default=False)
    disputed:Mapped[int|None]=mapped_column(Integer,nullable=True)
    assessment_note:Mapped[str]=mapped_column(Text,default='')
class Inspection(Base):
    __tablename__='inspections'
    id:Mapped[int]=mapped_column(primary_key=True)
    claim_id:Mapped[int]=mapped_column(ForeignKey('claims.id'),unique=True)
    findings:Mapped[str]=mapped_column(Text)
    evidence_complete:Mapped[bool]=mapped_column(Boolean,default=False)
    decision:Mapped[str]=mapped_column(String(30),default='pending')
class Audit(Base):
    __tablename__='audit'
    id:Mapped[int]=mapped_column(primary_key=True)
    actor:Mapped[str]=mapped_column(String(120))
    action:Mapped[str]=mapped_column(String(100))
    detail:Mapped[str]=mapped_column(Text)
    at:Mapped[str]=mapped_column(String(40))
