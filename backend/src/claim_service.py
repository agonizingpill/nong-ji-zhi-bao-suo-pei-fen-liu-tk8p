from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from .models import Machine,Claim,Inspection,Audit
from .merge_models import MergeGroup

def obj(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def get(s,model,id):
    x=s.get(model,id)
    if not x:raise HTTPException(404,'记录不存在')
    return x
def audit(s,u,action,detail):s.add(Audit(actor=u['email'],action=action,detail=str(detail),at=datetime.now(timezone.utc).isoformat()))
def claim_view(s,c):
    d=obj(c);d['machine_serial']=s.get(Machine,c.machine_id).serial
    i=s.scalar(select(Inspection).where(Inspection.claim_id==c.id));d['inspection']=obj(i) if i else None
    return d
def submit(s,data,u):
    m=get(s,Machine,data.machine_id)
    if data.hours_at_failure<m.hours:raise HTTPException(409,'故障工时不能小于机具最新台账工时')
    c=Claim(**data.model_dump(),historical=False,status='out_of_warranty' if data.hours_at_failure>m.warranty_hours else 'submitted',assessment_note='超出质保工时' if data.hours_at_failure>m.warranty_hours else '')
    m.hours=data.hours_at_failure;s.add(c);s.flush();audit(s,u,'claim_received',c.code);return claim_view(s,c)
def inspect(s,c,data,u):
    c=s.scalar(select(Claim).where(Claim.id==c.id).with_for_update().execution_options(populate_existing=True))
    if c.status!='assessed':raise HTTPException(409,'仅完成风险分流的索赔可补拆检')
    i=s.scalar(select(Inspection).where(Inspection.claim_id==c.id))
    if not i:i=Inspection(claim_id=c.id,decision='pending',**data.model_dump());s.add(i)
    else:i.findings=data.findings;i.evidence_complete=data.evidence_complete
    audit(s,u,'inspection_updated',c.code);s.flush();return obj(i)
def adjudicate(s,c,decision,u):
    from . import merge_service as mg
    mg.lock(s)
    c=s.scalar(select(Claim).where(Claim.id==c.id).with_for_update().execution_options(populate_existing=True))
    if c.status=='out_of_warranty':raise HTTPException(409,'机具故障工时已过保，不允许质保赔付')
    if c.status!='assessed':raise HTTPException(409,'索赔须完成风险分流，且不可重复裁决')
    m=mg.member_of(s,c.id)
    if m:
        g=s.get(MergeGroup,m.group_id)
        if g.primary_claim_id!=c.id:raise HTTPException(409,'归并成员不可独立裁决，须由主单统一签署')
        return mg.seal(s,g,decision,u)
    i=s.scalar(select(Inspection).where(Inspection.claim_id==c.id))
    if not i:raise HTTPException(409,'必须先记录拆检意见')
    if decision=='paid' and c.risk is not None and c.risk>=.5 and not i.evidence_complete:raise HTTPException(409,'高争议风险索赔必须补齐拆检证据后才能赔付')
    c.status=decision;i.decision=decision;audit(s,u,'claim_adjudicated',f'{c.code}:{decision}');return claim_view(s,c)
