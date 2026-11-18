from datetime import date
from typing import Literal
from pydantic import BaseModel,Field
class BayIn(BaseModel):
    code:str=Field(min_length=2,max_length=40,pattern=r'\S')
    daily_hours:float=Field(gt=0,le=24,allow_inf_nan=False)
    active:bool=True
class AppointmentIn(BaseModel):
    claim_id:int
    bay_id:int
    date:date
    hours:float=Field(gt=0,le=24,allow_inf_nan=False)
class FinishIn(BaseModel):
    actual_hours:float=Field(gt=0,le=48,allow_inf_nan=False)
    overtime_reason:str=Field(default='',max_length=2000)
class StockIn(BaseModel):
    code:str=Field(min_length=2,max_length=40,pattern=r'\S')
    part:Literal['hydraulic','engine','transmission']
    available_qty:int=Field(ge=0,le=100000)
class IssueIn(BaseModel):
    appointment_id:int
    stock_id:int
    qty:int=Field(gt=0,le=1000)
class FollowupIn(BaseModel):
    appointment_id:int
    run_hours:float=Field(gt=0,le=10000,allow_inf_nan=False)
    leak_found:bool
    noise:bool
class ReworkIn(BaseModel):
    appointment_id:int
