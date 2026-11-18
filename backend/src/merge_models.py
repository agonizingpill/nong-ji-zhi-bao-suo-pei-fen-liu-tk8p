from sqlalchemy import String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class MergeGroup(Base):
    __tablename__='merge_groups'
    __table_args__=(CheckConstraint("state in ('open','sealed')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    primary_claim_id:Mapped[int]=mapped_column(ForeignKey('claims.id'),unique=True)
    state:Mapped[str]=mapped_column(String(20),default='open')
    created_by:Mapped[str]=mapped_column(String(120))
    created_at:Mapped[str]=mapped_column(String(40))
    sealed_at:Mapped[str|None]=mapped_column(String(40),nullable=True)
class MergeMember(Base):
    __tablename__='merge_members'
    id:Mapped[int]=mapped_column(primary_key=True)
    group_id:Mapped[int]=mapped_column(ForeignKey('merge_groups.id'))
    claim_id:Mapped[int]=mapped_column(ForeignKey('claims.id'),unique=True)
class MergeLock(Base):
    __tablename__='merge_lock'
    id:Mapped[int]=mapped_column(primary_key=True)
    touched:Mapped[int]=mapped_column(default=0)
