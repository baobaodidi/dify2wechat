 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步消息回复功能
"""

import asyncio
import time
from src.wechat_official import wechat_official_handler

async def test_async_reply():
    """测试异步消息回复功能"""
    print("🧪 开始测试异步消息回复功能...")
    
    # 模拟一个微信消息
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'test_user_123',
        'ToUserName': 'gh_581b6239f6e9',
        'Content': '请详细介绍一下人工智能的发展历史和未来趋势，包括机器学习、深度学习、自然语言处理等各个领域的发展情况',
        'MsgId': '12345678901234567890',
        'CreateTime': str(int(time.time()))
    }
    
    print(f"📝 测试消息: {test_message['Content'][:50]}...")
    print(f"👤 用户ID: {test_message['FromUserName']}")
    
    # 测试客服消息发送功能
    print("\n🔧 测试客服消息发送功能...")
    
    # 检查微信客户端是否初始化
    if wechat_official_handler.wechat_client:
        print("✅ 微信客户端已初始化")
        
        # 测试发送客服消息
        test_content = "这是一条测试客服消息"
        success = await wechat_official_handler.send_customer_service_message(
            test_message['FromUserName'], 
            test_content
        )
        
        if success:
            print("✅ 客服消息发送测试成功")
        else:
            print("❌ 客服消息发送测试失败")
    else:
        print("❌ 微信客户端未初始化，无法测试客服消息")
    
    # 测试异步处理功能
    print("\n🚀 测试异步消息处理功能...")
    
    # 启动异步处理任务
    task = asyncio.create_task(
        wechat_official_handler.async_process_message(
            test_message, 
            test_message['FromUserName']
        )
    )
    
    print("⏳ 异步任务已启动，等待处理完成...")
    
    try:
        # 等待任务完成，最多等待60秒
        await asyncio.wait_for(task, timeout=60.0)
        print("✅ 异步消息处理完成")
    except asyncio.TimeoutError:
        print("⏰ 异步消息处理超时")
    except Exception as e:
        print(f"❌ 异步消息处理异常: {e}")
    
    print("\n📊 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_async_reply())