from pydantic import BaseModel,Field
class MergeIn(BaseModel):
    claim_ids:list[int]=Field(min_length=2)
    primary_claim_id:int
