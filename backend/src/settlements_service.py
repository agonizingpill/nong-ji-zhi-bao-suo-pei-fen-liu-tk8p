from decimal import Decimal,ROUND_HALF_UP
from datetime import datetime,timezone
from sqlalchemy import select
from fastapi import HTTPException
from .models import Claim
from .return_models import PartReturn
from .settlement_models import Settlement
from .claim_service import audit

def view(s,x):
    return {c.name:float(getattr(x,c.name))if isinstance(getattr(x,c.name),Decimal)else getattr(x,c.name)for c in x.__table__.columns}|{'claim_code':s.get(Claim,x.claim_id).code}
def qualification(s,claim_id):
    c=s.scalar(select(Claim).where(Claim.id==claim_id).with_for_update())
    if not c:raise HTTPException(404,'索赔不存在')
    if c.historical or c.status!='paid':raise HTTPException(409,'只有已签署赔付的现场索赔可结算')
    r=s.scalar(select(PartReturn).where(PartReturn.claim_id==c.id).with_for_update())
    if not r or r.state!='verified':raise HTTPException(409,'旧件尚未返厂核验，不可核定或记账赔付款')
    return c,r
def create(s,d,u):
    c,r=qualification(s,d.claim_id)
    if s.scalar(select(Settlement.id).where(Settlement.claim_id==c.id)):raise HTTPException(409,'该索赔已有结算单')
    cost=(d.part_cost+d.labor_hours*d.hour_rate).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    if cost<=0:raise HTTPException(409,'核定成本必须大于零')
    x=Settlement(**d.model_dump(),return_id=r.id,calculated_cost=cost,approved_amount=0,state='draft',approved_by='');s.add(x);s.flush();audit(s,u,'settlement_created',f'{c.code}:{cost}');return view(s,x)
def approve(s,x,d,u):
    qualification(s,x.claim_id)
    if x.state!='draft':raise HTTPException(409,'仅草稿结算可核定，核定后金额冻结')
    if d.approved_amount>x.calculated_cost:raise HTTPException(409,'批准金额超过配件费与人工费核定上限')
    x.approved_amount=d.approved_amount;x.approved_by=u['email'];x.state='approved';audit(s,u,'settlement_approved',f'{x.id}:{d.approved_amount}');return view(s,x)
def book(s,x,d,u):
    qualification(s,x.claim_id)
    if x.state!='approved':raise HTTPException(409,'须先核定金额，已记账单不能重复记账')
    x.ledger_reference=d.ledger_reference;x.booked_at=datetime.now(timezone.utc).isoformat();x.state='booked';audit(s,u,'settlement_booked',f'{x.id}:{d.ledger_reference}');return view(s,x)
