from datetime import datetime,timezone,date
from sqlalchemy import select
from fastapi import HTTPException
from .models import Claim
from .repair_models import RepairBay,RepairAppointment
from .spare_models import PartIssue
from .claim_service import audit

def now():return datetime.now(timezone.utc).isoformat()
def locked(s,cls,id):
    x=s.scalar(select(cls).where(cls.id==id).with_for_update().execution_options(populate_existing=True))
    if not x:raise HTTPException(404,'索赔、工位或维修记录不存在')
    return x
def view(s,x):
    data={c.name:getattr(x,c.name).isoformat() if isinstance(getattr(x,c.name),date) else getattr(x,c.name) for c in x.__table__.columns}
    return data|{'claim_code':s.get(Claim,x.claim_id).code,'part':s.get(Claim,x.claim_id).part,'bay_code':s.get(RepairBay,x.bay_id).code}
def claim(s,id):
    c=locked(s,Claim,id)
    if c.historical or c.status!='paid':raise HTTPException(409,'只有已赔付的现场索赔可安排维修')
    return c
def reserve(s,d,u):
    c=claim(s,d.claim_id);bay=locked(s,RepairBay,d.bay_id)
    if not bay.active:raise HTTPException(409,'工位已停用')
    if s.scalar(select(RepairAppointment.id).where(RepairAppointment.claim_id==c.id,RepairAppointment.state.in_(['reserved','running'])).with_for_update()):raise HTTPException(409,'该索赔已有活跃预约，不能重复占位')
    rows=s.scalars(select(RepairAppointment).where(RepairAppointment.bay_id==bay.id,RepairAppointment.date==d.date).with_for_update()).all()
    if sum(x.hours for x in rows)+d.hours>bay.daily_hours+1e-8:raise HTTPException(409,'该工位当日剩余容量不足')
    x=RepairAppointment(**d.model_dump(),created_at=now());s.add(x);s.flush();audit(s,u,'repair_reserved',f'{c.code}:{bay.code}:{d.date}:{d.hours}h');return view(s,x)
def appointment(s,id):
    preview=s.get(RepairAppointment,id)
    if not preview:raise HTTPException(404,'预约不存在')
    claim(s,preview.claim_id);return locked(s,RepairAppointment,id)
def start(s,id,u):
    x=appointment(s,id)
    if x.state!='reserved':raise HTTPException(409,'仅待开工预约可开工，不能重复')
    issue=s.scalar(select(PartIssue).where(PartIssue.appointment_id==x.id,PartIssue.state=='issued').with_for_update())
    if not issue:raise HTTPException(409,'开工前须领用与索赔部位匹配的备件')
    issue.state='consumed';x.state='running';audit(s,u,'repair_started',str(id));return view(s,x)
def finish(s,id,d,u):
    x=appointment(s,id)
    if x.state!='running':raise HTTPException(409,'只有已开工预约可完工')
    if d.actual_hours>x.hours and (u['role']!='admin' or len(d.overtime_reason.strip())<8):raise HTTPException(409,'超预约实耗须主管填写至少8字超时原因后签署')
    x.actual_hours=d.actual_hours;x.overtime_reason=d.overtime_reason.strip();x.completed_by=u['email'];x.state='completed';audit(s,u,'repair_completed',f'{id}:{d.actual_hours}h');return view(s,x)
