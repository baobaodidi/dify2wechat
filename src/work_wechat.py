#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信处理模块
"""

import hashlib
import time
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from loguru import logger
import httpx

from .config import config
from .dify_client import dify_client
from .session_manager import session_manager

class WorkWeChatHandler:
    """企业微信消息处理器"""
    
    def __init__(self):
        self.corp_id = config.work_wechat.corp_id
        self.corp_secret = config.work_wechat.corp_secret
        self.agent_id = config.work_wechat.agent_id
        self.access_token = None
        self.token_expires_at = 0
    
    async def get_access_token(self) -> str:
        """获取企业微信访问令牌"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                'corpid': self.corp_id,
                'corpsecret': self.corp_secret
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                result = response.json()
                
                if result.get('errcode') == 0:
                    self.access_token = result['access_token']
                    # 提前5分钟过期
                    self.token_expires_at = time.time() + result['expires_in'] - 300
                    logger.info("企业微信访问令牌获取成功")
                    return self.access_token
                else:
                    logger.error(f"获取访问令牌失败: {result}")
                    raise Exception(f"获取访问令牌失败: {result.get('errmsg', '未知错误')}")
                    
        except Exception as e:
            logger.error(f"获取访问令牌异常: {e}")
            raise
    
    async def send_message(self, user_id: str, content: str) -> bool:
        """发送消息给用户"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                },
                "safe": 0
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                result = response.json()
                
                if result.get('errcode') == 0:
                    logger.info(f"企业微信消息发送成功，用户: {user_id}")
                    return True
                else:
                    logger.error(f"企业微信消息发送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"发送企业微信消息异常: {e}")
            return False
    
    def parse_xml_message(self, xml_data: str) -> Dict[str, Any]:
        """解析XML消息"""
        try:
            root = ET.fromstring(xml_data)
            message = {}
            for child in root:
                message[child.tag] = child.text
            return message
        except Exception as e:
            logger.error(f"XML消息解析失败: {e}")
            return {}
    
    async def handle_message(self, message: Dict[str, Any]) -> bool:
        """处理企业微信消息"""
        try:
            msg_type = message.get('MsgType', '')
            from_user = message.get('FromUserName', '')
            content = message.get('Content', '').strip()
            
            # 只处理文本消息
            if msg_type != 'text' or not content:
                await self.send_message(from_user, "抱歉，我目前只能处理文本消息。")
                return True
            
            # 检查群聊@bot触发
            if config.message.enable_group:
                trigger = config.message.group_trigger
                if content.startswith(trigger):
                    # 移除触发词
                    content = content[len(trigger):].strip()
                elif '@' in content:
                    # 可能是群聊消息，但没有@bot
                    return True
            
            if not content:
                await self.send_message(from_user, "请输入要对话的内容。")
                return True
            
            # 获取会话ID
            conversation_id = await session_manager.get_conversation_id(from_user)
            
            # 调用Dify API
            result = await dify_client.chat_completion(
                message=content,
                user_id=from_user,
                conversation_id=conversation_id
            )
            
            # 保存会话ID
            if result.get('conversation_id'):
                await session_manager.set_conversation_id(
                    from_user, 
                    result['conversation_id']
                )
            
            # 发送回复
            reply_content = result.get('answer', '抱歉，我暂时无法回复。')
            
            # 限制消息长度
            max_length = config.message.max_length
            if len(reply_content) > max_length:
                reply_content = reply_content[:max_length] + "..."
            
            await self.send_message(from_user, reply_content)
            logger.info(f"企业微信消息处理完成，用户: {from_user}")
            return True
            
        except Exception as e:
            logger.error(f"企业微信消息处理异常: {e}")
            # 发送错误消息
            try:
                await self.send_message(
                    message.get('FromUserName', ''), 
                    "系统异常，请稍后再试。"
                )
            except:
                pass
            return False
    
    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """验证企业微信回调URL"""
        # 企业微信的URL验证逻辑
        # 这里需要根据企业微信的具体验证方式实现
        # 通常涉及解密和验证
        return echostr
    
    async def handle_webhook(self, request: Request) -> str:
        """处理企业微信Webhook请求"""
        try:
            # GET请求用于验证回调URL
            if request.method == "GET":
                msg_signature = request.query_params.get('msg_signature', '')
                timestamp = request.query_params.get('timestamp', '')
                nonce = request.query_params.get('nonce', '')
                echostr = request.query_params.get('echostr', '')
                
                # 验证URL（这里简化处理）
                logger.info("企业微信URL验证")
                return echostr
            
            # POST请求处理消息
            elif request.method == "POST":
                body = await request.body()
                xml_data = body.decode('utf-8')
                message = self.parse_xml_message(xml_data)
                
                if not message:
                    return ""
                
                logger.info(f"收到企业微信消息: {message.get('MsgType', '')} from {message.get('FromUserName', '')}")
                
                # 异步处理消息
                await self.handle_message(message)
                return "success"
                
        except Exception as e:
            logger.error(f"企业微信Webhook处理异常: {e}")
            return "error"

# 全局企业微信处理器实例
work_wechat_handler = WorkWeChatHandler() 