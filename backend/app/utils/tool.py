import re
import uuid
from passlib.context import CryptContext

def generate_uuid(type : int = 0):

    if type == 0 :
        uuid_ans = uuid.uuid1()
    else :
        uuid_ans = uuid.uuid4()
    return str(uuid_ans)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def send_sms(phone_number, verification_code):

    print(f"已经将验证码{verification_code}发送到手机{phone_number}")


def is_valid_phone_number(phone: str) -> bool:
    """
    判断一个字符串是否是有效的中国手机号。

    参数:
        phone (str): 待检查的字符串。

    返回:
        bool: 如果是有效的手机号返回 True，否则返回 False。
    """
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

# # 示例用法
# print(is_valid_phone_number("13812345678"))  # 输出: True
# print(is_valid_phone_number("12345678901"))  # 输出: False
# print(is_valid_phone_number("1891234567"))   # 输出: False