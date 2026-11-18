from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from .database import Session
from .security import current,allow
from .repair_models import RepairBay,RepairAppointment
from .spare_models import SpareStock,PartIssue
from .followup_models import RepairFollowup
from .workshop_schemas import BayIn,AppointmentIn,FinishIn,StockIn,IssueIn,FollowupIn,ReworkIn
from .claim_service import obj,audit
from . import repair_service as repair,spare_service as spare,followup_service as followup
router=APIRouter()
@router.get('/repair-bays')
def bays(u=Depends(current)):
    with Session() as s:return [obj(x) for x in s.scalars(select(RepairBay).order_by(RepairBay.id))]
@router.post('/repair-bays')
def bay(d:BayIn,u=Depends(current)):
    allow(u,'admin')
    with Session.begin() as s:
        x=RepairBay(**d.model_dump());s.add(x);s.flush();audit(s,u,'repair_bay_created',x.code);return obj(x)
@router.put('/repair-bays/{id}')
def edit_bay(id:int,d:BayIn,u=Depends(current)):
    allow(u,'admin')
    with Session.begin() as s:
        x=repair.locked(s,RepairBay,id)
        if d.code!=x.code:raise HTTPException(409,'工位编号不可改')
        rows=s.scalars(select(RepairAppointment).where(RepairAppointment.bay_id==id).with_for_update()).all();used={}
        for a in rows:used[a.date]=used.get(a.date,0)+a.hours
        if any(h>d.daily_hours for h in used.values()):raise HTTPException(409,'新日容量不能小于已有预约占用')
        x.daily_hours=d.daily_hours;x.active=d.active;audit(s,u,'repair_bay_updated',x.code);return obj(x)
@router.get('/repair-appointments')
def appointments(u=Depends(current)):
    with Session() as s:return [repair.view(s,x) for x in s.scalars(select(RepairAppointment).order_by(RepairAppointment.id.desc()))]
@router.post('/repair-appointments')
def reserve(d:AppointmentIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return repair.reserve(s,d,u)
@router.post('/repair-appointments/{id}/start')
def start(id:int,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return repair.start(s,id,u)
@router.post('/repair-appointments/{id}/complete')
def finish(id:int,d:FinishIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return repair.finish(s,id,d,u)
@router.get('/spare-stocks')
def stocks(u=Depends(current)):
    with Session() as s:return [obj(x) for x in s.scalars(select(SpareStock).order_by(SpareStock.id))]
@router.post('/spare-stocks')
def stock(d:StockIn,u=Depends(current)):
    allow(u,'admin')
    with Session.begin() as s:
        x=SpareStock(**d.model_dump());s.add(x);s.flush();audit(s,u,'stock_registered',x.code);return obj(x)
@router.get('/part-issues')
def issues(u=Depends(current)):
    with Session() as s:return [spare.view(s,x) for x in s.scalars(select(PartIssue).order_by(PartIssue.id.desc()))]
@router.post('/part-issues')
def issue(d:IssueIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return spare.issue(s,d,u)
@router.post('/part-issues/{id}/return')
def give_back(id:int,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return spare.give_back(s,id,u)
@router.get('/repair-followups')
def followups(u=Depends(current)):
    with Session() as s:return [followup.view(s,x) for x in s.scalars(select(RepairFollowup).order_by(RepairFollowup.id.desc()))]
@router.post('/repair-followups')
def add_followup(d:FollowupIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return followup.create(s,d,u)
@router.post('/repair-followups/{id}/rework')
def link(id:int,d:ReworkIn,u=Depends(current)):
    allow(u,'admin','assessor')
    with Session.begin() as s:return followup.link(s,id,d,u)
@router.post('/repair-followups/{id}/close')
def close(id:int,u=Depends(current)):
    allow(u,'admin')
    with Session.begin() as s:return followup.close(s,id,u)
