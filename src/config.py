#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from loguru import logger

class DifyConfig(BaseModel):
    """Dify配置"""
    api_base: str = Field(default="https://api.dify.ai/v1")
    api_key: str = Field(default="")
    conversation_id: str = Field(default="")
    verify_ssl: bool = Field(default=True)  # SSL证书校验开关

class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

class WeChatOfficialConfig(BaseModel):
    """微信公众号配置"""
    enabled: bool = Field(default=True)
    app_id: str = Field(default="")
    app_secret: str = Field(default="")
    token: str = Field(default="")
    encoding_aeskey: str = Field(default="")

class WorkWeChatConfig(BaseModel):
    """企业微信配置"""
    enabled: bool = Field(default=True)
    corp_id: str = Field(default="")
    corp_secret: str = Field(default="")
    agent_id: str = Field(default="")

class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: str = Field(default="")
    db: int = Field(default=0)

class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO")
    file: str = Field(default="logs/app.log")

class MessageConfig(BaseModel):
    """消息处理配置"""
    max_length: int = Field(default=2000)
    timeout: int = Field(default=3)  # 改为3秒，确保在微信5秒限制内
    enable_group: bool = Field(default=True)
    group_trigger: str = Field(default="@bot")

class SecurityConfig(BaseModel):
    """安全配置"""
    rate_limit: int = Field(default=10)
    whitelist: List[str] = Field(default_factory=list)

class Config(BaseModel):
    """主配置类"""
    dify: DifyConfig = Field(default_factory=DifyConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    wechat_official: WeChatOfficialConfig = Field(default_factory=WeChatOfficialConfig)
    work_wechat: WorkWeChatConfig = Field(default_factory=WorkWeChatConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    message: MessageConfig = Field(default_factory=MessageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

def load_config(config_path: str = "config.yaml") -> Config:
    """加载配置文件"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
        return Config()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 支持环境变量覆盖
        if 'DIFY_API_KEY' in os.environ:
            config_data.setdefault('dify', {})['api_key'] = os.environ['DIFY_API_KEY']
        
        return Config(**config_data)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return Config()

# 全局配置实例
config = load_config() 