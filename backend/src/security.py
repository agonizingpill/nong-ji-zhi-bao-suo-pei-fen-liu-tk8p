import hashlib, hmac, os, jwt
from fastapi import HTTPException, Header
from datetime import datetime,timedelta,timezone
from sqlalchemy import select
from .database import Session
from .models import User
SECRET=os.getenv('JWT_SECRET','local-warranty-demo-change-me')
def password_hash(p):return hashlib.pbkdf2_hmac('sha256',p.encode(),b'warranty-field-v1',150000).hex()
def token_for(u):return jwt.encode({'sub':str(u.id),'role':u.role,'exp':datetime.now(timezone.utc)+timedelta(hours=8)},SECRET,algorithm='HS256')
def current(authorization:str=Header(default='')):
    try:
        p=jwt.decode(authorization.removeprefix('Bearer '),SECRET,algorithms=['HS256'])
        with Session() as s:
            u=s.get(User,int(p['sub']))
            if not u:raise ValueError()
            return {'email':u.email,'role':u.role}
    except Exception:raise HTTPException(401,'登录已过期，请重新登录')
def allow(u,*roles):
    if u['role'] not in roles:raise HTTPException(403,'当前角色没有此操作权限')
