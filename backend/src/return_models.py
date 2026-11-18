from sqlalchemy import String, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class PartReturn(Base):
    __tablename__='part_returns'
    __table_args__=(CheckConstraint("state in ('dispatched','received','verified')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    claim_id:Mapped[int]=mapped_column(ForeignKey('claims.id'),unique=True)
    tracking_code:Mapped[str]=mapped_column(String(80),unique=True)
    expected_serial:Mapped[str]=mapped_column(String(60))
    received_serial:Mapped[str]=mapped_column(String(60),default='')
    condition:Mapped[str]=mapped_column(Text,default='')
    state:Mapped[str]=mapped_column(String(20),default='dispatched')
    verified_by:Mapped[str]=mapped_column(String(120),default='')
