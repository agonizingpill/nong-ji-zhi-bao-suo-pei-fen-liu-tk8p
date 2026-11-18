from fastapi import HTTPException
from sqlalchemy import select
from .models import Claim,Machine,Inspection
from .return_models import PartReturn
from .merge_models import MergeGroup,MergeMember
from .claim_service import get,audit

def return_view(s,x):
    claim=s.get(Claim,x.claim_id)
    return {c.name:getattr(x,c.name)for c in x.__table__.columns}|{'claim_code':claim.code}
def dispatch(s,d,u):
    c=s.scalar(select(Claim).where(Claim.id==d.claim_id).with_for_update())
    if not c:raise HTTPException(404,'索赔不存在')
    if c.historical or c.status not in ['assessed','paid','denied']:raise HTTPException(409,'仅已分流且非历史索赔可登记返厂')
    mm=s.scalar(select(MergeMember).where(MergeMember.claim_id==c.id))
    if mm and s.get(MergeGroup,mm.group_id).primary_claim_id!=c.id:raise HTTPException(409,'归并成员的旧件随主单流转，不可独立发件返厂')
    if not s.scalar(select(Inspection.id).where(Inspection.claim_id==c.id)):raise HTTPException(409,'请先保存拆检意见，再安排旧件返厂')
    if s.scalar(select(PartReturn.id).where(PartReturn.claim_id==c.id)):raise HTTPException(409,'该索赔已有返厂单，不得重复发件')
    m=s.get(Machine,c.machine_id)
    x=PartReturn(claim_id=c.id,tracking_code=d.tracking_code,expected_serial=m.serial,state='dispatched',condition='',received_serial='',verified_by='');s.add(x);s.flush();audit(s,u,'part_dispatched',f'{c.code}:{d.tracking_code}');return return_view(s,x)
def receive(s,x,d,u):
    if x.state!='dispatched':raise HTTPException(409,'只有已发出的旧件可以收货，收货证据不能覆盖')
    if d.received_serial!=x.expected_serial:raise HTTPException(409,'实收机具序列号与发件快照不符，拒绝收货')
    x.received_serial=d.received_serial;x.condition=d.condition;x.state='received';audit(s,u,'part_received',x.tracking_code);return return_view(s,x)
def verify(s,x,u):
    if x.state!='received':raise HTTPException(409,'请先收货，核验完成的旧件不可重复签验')
    if x.received_serial!=x.expected_serial or len(x.condition.strip())<8:raise HTTPException(409,'序列及旧件状况证据不完整')
    x.state='verified';x.verified_by=u['email'];audit(s,u,'part_verified',x.tracking_code);return return_view(s,x)
