from sqlalchemy import select
from fastapi import HTTPException
from .followup_models import RepairFollowup
from .repair_models import RepairAppointment
from .settlement_models import Settlement
from .settlements_service import view as settlement_view
from .repair_service import appointment,locked,now
from .claim_service import audit
from .models import Claim

def view(s,x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}|{'claim_code':s.get(Claim,s.get(RepairAppointment,x.appointment_id).claim_id).code}
def create(s,d,u):
    a=appointment(s,d.appointment_id)
    if a.state!='completed':raise HTTPException(409,'只有完工预约可以录返修质量回访')
    if s.scalar(select(RepairFollowup.id).where(RepairFollowup.appointment_id==a.id).with_for_update()):raise HTTPException(409,'此预约已有回访，不可重复')
    x=RepairFollowup(**d.model_dump(),state='rework' if d.leak_found or d.noise else 'review',created_at=now(),settlement_snapshot=[settlement_view(s,z) for z in s.scalars(select(Settlement).where(Settlement.claim_id==a.claim_id))]);s.add(x);s.flush();audit(s,u,'repair_followup',f'{a.id}:{x.state}');return view(s,x)
def context(s,id):
    pre=s.get(RepairFollowup,id)
    if not pre:raise HTTPException(404,'回访不存在')
    a=appointment(s,pre.appointment_id);return locked(s,RepairFollowup,id),a
def link(s,id,d,u):
    x,a=context(s,id)
    if x.state!='rework' or x.rework_appointment_id:raise HTTPException(409,'仅未关联的异常回访可指定返工预约')
    b=locked(s,RepairAppointment,d.appointment_id)
    if b.claim_id!=a.claim_id or b.id==a.id or b.created_at<x.created_at:raise HTTPException(409,'须关联回访后新建、同一索赔的返工预约')
    x.rework_appointment_id=b.id;audit(s,u,'followup_rework_linked',f'{id}:{b.id}');return view(s,x)
def close(s,id,u):
    x,a=context(s,id)
    if x.state=='closed':raise HTTPException(409,'回访已关闭，不能重复签署')
    if x.state=='rework':
        if not x.rework_appointment_id:raise HTTPException(409,'异常回访须先关联新的返工预约')
        b=locked(s,RepairAppointment,x.rework_appointment_id)
        if b.claim_id!=a.claim_id or b.state!='completed' or b.created_at<x.created_at:raise HTTPException(409,'同索赔的新返工预约尚未完工')
    x.state='closed';x.closed_by=u['email'];audit(s,u,'followup_closed',str(id));return view(s,x)
