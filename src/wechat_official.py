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
from .menu_manager import menu_manager

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
    
    async def _ensure_menu_exists(self):
        """确保菜单存在"""
        try:
            # 检查当前菜单
            current_menu = await menu_manager.get_menu()
            if not current_menu.get('menu'):
                # 菜单不存在，创建默认菜单
                logger.info("检测到菜单不存在，正在创建默认菜单...")
                success = await menu_manager.create_menu()
                if success:
                    logger.info("✅ 默认菜单创建成功")
                else:
                    logger.error("❌ 默认菜单创建失败")
        except Exception as e:
            logger.error(f"确保菜单存在时发生异常: {e}")
    
    async def handle_menu_click(self, message: Dict[str, Any], from_user: str, to_user: str) -> str:
        """处理菜单点击事件"""
        event_key = message.get('EventKey', '')
        logger.info(f"处理菜单点击事件: {event_key}, 用户: {from_user}")
        
        if event_key == 'AI_CHAT' or event_key == 'START_CHAT':
            response_text = "🤖 AI助手已准备就绪！\n\n请直接发送消息开始对话：\n• 问我任何问题\n• 寻求建议和帮助\n• 进行有趣的聊天\n\n我会尽我所能为你提供帮助！ ✨"
            
        elif event_key == 'CLEAR_HISTORY':
            # 清除用户会话历史
            try:
                await session_manager.clear_conversation(from_user)
                response_text = "🔄 会话历史已清除！\n\n你现在可以开始一个全新的对话。之前的聊天记录已被清空，我将不会记住之前的对话内容。"
            except Exception as e:
                logger.error(f"清除会话历史失败: {e}")
                response_text = "❌ 清除历史记录时发生错误，请稍后再试。"
        
        elif event_key == 'HELP_INFO':
            response_text = """ℹ️ 使用帮助

🤖 我是基于Dify的AI智能助手，具有以下功能：

💬 **对话功能**
• 直接发送文字消息与我对话
• 支持多轮连续对话
• 记住对话上下文

🔧 **菜单功能**  
• 🤖 AI助手：快速开始对话
• 🔄 清除历史：清空聊天记录
• ℹ️ 使用帮助：查看此帮助信息

⚡ **使用技巧**
• 可以问我任何问题
• 支持中英文对话
• 回复会在5秒内送达

有问题随时问我哦！ 😊"""
        
        elif event_key == 'CONTACT_SERVICE':
            response_text = "📞 联系客服\n\n如需人工客服帮助，请：\n• 发送「人工客服」关键词\n• 或添加客服微信：your-service-wechat\n• 或发送邮件至：service@yourcompany.com\n\n我们将尽快为您提供帮助！"
        
        elif event_key == 'ABOUT_US':
            response_text = """⭐ 关于我们

🚀 **项目简介**
Dify2WeChat是一个开源的微信AI接入方案，让AI助手轻松融入微信生态。

🛠️ **技术特点**
• 基于Dify AI平台
• 支持微信公众号和企业微信
• 高性能异步处理
• 完善的会话管理

🌟 **开源地址**
GitHub: dify2wechat

💪 让AI更好地服务每一个人！"""
        
        else:
            # 未知菜单事件
            response_text = f"🤔 收到菜单点击事件：{event_key}\n\n请直接发送消息与我对话，或使用菜单中的其他功能。"
        
        return self.create_text_response(from_user, to_user, response_text)
    
    async def async_complete_response(self, message: Dict[str, Any], user_id: str):
        """异步完成完整回复（等待超时后继续处理）"""
        try:
            logger.info(f"🔄 异步完整回复开始，用户: {user_id}")
            
            content = message.get('Content', '').strip()
            
            # 获取会话ID
            conversation_id = await session_manager.get_conversation_id(user_id)
            
            # 使用更长的超时时间进行完整处理
            original_timeout = dify_client.timeout
            dify_client.timeout = 30  # 异步处理时使用30秒超时
            
            logger.info(f"📡 异步调用Dify API获取完整回复...")
            # 清除之前的部分回复缓存，重新开始
            if user_id in dify_client.partial_responses:
                del dify_client.partial_responses[user_id]
            
            result = await dify_client.chat_completion_streaming(
                message=content,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # 恢复原始超时设置
            dify_client.timeout = original_timeout
            
            # 保存会话ID
            if result.get('conversation_id'):
                await session_manager.set_conversation_id(
                    user_id, 
                    result['conversation_id']
                )
            
            # 获取完整回复内容
            full_reply = result.get('answer', '抱歉，完整回复获取失败。')
            
            if len(full_reply) > 20:  # 确保回复有意义
                # 格式化完整回复
                reply_content = f"📋 详细回复：\n\n{full_reply}"
                
                # 限制消息长度
                max_length = config.message.max_length
                if len(reply_content) > max_length:
                    reply_content = reply_content[:max_length] + "...\n\n💡 回复内容较长，已截断显示"
                
                # 尝试通过客服消息发送
                logger.info(f"📤 尝试通过客服消息发送完整回复，长度: {len(full_reply)}")
                success = await self.send_customer_service_message(user_id, reply_content)
                
                if success:
                    logger.info(f"✅ 完整回复通过客服消息发送成功，用户: {user_id}")
                else:
                    logger.warning(f"⚠️ 客服消息发送失败，将完整回复保存到缓存")
                    # 保存到缓存，用户下次发消息时自动推送
                    await self.cache_complete_response(user_id, reply_content)
            else:
                logger.warning(f"⚠️ 异步获取的回复内容太短，跳过发送")
                
        except Exception as e:
            logger.error(f"💥 异步完整回复异常: {e}")
            # 发送错误提示（如果客服消息可用）或缓存错误信息
            error_msg = "抱歉，在生成详细回复时遇到了问题。您可以重新提问或换个问题试试。"
            
            success = await self.send_customer_service_message(user_id, error_msg)
            if not success:
                await self.cache_complete_response(user_id, error_msg)
                
        finally:
            # 清理任务记录
            if user_id in self.async_tasks:
                del self.async_tasks[user_id]
                logger.info(f"🧹 清理异步任务记录，用户: {user_id}")
    
    async def cache_complete_response(self, user_id: str, response: str):
        """缓存完整回复，供下次用户交互时使用"""
        try:
            cache_key = f"pending_response:{user_id}"
            # 使用会话管理器的Redis缓存
            if hasattr(session_manager, 'redis_client') and session_manager.redis_client:
                # 存储到Redis，有效期10分钟
                import json
                cache_data = {
                    'response': response,
                    'timestamp': time.time()
                }
                session_manager.redis_client.setex(cache_key, 600, json.dumps(cache_data))
                logger.info(f"💾 完整回复已缓存，用户: {user_id}")
            else:
                # 存储到内存
                if not hasattr(self, 'pending_responses'):
                    self.pending_responses = {}
                self.pending_responses[user_id] = {
                    'response': response,
                    'timestamp': time.time()
                }
                logger.info(f"💾 完整回复已存储到内存缓存，用户: {user_id}")
        except Exception as e:
            logger.error(f"缓存完整回复失败: {e}")
    
    async def get_cached_response(self, user_id: str) -> str:
        """获取缓存的完整回复"""
        try:
            cache_key = f"pending_response:{user_id}"
            cached_response = ""
            
            # 从Redis获取
            if hasattr(session_manager, 'redis_client') and session_manager.redis_client:
                import json
                cache_data = session_manager.redis_client.get(cache_key)
                if cache_data:
                    data = json.loads(cache_data)
                    cached_response = data.get('response', '')
                    # 获取后删除缓存
                    session_manager.redis_client.delete(cache_key)
            else:
                # 从内存获取
                if hasattr(self, 'pending_responses') and user_id in self.pending_responses:
                    cached_response = self.pending_responses[user_id].get('response', '')
                    # 获取后删除缓存
                    del self.pending_responses[user_id]
            
            if cached_response:
                logger.info(f"📥 获取到缓存的完整回复，用户: {user_id}")
                return cached_response
                
        except Exception as e:
            logger.error(f"获取缓存回复失败: {e}")
        
        return ""
    
    async def handle_message(self, message: Dict[str, Any]) -> str:
        """处理微信消息"""
        try:
            msg_type = message.get('MsgType', '')
            from_user = message.get('FromUserName', '')
            to_user = message.get('ToUserName', '')
            
            logger.info(f"处理消息类型: {msg_type}, 来自: {from_user}")
            
            # 处理事件消息
            if msg_type == 'event':
                event_type = message.get('Event', '')
                logger.info(f"收到事件: {event_type}")
                
                if event_type == 'subscribe':
                    # 关注事件
                    welcome_msg = "🎉 欢迎关注！我是基于Dify的AI助手！\n\n💬 你可以：\n• 直接发送消息与我对话\n• 点击下方菜单快速开始\n• 询问任何问题，我都会尽力帮助你！"
                    # 异步创建菜单（新用户关注时确保菜单存在）
                    asyncio.create_task(self._ensure_menu_exists())
                    return self.create_text_response(from_user, to_user, welcome_msg)
                elif event_type == 'unsubscribe':
                    # 取消关注事件（用户看不到回复，但记录日志）
                    logger.info(f"用户取消关注: {from_user}")
                    return ""
                elif event_type == 'CLICK':
                    # 菜单点击事件
                    return await self.handle_menu_click(message, from_user, to_user)
                else:
                    # 其他事件，返回提示信息
                    return self.create_text_response(
                        from_user, to_user, 
                        "感谢您的操作！请发送文本消息与我对话。"
                    )
            
            # 处理文本消息
            elif msg_type == 'text':
                content = message.get('Content', '').strip()
                if not content:
                    return self.create_text_response(
                        from_user, to_user,
                        "请发送文本消息与我对话。"
                    )
                
                logger.info(f"收到文本消息: {content}")
                
                # 检查是否有缓存的完整回复
                cached_response = await self.get_cached_response(from_user)
                if cached_response:
                    logger.info(f"💾 找到缓存的完整回复，优先返回")
                    return self.create_text_response(
                        from_user, to_user, 
                        f"📨 之前为您准备的完整回复：\n\n{cached_response}"
                    )
                
                # 继续处理文本消息，不返回
            
            # 处理其他类型消息（图片、语音等）
            else:
                return self.create_text_response(
                    from_user, to_user, 
                    "抱歉，我目前只能处理文本消息。请发送文字与我对话！"
                )
            
            # 如果到这里，说明是text消息且有内容，准备调用AI
            
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
            
            # 检查是否是部分回复（超时情况）
            if result.get('partial', False):
                logger.warning(f"📋 Dify返回部分回复，需要异步处理")
                # 抛出超时异常，让上层处理异步任务
                raise asyncio.TimeoutError("Dify API超时，返回部分内容")
            
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
            
        except asyncio.TimeoutError:
            # 重新抛出超时异常，让上层处理
            raise
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
                    from fastapi import Response
                    return Response(content=echostr, media_type="text/plain")
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
                
                # 微信要求5秒内响应，采用智能分层回复策略
                try:
                    content_length = len(message.get('Content', ''))
                    timeout_duration = 4.5  # 4.5秒超时，为异步处理留出时间
                    
                    logger.info(f"消息长度: {content_length}, 超时设置: {timeout_duration}秒")
                    
                    from_user = message.get('FromUserName', '')
                    to_user = message.get('ToUserName', '')
                    
                    # 智能分层回复策略
                    import asyncio
                    from .dify_client import dify_client
                    
                    # 等待4.5秒看能否获得完整回复
                    response = await asyncio.wait_for(
                        self.handle_message(message), 
                        timeout=timeout_duration
                    )
                    
                    # 如果在4.5秒内完成，直接返回，不需要异步处理
                    logger.info(f"✅ 4.5秒内获得完整回复，直接返回")
                    
                except asyncio.TimeoutError:
                    logger.warning("🔔 4.5秒内未能完成，切换到等待提示模式")
                    
                    # 不显示部分回复内容，直接提供等待提示
                    reply_content = "🤔 这个问题需要一些时间来思考，我正在为您准备详细的回复，请耐心等待..."
                    logger.info(f"回复超时，提示用户等待")
                    
                    # 启动异步完整处理任务
                    if from_user not in self.async_tasks:
                        logger.info(f"🚀 启动异步完整处理任务，用户: {from_user}")
                        self.async_tasks[from_user] = asyncio.create_task(
                            self.async_complete_response(message, from_user)
                        )
                    else:
                        logger.info(f"⚠️ 用户 {from_user} 已有异步任务在运行")
                    
                    response = self.create_text_response(from_user, to_user, reply_content)
                    
                except Exception as e:
                    logger.error(f"💥 消息处理异常: {e}")
                    # 发生异常时也提供友好回复
                    from_user = message.get('FromUserName', '')
                    to_user = message.get('ToUserName', '')
                    response = self.create_text_response(
                        from_user, to_user, 
                        "抱歉，处理您的消息时遇到了问题，请稍后再试。"
                    )
                
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