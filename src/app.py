#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用程序
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import asyncio
from typing import Dict, Any

from .config import config
from .wechat_official import wechat_official_handler
from .work_wechat import work_wechat_handler
from .session_manager import session_manager

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="Dify微信生态接入",
        description="将Dify AI助手接入微信生态的服务",
        version="1.0.0",
        docs_url="/docs" if config.server.debug else None,
        redoc_url="/redoc" if config.server.debug else None
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "Dify微信生态接入服务",
            "version": "1.0.0",
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    @app.api_route("/wechat/official", methods=["GET", "POST"])
    async def wechat_official_webhook(request: Request):
        """微信公众号Webhook"""
        if not config.wechat_official.enabled:
            raise HTTPException(status_code=404, detail="微信公众号未启用")
        
        try:
            response = await wechat_official_handler.handle_webhook(request)
            # 直接返回Response对象，不需要再包装
            return response
        except Exception as e:
            logger.error(f"微信公众号Webhook处理失败: {e}")
            raise HTTPException(status_code=500, detail="内部服务器错误")
    
    @app.api_route("/wechat/work", methods=["GET", "POST"])
    async def work_wechat_webhook(request: Request):
        """企业微信Webhook"""
        if not config.work_wechat.enabled:
            raise HTTPException(status_code=404, detail="企业微信未启用")
        
        try:
            response = await work_wechat_handler.handle_webhook(request)
            return PlainTextResponse(response)
        except Exception as e:
            logger.error(f"企业微信Webhook处理失败: {e}")
            raise HTTPException(status_code=500, detail="内部服务器错误")
    
    @app.post("/api/clear_session")
    async def clear_user_session(data: Dict[str, str]):
        """清除用户会话"""
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="用户ID不能为空")
        
        try:
            await session_manager.clear_conversation(user_id)
            return {"message": f"用户 {user_id} 的会话已清除"}
        except Exception as e:
            logger.error(f"清除用户会话失败: {e}")
            raise HTTPException(status_code=500, detail="清除会话失败")
    
    @app.get("/api/stats")
    async def get_stats():
        """获取统计信息"""
        try:
            return {
                "message": "统计信息",
                "wechat_official_enabled": config.wechat_official.enabled,
                "work_wechat_enabled": config.work_wechat.enabled,
                "group_trigger": config.message.group_trigger
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise HTTPException(status_code=500, detail="获取统计信息失败")
    
    @app.post("/api/test_dify")
    async def test_dify_api(data: Dict[str, str]):
        """测试Dify API响应时间"""
        from .dify_client import dify_client
        import time
        
        message = data.get("message", "你好")
        user_id = data.get("user_id", "test_user")
        
        try:
            start_time = time.time()
            result = await dify_client.chat_completion_streaming(message, user_id)
            end_time = time.time()
            
            return {
                "message": message,
                "user_id": user_id,
                "response_time": f"{end_time - start_time:.2f}s",
                "result": result
            }
        except Exception as e:
            logger.error(f"测试Dify API失败: {e}")
            raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")
    
    logger.info("FastAPI应用创建成功")
    return app