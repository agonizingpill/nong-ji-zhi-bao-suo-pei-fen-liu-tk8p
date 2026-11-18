from sqlalchemy import String,Integer,ForeignKey,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class SpareStock(Base):
    __tablename__='spare_stocks'
    __table_args__=(CheckConstraint('available_qty >= 0'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    part:Mapped[str]=mapped_column(String(40))
    available_qty:Mapped[int]=mapped_column(Integer)
class PartIssue(Base):
    __tablename__='part_issues'
    __table_args__=(CheckConstraint('qty > 0'),CheckConstraint("state in ('issued','returned','consumed')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    appointment_id:Mapped[int]=mapped_column(ForeignKey('repair_appointments.id'))
    stock_id:Mapped[int]=mapped_column(ForeignKey('spare_stocks.id'))
    qty:Mapped[int]=mapped_column(Integer)
    state:Mapped[str]=mapped_column(String(20),default='issued')
