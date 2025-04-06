# -*- coding: utf-8 -*-
from app.database.base import Base
from sqlalchemy.orm import Session, relationship
from app.database.crud import BaseOp
from sqlalchemy.inspection import inspect
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, Text, DateTime, func, ForeignKey
)
from typing import Optional
from app.utils.tool import get_password_hash

from pydantic import BaseModel

class UserResponse(BaseModel):
    """
    该模型用于表示用户数据的响应结构。
    
    属性：
        username (str): 用户的唯一用户名。
        phone_number (str): 用户的唯一电话号码。
        pwd (str): 用户密码。
        email (Optional[str]): 用户的电子邮件地址（可选）。
        address (Optional[str]): 用户的地址（可选）。
        full_name (Optional[str]): 用户的全名（可选）。
    """
    username: str
    phone_number: str
    pwd: str
    email: Optional[str] = None
    address: Optional[str] = None
    full_name: Optional[str] = None

    class Config:
        orm_mode = True  # 告诉 Pydantic 将 SQLAlchemy 模型当作字典来处理


class ChangePasswordRequest(BaseModel):
    """
    该模型表示用户更改密码的请求数据。
    
    属性：
        current_password (str): 用户当前的密码。
        new_password (str): 用户想要设置的新密码。
    
    注意：
        全部是密文
    """
    current_password: str
    new_password: str

    class Config:
        orm_mode = True  # 告诉 Pydantic 将 SQLAlchemy 模型当作字典来处理


class ResetPasswordRequest(BaseModel):
    """
    该模型用于用户请求重置密码时的请求数据。
    
    属性：
        phone_number (str): 用于验证重置请求的用户电话号码。
    """
    phone_number: str


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='User unique identifier')
    username = Column(String(50), nullable=False, unique=True, comment='Username (unique)')
    password_hash = Column(String(255), nullable=False, comment='Password hash')
    email = Column(String(100), comment='Email (unique)')
    role = Column(Enum('admin', 'viewer', 'user', name='user_roles'), nullable=False, default='user', comment='User role')
    full_name = Column(String(100), comment='Full name')
    phone_number = Column(String(20), unique=True ,comment='Phone number')
    address = Column(Text, comment='Address')
    is_active = Column(Boolean, default=True, comment='Is active')
    created_at = Column(DateTime, server_default=func.now(), comment='Creation timestamp')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='Update timestamp')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', phone_number='{self.phone_number}', role='{self.role}', address='{self.address}')>"
    def to_dict(self):
        """Convert the SQLAlchemy model to a dictionary."""
        return {column.key: getattr(self, column.key) for column in inspect(self).mapper.column_attrs}


class UserCrud(BaseOp[User]):
    def __init__(self, session: Session):
        self.session = session
        super().__init__(session, User)

    def get_by_username(self, username: str):
        """Fetch a user by their username."""
        return self.session.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str):
        """Fetch a user by their email."""
        return self.session.query(User).filter(User.email == email).first()

    def deactivate_user(self, user_id: int):
        """Deactivate a user by setting is_active to False."""
        user = self.session.query(User).get(user_id)
        if user:
            user.is_active = False
            self.session.commit()
        return user

    def activate_user(self, user_id: int):
        """Activate a user by setting is_active to True."""
        user = self.session.query(User).get(user_id)
        if user:
            user.is_active = True
            self.session.commit()
        return user
    @staticmethod
    def create_user(db: Session, user: UserResponse) -> User:
        """
        创建一个新用户并保存到数据库中
        :param db: 数据库会话
        :param user: Pydantic 用户数据（通常会从请求体中获取）
        :return: 创建的用户对象
        """
        # 创建 User 实例并填充数据
        db_user = User(
            username=user.username,
            password_hash= get_password_hash(user.pwd),
            email=user.email if user.email else "",
            phone_number=user.phone_number,
            full_name=user.full_name if user.full_name else "",
            address=user.address,
        )

        # 将用户添加到数据库会话
        db.add(db_user)
        db.commit()  # 提交更改
        db.refresh(db_user)  # 刷新对象以获取数据库生成的 ID

        return db_user



# class UserActivityLog(Base):
#     __tablename__ = 'user_activity_logs'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, nullable=False)
#     activity_type = Column(Enum('login', 'logout', 'action', name='activity_type_enum'), nullable=False)
#     details = Column(Text)
#     ip_address = Column(String(45), nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     # 外键约束，确保 user_id 对应的用户存在
#     user = relationship("User", backref="activity_logs")  # 假设有一个 User 表

#     def __repr__(self):
#         return f"<UserActivityLog(id={self.id}, user_id={self.user_id}, activity_type={self.activity_type}, ip_address={self.ip_address}, created_at={self.created_at})>"

# class UserActivityLogCRUD:
#     def __init__(self):
#         # 创建数据库会话
#         self.session = Session()