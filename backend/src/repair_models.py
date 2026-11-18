from sqlalchemy import String,Float,Boolean,Date,ForeignKey,CheckConstraint,Text
from sqlalchemy.orm import Mapped,mapped_column
from datetime import date
from .database import Base
class RepairBay(Base):
    __tablename__='repair_bays'
    __table_args__=(CheckConstraint('daily_hours > 0 AND daily_hours <= 24'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    daily_hours:Mapped[float]=mapped_column(Float)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
class RepairAppointment(Base):
    __tablename__='repair_appointments'
    __table_args__=(CheckConstraint('hours > 0 AND hours <= 24'),CheckConstraint("state in ('reserved','running','completed')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    claim_id:Mapped[int]=mapped_column(ForeignKey('claims.id'))
    bay_id:Mapped[int]=mapped_column(ForeignKey('repair_bays.id'))
    date:Mapped[date]=mapped_column(Date)
    hours:Mapped[float]=mapped_column(Float)
    state:Mapped[str]=mapped_column(String(20),default='reserved')
    actual_hours:Mapped[float|None]=mapped_column(Float,nullable=True)
    overtime_reason:Mapped[str]=mapped_column(Text,default='')
    completed_by:Mapped[str|None]=mapped_column(String(120),nullable=True)
    created_at:Mapped[str]=mapped_column(String(40))
