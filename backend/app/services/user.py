from sqlalchemy.orm import Session
from fastapi import  Depends, Body

from datetime import datetime
from functools import wraps

from fastapi.responses import JSONResponse

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.depends import mysql_session
from app.schemas.user import User

from app.exceptions import CustomHTTPException

from app.libs.message import Message


from app.utils.tool import get_password_hash

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_db(username: str, db: Session):
    return db.query(User).filter(User.username == username).first()

def validate_token_and_role_with_db(required_role: Optional[str] = None):
    '''
    装饰器验证token
    '''
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, token: str = Depends(oauth2_scheme), session: Session = Depends(mysql_session), **kwargs):
            pass
            print(args)
            print(token)
            print(kwargs)
            try:
                payload = verify_token(token)#jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                id = payload.get("id")
                username = payload.get("sub")
                role = payload.get("role")
                print(username)
                print(role)
                if username is None or role is None:
                    raise CustomHTTPException(
                        msg="Token 非法",
                        code=421
                    )
                
                user = session.query(User).filter(User.id == id).first()
                if not user:
                    raise CustomHTTPException(
                        msg="Token 非法",
                        code=421
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                    )
                if required_role and required_role!="admin" and role != required_role:
                    raise CustomHTTPException(
                        msg="权限不允许",
                        code=423
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )
                return await func(*args, session=session, **kwargs)
            except jwt.ExpiredSignatureError:
                raise CustomHTTPException(
                    msg="Token 过期",
                    code=420
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except jwt.InvalidTokenError:
                raise CustomHTTPException(
                    msg="Token 非法",
                    code=421
                )
            
        return wrapper
    return decorator


def get_current_user(db: Session = Depends(mysql_session), token: str = Depends(oauth2_scheme)) -> User:
    """
    解析和验证用户的 JWT，获取当前用户。
    """
    # 解码和验证 JWT
    user_data = verify_token(token)  # 假设 verify_token 会返回用户数据
    
    
    # 获取用户信息
    db_user = db.query(User).filter(User.id == user_data.get("id")).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

def verify_token(token: str):
    try:
        # 解码 JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise CustomHTTPException(
            msg="Token 过期",
            code=420
        )
    except jwt.PyJWTError:
        raise CustomHTTPException(
            msg="Token 非法",
            code=421
        )
        raise HTTPException(status_code=421, detail="Token 非法")