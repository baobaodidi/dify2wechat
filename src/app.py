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
from .menu_manager import menu_manager

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
    
    @app.get("/natapp-test")
    async def natapp_test():
        """natapp连通性测试端点"""
        import datetime
        return {
            "message": "🎉 natapp隧道连接成功！",
            "service": "Dify微信生态接入",
            "timestamp": datetime.datetime.now().isoformat(),
            "local_port": 8000,
            "endpoints": {
                "health": "/health",
                "wechat_webhook": "/wechat/official",
                "api_docs": "/docs"
            },
            "next_steps": "请在微信公众平台配置Webhook URL"
        }

    @app.get("/test")
    async def test_endpoint():
        """测试端点，用于验证natapp连通性"""
        return {
            "message": "natapp连接测试成功！",
            "timestamp": asyncio.get_event_loop().time(),
            "status": "ok"
        }

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
    
    @app.post("/api/menu/create")
    async def create_wechat_menu(data: Dict[str, Any] = None):
        """创建微信公众号自定义菜单"""
        try:
            menu_data = data.get("menu_data") if data else None
            success = await menu_manager.create_menu(menu_data)
            
            if success:
                return {"message": "✅ 自定义菜单创建成功", "success": True}
            else:
                return {"message": "❌ 自定义菜单创建失败", "success": False}
                
        except Exception as e:
            logger.error(f"创建菜单API异常: {e}")
            raise HTTPException(status_code=500, detail=f"创建菜单失败: {str(e)}")
    
    @app.delete("/api/menu/delete")
    async def delete_wechat_menu():
        """删除微信公众号自定义菜单"""
        try:
            success = await menu_manager.delete_menu()
            
            if success:
                return {"message": "✅ 自定义菜单删除成功", "success": True}
            else:
                return {"message": "❌ 自定义菜单删除失败", "success": False}
                
        except Exception as e:
            logger.error(f"删除菜单API异常: {e}")
            raise HTTPException(status_code=500, detail=f"删除菜单失败: {str(e)}")
    
    @app.get("/api/menu/get")
    async def get_wechat_menu():
        """获取当前微信公众号菜单配置"""
        try:
            menu_config = await menu_manager.get_menu()
            return {
                "message": "获取菜单配置成功",
                "menu_config": menu_config
            }
                
        except Exception as e:
            logger.error(f"获取菜单API异常: {e}")
            raise HTTPException(status_code=500, detail=f"获取菜单失败: {str(e)}")
    
    @app.get("/api/async/status")
    async def get_async_tasks_status():
        """获取当前异步任务状态"""
        try:
            active_tasks = {}
            for user_id, task in wechat_official_handler.async_tasks.items():
                active_tasks[user_id] = {
                    "status": "running" if not task.done() else "completed",
                    "done": task.done(),
                    "cancelled": task.cancelled()
                }
            
            return {
                "message": "获取异步任务状态成功",
                "active_tasks_count": len(active_tasks),
                "active_tasks": active_tasks
            }
                
        except Exception as e:
            logger.error(f"获取异步任务状态失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
    
    @app.post("/api/async/force_complete")
    async def force_complete_async_task(data: Dict[str, str]):
        """强制完成指定用户的异步任务"""
        user_id = data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="用户ID不能为空")
        
        try:
            if user_id in wechat_official_handler.async_tasks:
                task = wechat_official_handler.async_tasks[user_id]
                if not task.done():
                    # 等待任务完成（最多等待10秒）
                    try:
                        await asyncio.wait_for(task, timeout=10.0)
                        return {"message": f"用户 {user_id} 的异步任务已完成"}
                    except asyncio.TimeoutError:
                        task.cancel()
                        return {"message": f"用户 {user_id} 的异步任务超时已取消"}
                else:
                    return {"message": f"用户 {user_id} 的异步任务已经完成"}
            else:
                return {"message": f"用户 {user_id} 没有进行中的异步任务"}
                
        except Exception as e:
            logger.error(f"强制完成异步任务失败: {e}")
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    
    logger.info("FastAPI应用创建成功")
    return app