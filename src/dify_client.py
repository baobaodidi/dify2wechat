#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify API客户端
"""

import httpx
import asyncio
import time
from typing import Optional, Dict, Any
from loguru import logger

from .config import config

class DifyClient:
    """Dify API客户端"""
    
    def __init__(self):
        self.api_base = config.dify.api_base
        self.api_key = config.dify.api_key
        self.timeout = config.message.timeout
        self.verify_ssl = config.dify.verify_ssl
        # 用于存储部分回复的字典，key为user_id
        self.partial_responses = {}
        
    async def chat_completion(
        self, 
        message: str, 
        user_id: str,
        conversation_id: Optional[str] = None,
        files: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        发送消息到Dify并获取回复
        
        Args:
            message: 用户消息
            user_id: 用户ID
            conversation_id: 会话ID（可选）
            files: 文件列表（可选）
            
        Returns:
            包含回复内容的字典
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {},
                "query": message,
                "response_mode": "blocking",  # 先保持blocking模式，确保稳定性
                "user": user_id
            }
            
            if conversation_id:
                payload["conversation_id"] = conversation_id
            
            if files:
                payload["files"] = files
            
            # 使用更短的超时时间和优化的连接设置
            timeout = httpx.Timeout(connect=1.0, read=self.timeout, write=1.0, pool=1.0)
            async with httpx.AsyncClient(timeout=timeout, verify=self.verify_ssl) as client:
                response = await client.post(
                    f"{self.api_base}/chat-messages",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Dify API调用成功，用户: {user_id}")
                    return {
                        "success": True,
                        "answer": result.get("answer", ""),
                        "conversation_id": result.get("conversation_id", ""),
                        "message_id": result.get("id", "")
                    }
                else:
                    logger.error(f"Dify API调用失败: {response.status_code}, {response.text}")
                    return {
                        "success": False,
                        "error": f"API调用失败: {response.status_code}",
                        "answer": "抱歉，我暂时无法回复，请稍后再试。"
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Dify API调用超时，用户: {user_id}")
            # 超时时返回友好提示，而不是错误
            return {
                "success": False,
                "error": "请求超时",
                "answer": "我正在思考中... 🤔"
            }
        except Exception as e:
            logger.error(f"Dify API调用异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "系统异常，请稍后再试。"
            }
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取会话消息历史
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID  
            limit: 消息数量限制
            
        Returns:
            包含消息历史的字典
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "user": user_id,
                "limit": limit
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                response = await client.get(
                    f"{self.api_base}/messages",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "messages": result.get("data", [])
                    }
                else:
                    logger.error(f"获取消息历史失败: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"获取失败: {response.status_code}",
                        "messages": []
                    }
                    
        except Exception as e:
            logger.error(f"获取消息历史异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "messages": []
            }

    async def chat_completion_streaming(
        self, 
        message: str, 
        user_id: str,
        conversation_id: Optional[str] = None,
        files: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        使用流式模式发送消息到Dify并获取回复（更快的首字节时间）
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {},
                "query": message,
                "response_mode": "streaming",  # 使用流式响应
                "user": user_id
            }
            
            if conversation_id:
                payload["conversation_id"] = conversation_id
            
            if files:
                payload["files"] = files
            
            # 流式模式使用较长的超时时间，让微信层面的4.5秒截断先生效
            timeout = httpx.Timeout(connect=1.0, read=10.0, write=1.0, pool=1.0)  # read超时10秒，让微信层面截断先生效
            
            async with httpx.AsyncClient(timeout=timeout, verify=self.verify_ssl) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat-messages",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status_code != 200:
                        logger.error(f"Dify API调用失败: {response.status_code}")
                        return {
                            "success": False,
                            "error": f"API调用失败: {response.status_code}",
                            "answer": "抱歉，我暂时无法回复，请稍后再试。"
                        }
                    
                    # 处理流式响应 - 支持部分内容获取
                    answer = ""
                    conversation_id_result = ""
                    message_id = ""
                    start_time = time.time()
                    first_chunk_received = False
                    
                    # 清除之前的部分回复
                    self.partial_responses[user_id] = {
                        "answer": "",
                        "first_chunk_time": None,
                        "conversation_id": "",
                        "message_id": ""
                    }
                    
                    try:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                try:
                                    import json
                                    data = json.loads(line[6:])  # 移除 "data: " 前缀
                                    
                                    if data.get("event") == "message":
                                        answer += data.get("answer", "")
                                        # 实时更新部分回复
                                        self.partial_responses[user_id]["answer"] = answer
                                        self.partial_responses[user_id]["conversation_id"] = data.get("conversation_id", "")
                                        self.partial_responses[user_id]["message_id"] = data.get("id", "")
                                        
                                        if not first_chunk_received:
                                            first_chunk_received = True
                                            first_chunk_time = time.time() - start_time
                                            self.partial_responses[user_id]["first_chunk_time"] = first_chunk_time
                                            logger.info(f"收到首个数据块，耗时{first_chunk_time:.2f}秒")
                                        
                                    elif data.get("event") == "message_end":
                                        conversation_id_result = data.get("conversation_id", "")
                                        message_id = data.get("id", "")
                                        break
                                except json.JSONDecodeError:
                                    continue
                    except asyncio.CancelledError:
                        # 被取消时，返回部分内容
                        logger.info(f"流式处理被取消，返回部分内容，用户: {user_id}")
                        partial = self.partial_responses.get(user_id, {})
                        return {
                            "success": True,
                            "answer": partial.get("answer", ""),
                            "conversation_id": partial.get("conversation_id", ""),
                            "message_id": partial.get("message_id", ""),
                            "partial": True
                        }
                    
                    # 正常完成，返回结果
                    logger.info(f"Dify API流式调用成功，用户: {user_id}")
                    return {
                        "success": True,
                        "answer": answer,
                        "conversation_id": conversation_id_result,
                        "message_id": message_id
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Dify API流式调用超时，用户: {user_id}")
            return {
                "success": False,
                "error": "请求超时",
                "answer": "我正在思考中... 🤔"
            }
        except Exception as e:
            logger.error(f"Dify API流式调用异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "系统异常，请稍后再试。"
            }
    
    def get_partial_response(self, user_id: str) -> Dict[str, Any]:
        """获取用户的部分回复"""
        partial = self.partial_responses.get(user_id, {})
        first_chunk_time = partial.get("first_chunk_time")
        answer = partial.get("answer", "")
        
        if first_chunk_time is None:
            # 没有收到首字节，返回俏皮回复
            return {
                "success": False,
                "error": "首字节超时",
                "answer": "哎呀，我的大脑有点卡顿了 🤔 可能是在思考太深奥的问题！要不换个简单点的问题试试？😊",
                "partial": False
            }
        elif first_chunk_time <= 4.5:
            # 首字节在4.5秒内，返回部分内容
            if answer:
                return {
                    "success": True,
                    "answer": answer,
                    "conversation_id": partial.get("conversation_id", ""),
                    "message_id": partial.get("message_id", ""),
                    "partial": True
                }
            else:
                return {
                    "success": True,
                    "answer": "我正在思考中... 🤔",
                    "conversation_id": partial.get("conversation_id", ""),
                    "message_id": partial.get("message_id", ""),
                    "partial": True
                }
        else:
            # 首字节超过4.5秒，返回俏皮回复
            return {
                "success": False,
                "error": "首字节超时",
                "answer": "我的思考速度有点跟不上你的节奏呢 🐌 让我缓缓，或者你可以问个更直接的问题？✨",
                "partial": False
            }

# 全局Dify客户端实例
dify_client = DifyClient() 