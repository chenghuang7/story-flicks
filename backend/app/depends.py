#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from app.database.session import SessionLocal, engine as mysql_engine

def mysql_session():
    '''
    @description : mysql会话管理
    '''
    db = SessionLocal(bind=mysql_engine)
    try:
        yield db
    finally:
        db.close()