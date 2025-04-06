#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from sqlalchemy.orm import sessionmaker
from .base import Base, engine

# SQLAlchemy中，CRUD是通过会话进行管理的，所以需要先创建会话，
# 每一个SessionLocal实例就是一个数据库session
# flush指发送到数据库语句到数据库，但数据库不一定执行写入磁盘
# commit是指提交事务，将变更保存到数据库文件中

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# SessionLocal.configure(binds={Base: engine})


class __Session:
    def __enter__(self):
        self.session = SessionLocal()
        return self.session

    def __exit__(self, type, value, trace):
        self.session.close()


def with_session():
    return __Session()