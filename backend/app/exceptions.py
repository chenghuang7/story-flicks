from fastapi import HTTPException

class LLMResponseValidationError(Exception):
    """LLM 响应验证错误"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class CustomHTTPException(HTTPException):
    def __init__(self, msg: str, code: int):
        self.msg = msg
        self.code = code
        super().__init__(status_code=code, detail=msg)
