# 耕川 · 农机质保索赔分流

将经销商故障索赔接到机具质保台账，用传统机器学习分配拆检强度，再由主管签署赔付或拒赔。

模拟客户耕川农机有 18 名售后人员，覆盖水田拖拉机和旱作机具。现在经销商通过邮件送来维修记录，评估员人工核工时，主管在聊天里批准；维修记录散落、过保件混入、高风险缺证据是三个痛点。本项目接收机具与故障记录，替代保修核验、分流和拆检裁决段，下游得到持久化的裁决档案。演示不会向外部发送消息或真实支付。

## 启动

```bash
cp .env.example .env
docker compose up -d --build
# 启动默认 SEED_DEMO=true，亦可手动执行
docker compose exec -T backend python -m scripts.seed_demo
```

- 前端 http://localhost:18221
- 后端 http://localhost:19221/docs
- MySQL localhost:17721
- 收尾 `docker compose down -v --remove-orphans`（删除演示卷）

|角色|账号|口令|主要权限|
|---|---|---|---|
|admin 质保主管|admin@gengchuan.local|Field2026!|台账编辑、受理、拆检、最终赔付/拒赔、旧件核验、结算核定和记账|
|assessor 拆检评估员|assessor@gengchuan.local|Field2026!|新机登记、索赔、分流、拆检、旧件发件/收货、结算草稿；不可签署|
|viewer 经销商观察员|viewer@gengchuan.local|Field2026!|只读九页及审计|

## 业务与页面

1. 机具台账：序列号唯一，累计工时不可倒退。
2. 索赔受理：关联真实机具，故障工时不得低于台账；超质保工时直接标记过保，不能赔付。
3. 风险分流：Redis 队列交给 Python worker 计算，写回风险概率与模型证据；失败可重试。
4. 拆检裁决：评估员补拆检意见；概率 ≥0.5 的高风险索赔必须证据完整才能赔付；主管裁决同时更新 Claim.status 和 Inspection.decision，结案不可再改。

5. 旧件返厂：索赔完成分流并有拆检意见后登记物流；每份索赔仅一单，实收序列必须匹配发件快照；收货证据不得覆盖，主管核验后冻结。
6. 赔付结算：仅已赔付且旧件核验通过的现场索赔可生成费用核定单；Python Decimal 按配件费＋工时×费率计算金额上限；主管核定不得超额，核定后冻结金额，使用唯一记账凭证一次入账。

历史数据为固定 seed=42 生成的 180 条**模拟**已结案索赔，只用于演示。ColumnTransformer 对机型和故障部位 One-hot 编码，对故障工时、机龄、渗漏数值标准化，LogisticRegression 分类；分层留出 25%（45条），训练集 135 条，报告留出 accuracy/ROC AUC 及编码后系数。输入来自领域表而非任意 JSON。数据不足40条拒绝训练；不把模型输出作为自动赔付依据。随机种子42、训练/留出划分固定，模型的概率是模拟数据上的演示估计，未作真实业务校准。

### 一天的工作剧本

08:30 评估员查 GC-2408 水田机，台账 860h、质保2000h；09:00 受理 `CL-26017` 液压渗漏、机龄400天；09:30 分流 `CL-HIGH`（1900h/680天）；10:00 查看训练135/留出45条和风险概率；10:30 仅补文字但不勾证据，主管赔付被拒；11:00 核对工时计、油样和照片后补全证据；14:00 主管签署，索赔和拆检同步为 paid；16:00 查看审计，同时确认 `CL-EXPIRED` 的2450h过保不能赔付。真实验收会另建 `GC-E2E` 与 `CL-E2E` 检查新记录链路。

## 技术和目录

|层|技术|
|---|---|
|界面|原生 ES modules、HTML、CSS、Nginx1.27|
|后端|Python3.12、FastAPI、SQLAlchemy2、PyMySQL|
|算法|scikit-learn1.6、NumPy；真实worker训练|
|持久化|MySQL8，外键、唯一键、范围约束|
|队列|Redis7 list；共享 artifacts 卷保存模型指标与心跳|
|安全横切|JWT8小时、角色校验、PBKDF2口令、审计、请求追踪、全局错误恢复|

`backend/src/models.py` 领域实体；`schemas.py` 请求约束；`claim_service.py` 状态与关联规则；`risk_model.py` 算法；`worker.py` 队列；`main.py` 路由；`middlewares.py` 请求追踪和错误恢复。`backend/scripts/seed_demo.py` 仅插入自然键缺失的演示记录，不覆盖修改。`frontend/src/pages/` 九业务页；`components/common.js` 共享导航、状态、标题和通知；`utils/api.js` API/会话/页面状态；`utils/format.js` 转义和格式化。

角色、索赔状态、故障部位枚举分别在 `backend/src/constants.py` 与 `frontend/src/constants.js` 定义；请求部位在 `backend/src/schemas.py` 的 Literal 中约束；角色校验在 `security.py`/`main.py`，状态转换在 `claim_service.py`/`worker.py`。共用状态徽标在索赔/风险/拆检三页复用。

环境变量 `.env.example`：COMPOSE_PROJECT_NAME、FRONTEND_PORT、BACKEND_PORT、DB_PORT、JWT_SECRET；数据库连接和 Redis 地址在 Compose 内设置。命名卷 db-data、redis-data、artifacts。当前宿主默认网络池耗尽，因此显式使用10.221.22.0/24子网；若换环境冲突可修改Compose networks。五服务都有真实健康检查，backend/worker 等待 MySQL/Redis healthy，前端等待后端。默认 seed 失败记日志不阻止进程。生产前应替换演示口令和 JWT secret。

本地开发：Python `pip install -r backend/requirements.txt`，设置 DATABASE_URL/REDIS_URL 后在 backend 下 `uvicorn src.main:app --reload`；前端仍由 Compose Nginx 代理。测试与截图都在仓库外层 `test-artifacts/gb-1022/`，不会混入源码。

## 新增履约模块

`return_models.py` / `returns_service.py` 保存返件追踪及收货冻结规则；`settlement_models.py` / `settlements_service.py` 保存成本、核定金额与记账凭证；`fulfilment_schemas.py` 校验精确小数和文本，`fulfilment_routes.py` 提供独立事务及角色权限。前端 `pages/returns.js`、`pages/settlements.js` 对应两页。

|接口|权限与用途|
|---|---|
|GET /part-returns、GET /settlements|三角色读取|
|POST /part-returns、POST /part-returns/{id}/receive|admin/assessor 发出与收货|
|POST /part-returns/{id}/verify|admin 主管核验|
|POST /settlements|admin/assessor 创建费用核定单|
|POST /settlements/{id}/approve、POST /settlements/{id}/book|admin 核定和记账|

Seed 另有 `CL-RETURN-DEMO`（已赔付、可发件）和 `CL-SETTLE-DEMO`（已赔付、旧件已核验、可结算），均有关联拆检意见，且不会覆盖已录入数据。可依次发件→收货→主管核验→创建费用单→核定金额→记账。验收与截图见 `test-artifacts/gb-1022/expansion/`，新增 8 个有实际职责的业务源码文件。

## 维修履约与回访（第三轮扩展）

7. 维修工位预约：RepairBay定义每日工时与启用状态，RepairAppointment绑定已赔付现场索赔、工位、日期和预约工时。对索赔加锁避免同一索赔重复活跃预约，对工位加锁累加该日所有预约容量；完工预约仍保留当日占用。待开工→维修中→已完工。实际超预约工时时只有主管填写至少8字原因才能完工，普通评估员不能以填写原因绕过。
8. 备件库领退：SpareStock按故障部位记录可用件数，PartIssue关联预约和库位。未开工才可领料，要求对应Claim.part，锁库存拒绝不足；同预约只有一笔有效领料。开工必须领料并将领料转consumed。未开工可整笔退料一次，库存回加；已退记录保留，重新领料生成新流水，已使用不可退。
9. 返修质量回访：RepairFollowup仅关联完工预约，记录维修后运行工时（非机具累计表读数）、漏油及异常噪声。正常为review、任一异常为rework，主管负责close。异常必须关联回访发生后新建的同索赔预约，并经新预约领料、开工、完工才能关闭；原预约、其他索赔或旧维修不可抵扣。回访保存当时的原结算快照，不修改结算金额或凭证。

|接口|权限/动作|
|---|---|
|GET /repair-bays、/repair-appointments、/spare-stocks、/part-issues、/repair-followups|三角色读取|
|POST /repair-bays、PUT /repair-bays/{id}|admin维护工位；不可将日容量改低于已有日预约占用|
|POST /repair-appointments、/{id}/start、/{id}/complete|admin/assessor预约、开工、完工；超时完工仅admin+原因|
|POST /spare-stocks|admin登记独立备件库位及初始库存|
|POST /part-issues、/{id}/return|admin/assessor领料、整笔退料|
|POST /repair-followups、/{id}/rework|admin/assessor录回访、关联返工预约|
|POST /repair-followups/{id}/close|仅admin关闭|

新增 `repair_models.py`、`spare_models.py`、`followup_models.py` 分别建模工位/预约、库存/流水、回访；三个同名service分别负责日容量与完工、库存领退、返工闭环；`workshop_schemas.py` 请求边界与 `workshop_routes.py` 事务/权限；前端 `pages/repairs.js`、`spares.js`、`followups.js` 三页复用原导航/标题/API工具。维修、领料、回访状态枚举在前后端constants定义。

seed新增BAY-HYD(8h/日)、BAY-QUICK(4h/日)、BAY-OFF停用，以及hydraulic20/engine5/transmission3件备件。可用CL-RETURN-DEMO或CL-SETTLE-DEMO已赔付索赔演练预约→匹配领料→开工→完工→质量回访；异常再安排同索赔新预约返工后主管关闭。自然键只补缺失，重复seed不改已扣库存、维修实耗、工位容量、回访与原结算。新增5张表，不给原历史表加列，也不回填改变旧签结。

当前范围：预约为按日工时额度，无具体起止时刻、跨工位调度或取消；完工超时只留主管依据，不重分配其他预约。工位停用只阻止新预约，已确认维修仍可履约；无工资、采购补货、拆单部分退料、仓库扫码或真实售后联系。回访是人工登记，不外发消息；异常关闭证明同索赔返工完工，不替代另一轮质量验收或重开原赔款。新增证据见 `test-artifacts/gb-1022/v3/`。

## 已知范围

不接真实经销商附件存储、赔款财务或外部消息。拆检证据是结构化完整性确认与文字记录，不上传图片。当前小型实现为单worker，进程在任务取出后意外退出时需要管理员将失败任务恢复或重建演示数据，未做可靠消息重投。固定 seed 为可重复演示，不代表真实索赔泛化性能。

License: MIT.
