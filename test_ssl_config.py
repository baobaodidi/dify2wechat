#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SSL配置的脚本
"""

import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.dify_client import DifyClient
from src.config import config

async def test_ssl_config():
    """测试SSL配置"""
    print("=== SSL配置测试 ===")
    print(f"API Base: {config.dify.api_base}")
    print(f"SSL验证: {config.dify.verify_ssl}")
    
    client = DifyClient()
    print(f"客户端SSL验证设置: {client.verify_ssl}")
    
    # 测试一个简单的请求（这里只是测试连接，不需要真实的API key）
    try:
        result = await client.chat_completion(
            message="测试消息",
            user_id="test_user"
        )
        print("请求结果:", result)
    except Exception as e:
        print(f"请求异常: {e}")
        print("如果是SSL错误，请检查verify_ssl配置是否正确设置为false")

if __name__ == "__main__":
    asyncio.run(test_ssl_config())
