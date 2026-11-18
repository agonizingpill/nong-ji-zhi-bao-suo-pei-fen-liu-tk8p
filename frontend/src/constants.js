export const ROLES={admin:'质保主管',assessor:'拆检评估员',viewer:'经销商观察员'};
export const CLAIM_STATES={submitted:'待分流',queued:'计算中',assessed:'待裁决',out_of_warranty:'工时过保',paid:'赔付结案',denied:'拒赔结案',failed:'计算失败'};
export const PARTS={hydraulic:'液压总成',engine:'发动机',transmission:'传动总成'};
export const AUDIT_ACTIONS={machine_updated:'机具台账更新',machine_registered:'新机登记',claim_received:'现场索赔受理',risk_queued:'送入风险分流',warranty_rejected:'工时过保拦截',inspection_updated:'拆检意见补充',claim_adjudicated:'主管裁决签署'};

export const RETURN_STATES={dispatched:'已发出',received:'待核验',verified:'已核验'};
export const SETTLEMENT_STATES={draft:'待核定',approved:'已核定',booked:'已记账'};

export const REPAIR_STATES={reserved:'待开工',running:'维修中',completed:'已完工'};
export const ISSUE_STATES={issued:'已领待用',returned:'已退库',consumed:'已使用'};
export const FOLLOWUP_STATES={review:'待主管复核',rework:'需返工',closed:'已关闭'};
