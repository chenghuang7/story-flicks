
import json
import time


class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).type(default error , optional: error,warning,info,skip)
    '''

    def __init__(self, error, message, data='', type="error", err_code: int = -1, page_size=None, page_index=None,
                 total=0, end_time=int(time.time()*1000), start_time=int(time.time()*1000)):
        super(APIError, self).__init__(message)
        self.type = type
        self.error = error  # field相关 XXX 错误
        self.data = data  # 错误携带的data 信息，用于开发人员查看详细的错误信息
        self.message = message
        self.err_code = err_code
        self.page_size = page_size
        self.page_index = page_index
        self.total = total
        self.end_time=end_time
        self.start_time=start_time

    def __str__(self):
        """返回一个对象的描述信息"""
        return json.dumps(self.dict(), ensure_ascii=False)

    def keys(self):
        return ["type", "error", "data", "message", "err_code", "end_time", "start_time", "page_size", "page_index", "total"]

    def __getitem__(self, item):
        return getattr(self, item)

    def dict(self):
        return dict(
            type=self.type,
            error=self.error,
            data=self.data,
            message=self.message,
            err_code=self.err_code,
            end_time=self.end_time,
            page_size=self.page_size,
            page_index=self.page_index,
            total=self.total,
            start_time=self.start_time
        )


class APIPermissionLoginError(APIError):
    """
    Indicate the api has no permission. 前端需要重新登录
    """

    def __init__(self, message="登录状态已经失效", data="权限", err_code=2):
        super(APIPermissionLoginError, self).__init__(
            "APIPermissionLoginError", message, data, err_code=err_code
        )


class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''

    def __init__(self, message='无效权限', data="权限", err_code=5):
        super(APIPermissionError, self).__init__('APIPermissionError', message, data, err_code=err_code)


class APIPermissionProjectError(APIError):
    '''
    Indicate the api has no permission.
    '''

    def __init__(self, message='项目无效权限', data="权限", err_code=6):
        super(APIPermissionProjectError, self).__init__('APIPermissionProjectError', message, data, err_code=err_code)


class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''

    def __init__(self, message='数据未找到', data="", err_code=11):
        super(APIResourceNotFoundError, self).__init__("APIResourceNotFoundError", message, data=data,
                                                       err_code=err_code)


class APIResourceDuplicate(APIError):
    """
    资源重复提交错误
    """

    def __init__(self, message='重复资源', data="", err_code=12):
        super(APIResourceDuplicate, self).__init__("APIResourceDuplicate", message, data=data, err_code=err_code)


class APIParaError(APIError):
    '''
    API 参数错误
    '''

    def __init__(self, message="接口参数错误", data="", err_code=13):
        super(APIParaError, self).__init__("APIParaError", message, data=data, err_code=err_code)


class APIInterfaceNotFinish(APIError):
    '''
    接口还未完成的错误
    '''

    def __init__(self, message='此接口的功能正在开发中', data="", err_code=14):
        super(APIInterfaceNotFinish, self).__init__("APIInterfaceNotFinish", message, data=data, err_code=err_code)


class APIRequestsError(APIError):
    """
    服务器请求requests 数据的时候，request请求错误
    """

    def __init__(self, message="第三方服务访问错误", data="", err_code=15):
        super(APIRequestsError, self).__init__("APIRequestsError", message, data=data, err_code=err_code)


class SendEmailError(APIError):
    def __init__(self, message="邮件发送失败", data="", err_code=16):
        super(SendEmailError, self).__init__("SendEmailError", message, data=data, err_code=err_code)


class MysqlError(APIError):
    def __init__(self, message, data, err_code=18):
        super(MysqlError, self).__init__("MysqlOperateError", message=message, data=data, err_code=err_code)


class SensitiveWordError(APIError):
    def __init__(self, message="用户输入敏感", data="", err_code=19):
        super(SensitiveWordError, self).__init__("SensitiveWordError",
                                                 message=message,
                                                 data=data,
                                                 err_code=err_code)


class FileError(APIError):
    """
    文件错误
    """
    def __init__(self, message="文件解析失败", data="", err_code=20):
        super(FileError, self).__init__("FileError", message, data=data, err_code=err_code)