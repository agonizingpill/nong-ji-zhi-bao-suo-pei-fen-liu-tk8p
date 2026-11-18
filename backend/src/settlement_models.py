from decimal import Decimal
from sqlalchemy import String, ForeignKey, Numeric,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class Settlement(Base):
    __tablename__='settlements'
    __table_args__=(CheckConstraint('part_cost >= 0 AND labor_hours >= 0 AND hour_rate >= 0 AND approved_amount >= 0'),CheckConstraint('approved_amount <= calculated_cost'))
    id:Mapped[int]=mapped_column(primary_key=True)
    claim_id:Mapped[int]=mapped_column(ForeignKey('claims.id'),unique=True)
    return_id:Mapped[int]=mapped_column(ForeignKey('part_returns.id'))
    part_cost:Mapped[Decimal]=mapped_column(Numeric(12,2))
    labor_hours:Mapped[Decimal]=mapped_column(Numeric(8,2))
    hour_rate:Mapped[Decimal]=mapped_column(Numeric(10,2))
    calculated_cost:Mapped[Decimal]=mapped_column(Numeric(12,2))
    approved_amount:Mapped[Decimal]=mapped_column(Numeric(12,2),default=0)
    state:Mapped[str]=mapped_column(String(20),default='draft')
    approved_by:Mapped[str]=mapped_column(String(120),default='')
    ledger_reference:Mapped[str|None]=mapped_column(String(80),unique=True,nullable=True)
    booked_at:Mapped[str|None]=mapped_column(String(40),nullable=True)
