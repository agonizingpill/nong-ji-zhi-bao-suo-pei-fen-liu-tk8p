from decimal import Decimal
from pydantic import BaseModel,Field
class ReturnIn(BaseModel):
    claim_id:int
    tracking_code:str=Field(min_length=4,max_length=80)
class ReceiveIn(BaseModel):
    received_serial:str=Field(min_length=2,max_length=60)
    condition:str=Field(min_length=8,max_length=2000)
class SettlementIn(BaseModel):
    claim_id:int
    part_cost:Decimal=Field(ge=0,le=1000000,max_digits=10,decimal_places=2)
    labor_hours:Decimal=Field(ge=0,le=500,max_digits=7,decimal_places=2)
    hour_rate:Decimal=Field(ge=0,le=10000,max_digits=8,decimal_places=2)
class ApprovalIn(BaseModel):
    approved_amount:Decimal=Field(gt=0,le=2000000,max_digits=10,decimal_places=2)
class BookingIn(BaseModel):
    ledger_reference:str=Field(min_length=4,max_length=80)
