#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号自定义菜单管理模块
"""

import httpx
import json
from typing import Dict, List, Any
from loguru import logger
from wechatpy import WeChatClient

from .config import config

class MenuManager:
    """微信公众号菜单管理器"""
    
    def __init__(self):
        self.app_id = config.wechat_official.app_id
        self.app_secret = config.wechat_official.app_secret
        self.wechat_client = None
        
        if self.app_id and self.app_secret:
            try:
                self.wechat_client = WeChatClient(self.app_id, self.app_secret)
                logger.info("菜单管理器初始化成功")
            except Exception as e:
                logger.error(f"菜单管理器初始化失败: {e}")
    
    async def create_menu(self, menu_data: Dict[str, Any] = None) -> bool:
        """创建自定义菜单"""
        if not self.wechat_client:
            logger.error("微信客户端未初始化")
            return False
        
        # 默认菜单配置
        if menu_data is None:
            menu_data = {
                "button": [
                    {
                        "type": "click",
                        "name": "🤖 AI助手", 
                        "key": "AI_CHAT"
                    },
                    {
                        "name": "📋 功能菜单",
                        "sub_button": [
                            {
                                "type": "click",
                                "name": "💬 开始对话",
                                "key": "START_CHAT"
                            },
                            {
                                "type": "click", 
                                "name": "🔄 清除历史",
                                "key": "CLEAR_HISTORY"
                            },
                            {
                                "type": "click",
                                "name": "ℹ️ 使用帮助", 
                                "key": "HELP_INFO"
                            }
                        ]
                    },
                    {
                        "name": "🔗 更多服务",
                        "sub_button": [
                            {
                                "type": "view",
                                "name": "📖 使用指南",
                                "url": "https://github.com/your-repo/dify2wechat"
                            },
                            {
                                "type": "click",
                                "name": "📞 联系客服",
                                "key": "CONTACT_SERVICE"
                            },
                            {
                                "type": "click",
                                "name": "⭐ 关于我们", 
                                "key": "ABOUT_US"
                            }
                        ]
                    }
                ]
            }
        
        try:
            # 获取access_token
            access_token = self.wechat_client.access_token
            logger.info(f"获取access_token成功: {access_token[:20]}...")
            
            # 调用菜单创建API
            url = f"https://api.weixin.qq.com/cgi-bin/menu/create?access_token={access_token}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=menu_data)
                result = response.json()
                
                logger.info(f"菜单创建API响应: {result}")
                
                if result.get('errcode') == 0:
                    logger.info("✅ 自定义菜单创建成功")
                    return True
                else:
                    logger.error(f"❌ 菜单创建失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"💥 菜单创建异常: {e}")
            return False
    
    async def delete_menu(self) -> bool:
        """删除自定义菜单"""
        if not self.wechat_client:
            logger.error("微信客户端未初始化")
            return False
        
        try:
            access_token = self.wechat_client.access_token
            url = f"https://api.weixin.qq.com/cgi-bin/menu/delete?access_token={access_token}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                result = response.json()
                
                if result.get('errcode') == 0:
                    logger.info("✅ 自定义菜单删除成功")
                    return True
                else:
                    logger.error(f"❌ 菜单删除失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"💥 菜单删除异常: {e}")
            return False
    
    async def get_menu(self) -> Dict[str, Any]:
        """获取当前菜单配置"""
        if not self.wechat_client:
            logger.error("微信客户端未初始化")
            return {}
        
        try:
            access_token = self.wechat_client.access_token
            url = f"https://api.weixin.qq.com/cgi-bin/menu/get?access_token={access_token}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                result = response.json()
                
                if result.get('errcode') == 0 or 'menu' in result:
                    logger.info("✅ 获取菜单配置成功")
                    return result
                else:
                    logger.error(f"❌ 获取菜单失败: {result}")
                    return {}
                    
        except Exception as e:
            logger.error(f"💥 获取菜单异常: {e}")
            return {}

# 全局菜单管理器实例
menu_manager = MenuManager() 