from pydantic import Field, BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

class Settings(BaseSettings):
    app_name: str = "Story Flicks"
    debug: bool = True
    version: str = "1.0.0"
    
    # provider configuration
    text_provider: str = "glm"
    image_provider: str = "glm"

    # base url configuration
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    openai_base_url: str = "https://api.openai.com/v1"
    aliyun_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    ollama_base_url: str = "http://localhost:11434/v1"
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"

    # api key
    glm_api_key: str = ""
    openai_api_key: str = ""
    aliyun_api_key: str = ""
    deepseek_api_key: str = ""
    ollama_api_key: str = ""
    siliconflow_api_key: str = ""

    text_llm_model: str = "glm-4-flash"
    image_llm_model: str = "cogview-3-flash"
    
    video_url: str = "154.8.194.44"
    backend_port: str = Field("8000", description="后端端口")
    
    # 开始配置一些基础服务
    MYSQL_HOST: str = Field("", description="mysql的连接地址")
    MYSQL_PORT: int = Field(..., description="mysql的连接端口")
    MYSQL_USER: str = Field("", description="mysql的连接用户")
    MYSQL_PASSWD: str = Field("", description="mysql的连接密码")
    MYSQL_DB: str = Field("", description="mysql的连接库名")

    class Config:
        env_file = ".env"
        # env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    
    def to_dict(self):
       
        for key, value in self.__dict__.items() :
            
            if not key.startswith('_') :
                print(key,value)
        # return {
        #     key: value
        #     for key, value in self.__dict__.items()
        #     if not key.startswith('_')  # 忽略私有属性
        # }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings=Settings()