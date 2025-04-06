#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

from app.config import settings

class _BaseModelMixin:
    '''
    @name     : 混入类
    @desc     : 提供一些基础方法
    '''
    @classmethod
    def get_columns(cls):
        d = []
        for column in cls.__table__.columns:
            d.append(column.name)
        return d

    def to_dict(self):
        d = {}
        for column in self.get_columns():
            r = getattr(self, column)
            if isinstance(r, Enum):
                r = r.value
            d[column] = r
        return d

    def __getitem__(self, item):
        r = getattr(self, item)
        if isinstance(r, Enum):
            r = r.value
        return r


SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4"
)

# echo=True表示引擎将用repr()函数记录所有语句及其参数列表到日志
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True,
    # convert_unicode=True,
    pool_size=30,
)

# 创建基本映射类
Base = declarative_base(cls=_BaseModelMixin)