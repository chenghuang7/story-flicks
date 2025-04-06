#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from typing import Generic, TypeVar, Any, Optional

from pydantic import BaseModel

T = TypeVar("T")

class Message(BaseModel,Generic[T]):
    type: str = "info"
    message: str = ""
    code: int = 0
    data: Optional[T]

    total: Optional[int] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    page_index: Optional[int] = None
    page_size: Optional[int] = None


    @staticmethod
    def info(msg="", data="", code: int = 0, **kw):
        return {
            "type": "info",
            "message": msg,
            "data": data,
            "code": code,
            **kw,
        }

    @staticmethod
    def warn(msg, data="", code: int = 0, **kw):
        return {
            "type": "warning",
            "message": msg,
            "data": data,
            "code": code,
            **kw,
        }

    @staticmethod
    def error(msg, data="", code: int = -1, **kw):
        return {
            "type": "error",
            "message": msg,
            "data": data,
            "code": code,
            **kw,
        }

    @staticmethod
    def success(msg, data="", code: int = 200, **kw):
        return {
            "type": "success",
            "message": msg,
            "data": data,
            "code": code,
            **kw,
        }