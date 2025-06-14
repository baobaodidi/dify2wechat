#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify微信生态接入主程序
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.app import create_app

def setup_logging():
    """设置日志"""
    log_level = config.logging.level
    log_file = config.logging.file
    
    # 创建日志目录
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days"
    )

def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        logger.info("🚀 启动Dify微信生态接入服务")
        
        # 检查配置
        if config.dify.api_key == "your-dify-api-key":
            logger.error("❌ 请先配置Dify API密钥")
            return
            
        # 创建FastAPI应用
        app = create_app()
        
        # 启动服务
        logger.info(f"📡 服务启动在 http://{config.server.host}:{config.server.port}")
        uvicorn.run(
            app,
            host=config.server.host,
            port=config.server.port,
            log_level=config.logging.level.lower()
        )
        
    except KeyboardInterrupt:
        logger.info("👋 服务已停止")
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise

if __name__ == "__main__":
    main() 