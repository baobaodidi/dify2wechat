#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理模块
"""

import redis
import json
import time
from typing import Optional, Dict, Any
from loguru import logger

from .config import config

class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_store = {}  # 内存存储作为备选
        self.init_redis()
    
    def init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password or None,
                db=config.redis.db,
                decode_responses=True,
                socket_timeout=5
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存存储: {e}")
            self.redis_client = None
    
    async def get_conversation_id(self, user_id: str) -> Optional[str]:
        """获取用户的会话ID"""
        try:
            key = f"conversation:{user_id}"
            
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    session_data = json.loads(data)
                    return session_data.get('conversation_id')
            else:
                # 使用内存存储
                session_data = self.memory_store.get(key)
                if session_data:
                    return session_data.get('conversation_id')
                    
        except Exception as e:
            logger.error(f"获取会话ID失败: {e}")
        
        return None
    
    async def set_conversation_id(self, user_id: str, conversation_id: str):
        """设置用户的会话ID"""
        try:
            key = f"conversation:{user_id}"
            session_data = {
                'conversation_id': conversation_id,
                'updated_at': int(time.time())
            }
            
            if self.redis_client:
                # Redis存储，过期时间7天
                self.redis_client.setex(
                    key, 
                    7 * 24 * 3600, 
                    json.dumps(session_data)
                )
            else:
                # 内存存储
                self.memory_store[key] = session_data
                
            logger.debug(f"会话ID已保存，用户: {user_id}")
            
        except Exception as e:
            logger.error(f"保存会话ID失败: {e}")
    
    async def clear_conversation(self, user_id: str):
        """清除用户会话"""
        try:
            keys = [f"conversation:{user_id}", f"context:{user_id}"]
            
            if self.redis_client:
                self.redis_client.delete(*keys)
            else:
                for key in keys:
                    self.memory_store.pop(key, None)
                    
            logger.info(f"用户会话已清除: {user_id}")
            
        except Exception as e:
            logger.error(f"清除会话失败: {e}")

# 全局会话管理器实例
session_manager = SessionManager() 