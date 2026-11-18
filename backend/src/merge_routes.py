from fastapi import APIRouter,Depends
from sqlalchemy import select
from .database import Session
from .security import current,allow
from .merge_models import MergeGroup
from .merge_schemas import MergeIn
from . import merge_service as mg
router=APIRouter()
@router.get('/merge-groups')
def groups(u=Depends(current)):
    with Session() as s:return [mg.view(s,g) for g in s.scalars(select(MergeGroup).order_by(MergeGroup.id.desc()))]
@router.post('/merge-groups')
def create(d:MergeIn,u=Depends(current)):
    allow(u,'admin')
    with Session.begin() as s:return mg.merge(s,d,u)
