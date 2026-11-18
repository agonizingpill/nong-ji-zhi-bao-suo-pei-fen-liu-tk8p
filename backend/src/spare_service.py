from sqlalchemy import select
from fastapi import HTTPException
from .spare_models import SpareStock,PartIssue
from .repair_models import RepairAppointment
from .models import Claim
from .repair_service import appointment,locked
from .claim_service import audit

def view(s,x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}|{'stock_code':s.get(SpareStock,x.stock_id).code,'claim_code':s.get(Claim,s.get(RepairAppointment,x.appointment_id).claim_id).code}
def issue(s,d,u):
    x=appointment(s,d.appointment_id);stock=locked(s,SpareStock,d.stock_id)
    if x.state!='reserved':raise HTTPException(409,'仅未开工预约可以领料')
    if stock.part!=s.get(Claim,x.claim_id).part:raise HTTPException(409,'备件部位与索赔部位不匹配')
    if s.scalar(select(PartIssue.id).where(PartIssue.appointment_id==x.id,PartIssue.state.in_(['issued','consumed'])).with_for_update()):raise HTTPException(409,'本预约已有有效领料，不可重复扣库')
    if stock.available_qty<d.qty:raise HTTPException(409,'备件可用库存不足')
    stock.available_qty-=d.qty;r=PartIssue(**d.model_dump());s.add(r);s.flush();audit(s,u,'parts_issued',f'{x.id}:{stock.code}:{d.qty}');return view(s,r)
def give_back(s,id,u):
    preview=s.get(PartIssue,id)
    if not preview:raise HTTPException(404,'领料记录不存在')
    x=appointment(s,preview.appointment_id);stock=locked(s,SpareStock,preview.stock_id);r=locked(s,PartIssue,id)
    if x.state!='reserved' or r.state!='issued':raise HTTPException(409,'只允许未开工且未退回的备件退料一次')
    stock.available_qty+=r.qty;r.state='returned';audit(s,u,'parts_returned',f'{id}:{r.qty}');return view(s,r)
