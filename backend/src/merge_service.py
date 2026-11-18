from datetime import datetime,timezone
from sqlalchemy import select,update
from fastapi import HTTPException
from .models import Claim,Machine,Inspection
from .merge_models import MergeGroup,MergeMember,MergeLock
from .claim_service import audit,claim_view

def now():return datetime.now(timezone.utc).isoformat()
def lock(s):
    # 归并与裁决共用同一哨兵写锁：先取锁再校验，整组操作彼此串行，避免并发漏成员或出现两个主单
    if not s.execute(update(MergeLock).where(MergeLock.id==1).values(touched=MergeLock.touched+1)).rowcount:
        s.add(MergeLock(id=1));s.flush()
def member_of(s,claim_id):return s.scalar(select(MergeMember).where(MergeMember.claim_id==claim_id))
def evidence(s,claim_id):
    i=s.scalar(select(Inspection).where(Inspection.claim_id==claim_id))
    return i,bool(i and i.evidence_complete)
def view(s,g):
    mems=s.scalars(select(MergeMember).where(MergeMember.group_id==g.id).order_by(MergeMember.claim_id)).all()
    members=[];blocks=[]
    for m in mems:
        c=s.get(Claim,m.claim_id);i,ev=evidence(s,c.id)
        members.append({'claim_id':c.id,'code':c.code,'risk':c.risk,'status':c.status,'has_inspection':bool(i),'evidence_complete':ev,'is_primary':c.id==g.primary_claim_id})
        if g.state=='open' and c.risk is not None and c.risk>=.5 and not ev:blocks.append(f'{c.code} 高风险缺拆检证据')
    if g.state=='open' and not any(x['is_primary'] and x['has_inspection'] for x in members):blocks.append('主单尚未记录拆检意见')
    primary=s.get(Claim,g.primary_claim_id)
    return {'id':g.id,'state':g.state,'primary_claim_id':g.primary_claim_id,'primary_code':primary.code,'machine_serial':s.get(Machine,primary.machine_id).serial,'part':primary.part,'created_by':g.created_by,'created_at':g.created_at,'sealed_at':g.sealed_at,'members':members,'blocks':blocks}
def check(c):
    if c.historical:raise HTTPException(409,f'索赔 {c.code} 为历史结案数据，不能归并')
    if c.status in('paid','denied','merged','out_of_warranty'):raise HTTPException(409,f'归并包含已结案索赔 {c.code}，整次归并已拒绝，原签结不变')
    if c.status!='assessed':raise HTTPException(409,f'索赔 {c.code} 尚未完成风险分流，不能归并')
def locked_claims(s,ids):
    return s.scalars(select(Claim).where(Claim.id.in_(ids)).order_by(Claim.id).with_for_update().execution_options(populate_existing=True)).all()
def merge(s,d,u):
    lock(s)
    ids=sorted(set(d.claim_ids))
    if len(ids)<2:raise HTTPException(409,'归并至少需要两份不同索赔')
    if d.primary_claim_id not in ids:raise HTTPException(409,'主单必须在归并索赔之中')
    claims=locked_claims(s,ids)
    if len(claims)<len(ids):raise HTTPException(404,'索赔不存在')
    for c in claims:check(c)
    mems=s.scalars(select(MergeMember).where(MergeMember.claim_id.in_(ids))).all()
    gids=sorted({m.group_id for m in mems})
    groups=s.scalars(select(MergeGroup).where(MergeGroup.id.in_(gids)).order_by(MergeGroup.id).with_for_update()).all() if gids else []
    allmems=s.scalars(select(MergeMember).where(MergeMember.group_id.in_(gids))).all() if gids else []
    extras=locked_claims(s,[m.claim_id for m in allmems if m.claim_id not in ids]) if gids else []
    for c in extras:check(c)
    everyone=list(claims)+list(extras);first=everyone[0]
    if any(c.machine_id!=first.machine_id or c.part!=first.part for c in everyone):raise HTTPException(409,'仅同机具同部位的索赔可归并或合组')
    have={m.claim_id for m in allmems}
    if len(groups)==1 and set(ids)==have and groups[0].primary_claim_id==d.primary_claim_id:
        return view(s,groups[0])
    if groups:
        byclaim={m.claim_id:m.group_id for m in allmems};tid=byclaim.get(d.primary_claim_id,groups[0].id)
        target=next(g for g in groups if g.id==tid)
        for g in groups:
            if g.id==tid:continue
            for m in allmems:
                if m.group_id==g.id:m.group_id=tid
            s.delete(g)
        for c in claims:
            if c.id not in have:s.add(MergeMember(group_id=tid,claim_id=c.id))
        target.primary_claim_id=d.primary_claim_id;s.flush()
        audit(s,u,'merge_grouped',f'{tid}:'+','.join(sorted(c.code for c in everyone)))
        return view(s,target)
    g=MergeGroup(primary_claim_id=d.primary_claim_id,state='open',created_by=u['email'],created_at=now());s.add(g);s.flush()
    for c in claims:s.add(MergeMember(group_id=g.id,claim_id=c.id))
    audit(s,u,'merge_grouped',f'{g.id}:'+','.join(sorted(c.code for c in everyone)))
    return view(s,g)
def seal(s,g,decision,u):
    mems=s.scalars(select(MergeMember).where(MergeMember.group_id==g.id).order_by(MergeMember.claim_id)).all()
    claims={c.id:c for c in locked_claims(s,[m.claim_id for m in mems])}
    if g.state!='open' or any(claims[m.claim_id].status!='assessed' for m in mems):raise HTTPException(409,'归并组已封存或成员状态已变化，请刷新后重试')
    primary=claims[g.primary_claim_id]
    pi,_=evidence(s,primary.id)
    if not pi:raise HTTPException(409,'主单必须先记录拆检意见')
    if decision=='paid':
        blocked=[claims[m.claim_id].code for m in mems if claims[m.claim_id].risk is not None and claims[m.claim_id].risk>=.5 and not evidence(s,m.claim_id)[1]]
        if blocked:raise HTTPException(409,'归并组成员高风险缺证据，主单不可赔付：'+'、'.join(blocked))
    primary.status=decision;pi.decision=decision
    for m in mems:
        c=claims[m.claim_id]
        if c.id==primary.id:continue
        c.status='merged'
        i,_=evidence(s,c.id)
        if i:i.decision=decision
    g.state='sealed';g.sealed_at=now()
    audit(s,u,'claim_adjudicated',f'{primary.code}:{decision}')
    audit(s,u,'merge_sealed',f'{primary.code}:{decision}:'+','.join(claims[m.claim_id].code for m in mems))
    return claim_view(s,primary)
