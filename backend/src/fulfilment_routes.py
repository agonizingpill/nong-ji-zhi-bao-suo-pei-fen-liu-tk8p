from fastapi import APIRouter,Depends
from sqlalchemy import select
from .database import Session
from .security import current,allow
from .claim_service import get
from .return_models import PartReturn
from .settlement_models import Settlement
from .fulfilment_schemas import ReturnIn,ReceiveIn,SettlementIn,ApprovalIn,BookingIn
from . import returns_service as returns,settlements_service as payments
router=APIRouter()
def locked(s,cls,id):
    from fastapi import HTTPException
    x=s.scalar(select(cls).where(cls.id==id).with_for_update())
    if not x:raise HTTPException(404,'返厂或结算记录不存在')
    return x
@router.get('/part-returns')
def list_returns(u=Depends(current)):
    with Session()as s:return [returns.return_view(s,x)for x in s.scalars(select(PartReturn).order_by(PartReturn.id.desc()))]
@router.post('/part-returns')
def dispatch(d:ReturnIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin()as s:return returns.dispatch(s,d,u)
@router.post('/part-returns/{id}/receive')
def receive(id:int,d:ReceiveIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin()as s:return returns.receive(s,locked(s,PartReturn,id),d,u)
@router.post('/part-returns/{id}/verify')
def verify(id:int,u=Depends(current)):
    allow(u,'admin')
    with Session.begin()as s:return returns.verify(s,locked(s,PartReturn,id),u)
@router.get('/settlements')
def list_settlements(u=Depends(current)):
    with Session()as s:return [payments.view(s,x)for x in s.scalars(select(Settlement).order_by(Settlement.id.desc()))]
@router.post('/settlements')
def create(d:SettlementIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin()as s:return payments.create(s,d,u)
@router.post('/settlements/{id}/approve')
def approve(id:int,d:ApprovalIn,u=Depends(current)):
    allow(u,'admin')
    with Session.begin()as s:return payments.approve(s,locked(s,Settlement,id),d,u)
@router.post('/settlements/{id}/book')
def book(id:int,d:BookingIn,u=Depends(current)):
    allow(u,'admin')
    with Session.begin()as s:return payments.book(s,locked(s,Settlement,id),d,u)
