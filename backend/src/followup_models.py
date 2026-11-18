from sqlalchemy import String,Float,Boolean,ForeignKey,JSON,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class RepairFollowup(Base):
    __tablename__='repair_followups'
    __table_args__=(CheckConstraint('run_hours > 0'),CheckConstraint("state in ('review','rework','closed')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    appointment_id:Mapped[int]=mapped_column(ForeignKey('repair_appointments.id'),unique=True)
    run_hours:Mapped[float]=mapped_column(Float)
    leak_found:Mapped[bool]=mapped_column(Boolean)
    noise:Mapped[bool]=mapped_column(Boolean)
    state:Mapped[str]=mapped_column(String(20))
    rework_appointment_id:Mapped[int|None]=mapped_column(ForeignKey('repair_appointments.id'),nullable=True)
    settlement_snapshot:Mapped[list]=mapped_column(JSON)
    created_at:Mapped[str]=mapped_column(String(40))
    closed_by:Mapped[str|None]=mapped_column(String(120),nullable=True)
