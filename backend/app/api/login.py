from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse

import random
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from app.services.user import create_access_token, validate_token_and_role_with_db, get_current_user
from app.utils.tool import get_password_hash, verify_password, send_sms
from app.depends import mysql_session
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.schemas.user import User, UserCrud, UserResponse, ChangePasswordRequest, ResetPasswordRequest
# from model.Dto.pwd_model import PasswordResetRequest, ResetPasswordSubmitRequest
from app.libs.message import Message

from app.exceptions import CustomHTTPException

user_router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 1000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@user_router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(mysql_session),
):
    '''
    登录
    支持手机号或者账号登录
    '''
    print(request.client.host)
    user = session.query(User).filter(User.username == form_data.username).first()
    if not user :
        user = session.query(User).filter(User.phone_number == form_data.username).first()

    if not user or not user.is_active or not verify_password(form_data.password, user.password_hash) :
        print("34343433e452356532635632")
        raise CustomHTTPException(
            code=401,
            msg="用户名或者密码错误"
        )

    print(user.password_hash, form_data.password)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": user.id, "sub": user.username, "role": user.role}, 
        expires_delta=access_token_expires
    )
    print(f"Access token: {access_token}")
    return Message.success(msg="成功", data={"user_name":user.username, "access_token": access_token, "token_type": "bearer"})

@user_router.post("/logout")
@validate_token_and_role_with_db(None)
async def logout(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(mysql_session),
):
    '''
    登出
    '''
    # 客户端处理，删除本地存储的令牌
    # 服务器端并不需要做任何操作，只是通知客户端注销
    return Message.success(msg="成功", data=[{"message": "Successfully logged out"}])

@user_router.get("/get_user_info")
@validate_token_and_role_with_db(None) 
async def get_user_info(
    session: Session = Depends(mysql_session),
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)  # 显式包含 token 参数
):
    print(current_user.to_dict())
    user_info = current_user.to_dict()
    user_info.pop("password_hash")
    return Message.success(
        msg="成功",
        data=user_info
    )

# @user_router.post("/reset_pwd")
# def reset_password_request(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
#     user = crud.get_user_by_email(db, email=request.email)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User with this email does not exist"
#         )

#     # 生成重置密码的 token（可以用更复杂的方式）
#     token = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
#     send_reset_password_email(request.email, token)

#     # 这里我们可以将 token 保存到数据库或缓存中，验证时使用
#     return {"message": "Reset password token sent to your email"}

@user_router.post("/register")
def register(user: UserResponse, 
             db: Session = Depends(mysql_session),
             ):
    '''
    注册
    检查用户名或手机号是否已存在，该字段不允许重复
    '''
    
    print(user.username)
    print(user.phone_number)
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        
        raise CustomHTTPException(
            code=402,
            msg="用户名已被注册"
        )
    
    if user.phone_number :
        db_user = db.query(User).filter(User.phone_number == user.phone_number).first()
        if db_user:
            raise CustomHTTPException(
                code=402,
                msg="手机号已被注册"
            )
    else :
        return Message.error(msg="手机号必须被提供",code=404)

    # 创建用户
    new_user = UserCrud.create_user(db=db, user=user)
    return Message.success(msg="成功", 
                           data={
                               "username": new_user.username, 
                               "phone_number": new_user.phone_number, 
                               "id": new_user.id
                            })

@user_router.delete("/delete_account", status_code=status.HTTP_204_NO_CONTENT)
@validate_token_and_role_with_db(required_role="admin")
def delete_account(
    db: Session = Depends(mysql_session),
    current_user: User = Depends(get_current_user),
    action_type: str = Query(..., enum=["deactivate", "delete"], description="Action type: 'deactivate' to disable account, 'delete' to remove account")
):
    """
    注销用户账号。
    - type = 'deactivate' 禁用账户（is_active 设置为 False）。
    - type = 'delete' 删除用户账户。
    """

    print("current_user", current_user)
    # 获取当前用户信息
    user_id = current_user.id
    
    # 从数据库查询当前用户
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise CustomHTTPException(
            code=400,
            msg="该用户不存在"
        )
    if action_type == "deactivate":
        db_user.is_active = False
        db.commit()
        return Message.success(msg="成功", data={"detail": "Account deactivated successfully"})

    elif action_type == "delete" :
        db.delete(db_user)
        db.commit()
        return Message.success(msg="成功", data={"detail": "Account deleted successfully"})
    else :
        raise CustomHTTPException(
            code=404,
            msg="非法操作"
        )
    
@user_router.put("/change_password", status_code=status.HTTP_200_OK)
def change_password(
    change_password_request: ChangePasswordRequest,
    db: Session = Depends(mysql_session),
    current_user: User = Depends(get_current_user),
):
    """
    修改用户密码。需要提供当前密码和新密码。
    """
    # 获取当前用户信息
    db_user = db.query(User).filter(User.id == current_user.id).first()
    
    if not db_user:
        raise CustomHTTPException(
            code=400,
            msg="该用户不存在"
        )
    
    if not verify_password(change_password_request.current_password, db_user.password_hash):
        raise CustomHTTPException(
            code=401,
            msg="用户名或者密码错误"
        )
    
    db_user.password_hash = get_password_hash(change_password_request.new_password)
    db.commit()
    return Message.success(msg="成功", data={"detail": "Password updated successfully"})

# # 重置密码的操作暂时不写把
# @user_router.post("/request_reset_password", status_code=status.HTTP_200_OK)
# def request_reset_password(
#     reset_request: ResetPasswordRequest,
#     db: Session = Depends(mysql_session),
# ):
#     """
#     用户请求重置密码。系统会发送一个包含验证码的短信。
#     """
#     db_user = db.query(User).filter(User.phone_number == reset_request.phone_number).first()
#     if not db_user:
#         raise CustomHTTPException(
#             code=400,
#             msg="该用户不存在"
#         )
#         return Message.error(
#             msg="该用户不存在",
#             code=400
#         )
#         raise HTTPException(status_code=404, detail="User not found")

#     verification_code = str(random.randint(100000, 999999))

#     expiration = datetime.now() + timedelta(minutes=5)

#     password_reset_request = PasswordResetRequest(
#         user_id=db_user.id,
#         phone_number=db_user.phone_number,
#         verification_code=verification_code,
#         expiration=expiration
#     )
#     db.add(password_reset_request)
#     db.commit()

#     send_sms(db_user.phone_number, f"Your password reset code is {verification_code}")
#     return Message.success(msg="成功", data={
#         "detail": "Password updated successfully",
#         "reset_code" : verification_code,
#         "describe" : "还没有买用来发验证码的手机号，暂时我返回在这里，之后再调"
#         })

#     return {"detail": "Password reset code sent successfully"}

# @user_router.post("/reset_password", status_code=status.HTTP_200_OK)
# def reset_password(
#     reset_request: ResetPasswordSubmitRequest,
#     db: Session = Depends(mysql_session),
# ):
#     """
#     用户通过手机验证码重置密码。
#     """
#     # 查找验证码请求
#     db_request = db.query(PasswordResetRequest).filter(
#         PasswordResetRequest.phone_number == reset_request.phone_number,
#         PasswordResetRequest.verification_code == reset_request.verification_code
#     ).first()

#     if not db_request:
#         raise CustomHTTPException(
#             code=411,
#             msg="验证码有误"
#         )
#         return Message.error(
#             msg="验证码有误",
#             code=411
#         )
#         raise HTTPException(status_code=400, detail="Invalid phone number or verification code")

#     if db_request.expiration < datetime.utcnow():
#         raise CustomHTTPException(
#             code=410,
#             msg="验证码已过期"
#         )
#         return Message.error(
#             msg="验证码已过期",
#             code=410
#         )
#         raise HTTPException(status_code=400, detail="Verification code has expired")

#     db_user = db.query(User).filter(User.id == db_request.user_id).first()
#     if not db_user:
#         raise CustomHTTPException(
#             code=400,
#             msg="该用户不存在"
#         )
#         return Message.error(
#             msg="该用户不存在",
#             code=400
#         )
#         raise HTTPException(status_code=404, detail="User not found")

#     # 哈希新密码并更新数据库
#     db_user.password_hash = get_password_hash(reset_request.new_password)
#     db.commit()

#     # 删除已使用的验证码请求（防止验证码被重复使用）
#     db.delete(db_request)
#     db.commit()
#     return Message.success(msg="成功", data={
#         "detail": "Password reset successfully",
#         })
#     return {"detail": "Password reset successfully"}