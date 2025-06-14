#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号处理模块
"""

import asyncio
import hashlib
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Set
from fastapi import Request, HTTPException
from loguru import logger
from wechatpy import WeChatClient
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException

from .config import config
from .dify_client import dify_client
from .session_manager import session_manager

class WeChatOfficialHandler:
    """微信公众号消息处理器"""
    
    def __init__(self):
        self.token = config.wechat_official.token
        self.app_id = config.wechat_official.app_id
        self.app_secret = config.wechat_official.app_secret
        self.encoding_aes_key = config.wechat_official.encoding_aeskey
        
        # 初始化加密处理器
        if self.encoding_aes_key:
            self.crypto = WeChatCrypto(self.token, self.encoding_aes_key, self.app_id)
        else:
            self.crypto = None
        
        # 初始化微信客户端（用于发送客服消息）
        self.wechat_client = None
        if self.app_id and self.app_secret:
            try:
                self.wechat_client = WeChatClient(self.app_id, self.app_secret)
                logger.info("微信客户端初始化成功")
            except Exception as e:
                logger.warning(f"微信客户端初始化失败: {e}")
            
        # 消息去重缓存（存储最近处理的消息ID）
        self.processed_messages: Set[str] = set()
        self.max_cache_size = 1000
        
        # 异步处理任务跟踪
        self.async_tasks: Dict[str, asyncio.Task] = {}
    
    async def send_customer_service_message(self, user_id: str, content: str) -> bool:
        """发送客服消息"""
        if not self.wechat_client:
            logger.error("❌ 微信客户端未初始化，无法发送客服消息")
            return False
        
        try:
            # 使用异步方式发送客服消息
            import httpx
            
            logger.info(f"🔑 开始获取access_token...")
            # 获取access_token
            access_token = self.wechat_client.access_token
            logger.info(f"✅ 获取access_token成功: {access_token[:20]}...")
            
            # 构建客服消息API URL
            url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
            logger.info(f"🌐 客服消息API URL: {url[:80]}...")
            
            # 构建消息数据
            data = {
                "touser": user_id,
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            logger.info(f"📦 消息数据: {data}")
            
            # 发送HTTP请求
            logger.info("🚀 开始发送HTTP请求...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
                logger.info(f"📡 HTTP响应状态: {response.status_code}")
                
                result = response.json()
                logger.info(f"📄 API响应结果: {result}")
                
                if result.get('errcode') == 0:
                    logger.info(f"✅ 客服消息发送成功，用户: {user_id}")
                    return True
                else:
                    logger.error(f"❌ 客服消息发送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"💥 客服消息发送异常: {e}")
            import traceback
            logger.error(f"异常详情: {traceback.format_exc()}")
            return False
    
    async def async_process_message(self, message: Dict[str, Any], user_id: str):
        """异步处理消息并发送客服消息回复"""
        try:
            logger.info(f"🚀 开始异步处理消息，用户: {user_id}")
            
            content = message.get('Content', '').strip()
            logger.info(f"📝 异步处理消息内容: {content[:50]}...")
            
            # 获取会话ID
            conversation_id = await session_manager.get_conversation_id(user_id)
            logger.info(f"🔗 获取会话ID: {conversation_id}")
            
            # 调用Dify API（使用更长的超时时间）
            original_timeout = dify_client.timeout
            dify_client.timeout = 30  # 异步处理时使用30秒超时
            logger.info(f"⏰ 设置Dify超时时间: {dify_client.timeout}秒")
            
            logger.info("📡 开始调用Dify API（流式模式）...")
            result = await dify_client.chat_completion_streaming(
                message=content,
                user_id=user_id,
                conversation_id=conversation_id
            )
            logger.info("✅ Dify API流式调用完成")
            
            # 恢复原始超时设置
            dify_client.timeout = original_timeout
            
            # 保存会话ID
            if result.get('conversation_id'):
                await session_manager.set_conversation_id(
                    user_id, 
                    result['conversation_id']
                )
                logger.info(f"💾 保存会话ID: {result['conversation_id']}")
            
            # 获取回复内容
            reply_content = result.get('answer', '抱歉，我暂时无法回复。')
            logger.info(f"💬 获取回复内容，长度: {len(reply_content)}")
            
            # 限制消息长度
            max_length = config.message.max_length
            if len(reply_content) > max_length:
                reply_content = reply_content[:max_length] + "..."
                logger.info(f"✂️ 消息长度超限，截断至: {len(reply_content)}")
            
            # 通过客服消息API发送回复
            logger.info("📤 开始发送客服消息...")
            success = await self.send_customer_service_message(user_id, reply_content)
            
            if success:
                logger.info(f"✅ 异步消息处理完成，用户: {user_id}")
            else:
                logger.warning(f"⚠️ 客服消息API不可用，用户: {user_id}")
                logger.info("💡 建议：1) 升级为认证服务号 2) 开通客服功能 3) 或使用模板消息")
                logger.info(f"📝 AI回复内容（已生成但无法发送）: {reply_content[:100]}...")
                
        except Exception as e:
            logger.error(f"💥 异步消息处理异常: {e}")
            import traceback
            logger.error(f"异常详情: {traceback.format_exc()}")
            
            # 发送错误提示
            try:
                await self.send_customer_service_message(
                    user_id, 
                    "抱歉，处理您的消息时出现了问题，请稍后再试。"
                )
            except Exception as send_error:
                logger.error(f"发送错误提示失败: {send_error}")
        finally:
            # 清理任务记录
            if user_id in self.async_tasks:
                del self.async_tasks[user_id]
                logger.info(f"🧹 清理异步任务记录，用户: {user_id}")
        
    def verify_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """验证微信服务器签名"""
        try:
            tmp_list = [self.token, timestamp, nonce]
            tmp_list.sort()
            tmp_str = ''.join(tmp_list)
            hash_obj = hashlib.sha1(tmp_str.encode('utf-8'))
            return hash_obj.hexdigest() == signature
        except Exception as e:
            logger.error(f"签名验证失败: {e}")
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
    
    def create_text_response(self, to_user: str, from_user: str, content: str) -> str:
        """创建文本回复消息"""
        timestamp = int(time.time())
        template = """<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
        return template.format(
            to_user=to_user,
            from_user=from_user,
            timestamp=timestamp,
            content=content
        )
    
    async def handle_message(self, message: Dict[str, Any]) -> str:
        """处理微信消息"""
        try:
            msg_type = message.get('MsgType', '')
            from_user = message.get('FromUserName', '')
            to_user = message.get('ToUserName', '')
            
            logger.info(f"处理消息类型: {msg_type}, 来自: {from_user}")
            
            # 只处理文本消息
            if msg_type != 'text':
                return self.create_text_response(
                    from_user, to_user, 
                    "抱歉，我目前只能处理文本消息。"
                )
            
            content = message.get('Content', '').strip()
            if not content:
                return self.create_text_response(
                    from_user, to_user,
                    "请发送文本消息与我对话。"
                )
            
            logger.info(f"收到消息内容: {content}")
            
            # 微信公众号默认不需要@bot触发（因为是私聊）
            # 如果启用了群聊模式且有触发词，则检查触发
            if config.message.enable_group and config.message.group_trigger:
                trigger = config.message.group_trigger
                if content.startswith(trigger):
                    # 移除触发词
                    content = content[len(trigger):].strip()
                # 微信公众号私聊模式下，即使有触发词配置也正常处理
            
            # 获取会话ID
            conversation_id = await session_manager.get_conversation_id(from_user)
            
            # 统一使用流式模式，提升响应速度
            content_length = len(content)
            logger.info(f"使用流式模式处理消息，长度: {content_length}")
            
            result = await dify_client.chat_completion_streaming(
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
            
            # 返回回复
            reply_content = result.get('answer', '抱歉，我暂时无法回复。')
            
            # 限制消息长度
            max_length = config.message.max_length
            if len(reply_content) > max_length:
                reply_content = reply_content[:max_length] + "..."
            
            logger.info(f"公众号消息处理完成，用户: {from_user}, 回复: {reply_content[:50]}...")
            return self.create_text_response(from_user, to_user, reply_content)
            
        except Exception as e:
            logger.error(f"消息处理异常: {e}")
            return self.create_text_response(
                message.get('FromUserName', ''),
                message.get('ToUserName', ''),
                "系统异常，请稍后再试。"
            )
    
    async def handle_webhook(self, request: Request) -> str:
        """处理微信Webhook请求"""
        try:
            # GET请求用于验证服务器
            if request.method == "GET":
                signature = request.query_params.get('signature', '')
                timestamp = request.query_params.get('timestamp', '')
                nonce = request.query_params.get('nonce', '')
                echostr = request.query_params.get('echostr', '')
                
                if self.verify_signature(signature, timestamp, nonce):
                    logger.info("微信服务器验证成功")
                    return echostr
                else:
                    logger.error("微信服务器验证失败")
                    raise HTTPException(status_code=403, detail="验证失败")
            
            # POST请求处理消息
            elif request.method == "POST":
                # 获取请求参数
                signature = request.query_params.get('signature', '')
                timestamp = request.query_params.get('timestamp', '')
                nonce = request.query_params.get('nonce', '')
                msg_signature = request.query_params.get('msg_signature', '')
                encrypt_type = request.query_params.get('encrypt_type', '')
                
                # 读取消息体
                body = await request.body()
                xml_data = body.decode('utf-8')
                
                logger.info(f"收到POST请求，加密类型: {encrypt_type}")
                logger.debug(f"原始XML数据: {xml_data}")
                
                # 处理加密消息
                if encrypt_type == 'aes' and self.crypto:
                    try:
                        # 解密消息
                        decrypted_xml = self.crypto.decrypt_message(
                            xml_data, msg_signature, timestamp, nonce
                        )
                        logger.info("消息解密成功")
                        logger.debug(f"解密后XML: {decrypted_xml}")
                        xml_data = decrypted_xml
                    except InvalidSignatureException as e:
                        logger.error(f"消息签名验证失败: {e}")
                        raise HTTPException(status_code=403, detail="消息签名验证失败")
                    except Exception as e:
                        logger.error(f"消息解密失败: {e}")
                        raise HTTPException(status_code=400, detail="消息解密失败")
                else:
                    # 明文消息，暂时跳过签名验证（微信明文模式签名机制不同）
                    logger.info("明文模式消息，跳过签名验证")
                
                # 解析消息
                message = self.parse_xml_message(xml_data)
                
                if not message:
                    logger.warning("消息解析为空")
                    return ""
                
                logger.info(f"收到微信消息: {message.get('MsgType', '')} from {message.get('FromUserName', '')}")
                
                # 消息去重检查
                msg_id = message.get('MsgId', '')
                if msg_id and msg_id in self.processed_messages:
                    logger.info(f"消息已处理过，跳过: {msg_id}")
                    # 返回空响应，避免重复回复
                    from fastapi import Response
                    return Response(content="", media_type="text/xml")
                
                # 添加到已处理消息缓存
                if msg_id:
                    self.processed_messages.add(msg_id)
                    # 限制缓存大小
                    if len(self.processed_messages) > self.max_cache_size:
                        # 移除一半的旧消息
                        old_messages = list(self.processed_messages)[:self.max_cache_size // 2]
                        for old_msg in old_messages:
                            self.processed_messages.discard(old_msg)
                
                # 微信要求5秒内响应，采用4.5秒截断策略
                try:
                    content_length = len(message.get('Content', ''))
                    timeout_duration = 4.5  # 4.5秒超时，实现截断策略
                    
                    logger.info(f"消息长度: {content_length}, 超时设置: {timeout_duration}秒")
                    
                    # 设置超时处理
                    import asyncio
                    response = await asyncio.wait_for(
                        self.handle_message(message), 
                        timeout=timeout_duration
                    )
                except asyncio.TimeoutError:
                    logger.warning("4.5秒截断触发")
                    from_user = message.get('FromUserName', '')
                    to_user = message.get('ToUserName', '')
                    
                    # 获取部分回复内容
                    from .dify_client import dify_client
                    partial_result = dify_client.get_partial_response(from_user)
                    
                    reply_content = partial_result.get('answer', '抱歉，我暂时无法回复。')
                    
                    # 如果是部分内容，添加提示
                    if partial_result.get('partial', False):
                        logger.info(f"返回部分内容，长度: {len(reply_content)}")
                    else:
                        logger.info(f"返回俏皮回复")
                    
                    response = self.create_text_response(from_user, to_user, reply_content)
                    

                
                logger.info(f"准备返回回复，长度: {len(response)}")
                logger.info(f"回复XML内容: {response}")
                
                # 如果是加密模式，需要加密回复
                if encrypt_type == 'aes' and self.crypto:
                    try:
                        encrypted_response = self.crypto.encrypt_message(response, nonce, timestamp)
                        logger.info("回复消息加密成功")
                        logger.info(f"最终返回加密响应，长度: {len(encrypted_response)}")
                        from fastapi import Response
                        return Response(content=encrypted_response, media_type="text/xml")
                    except Exception as e:
                        logger.error(f"回复消息加密失败: {e}")
                        logger.info(f"返回明文响应: {response}")
                        from fastapi import Response
                        return Response(content=response, media_type="text/xml")
                
                logger.info(f"最终返回明文响应: {response}")
                # 返回XML响应，设置正确的Content-Type
                from fastapi import Response
                return Response(content=response, media_type="text/xml")
                
        except Exception as e:
            logger.error(f"Webhook处理异常: {e}")
            raise HTTPException(status_code=500, detail="内部服务器错误")

# 全局微信公众号处理器实例
wechat_official_handler = WeChatOfficialHandler() 