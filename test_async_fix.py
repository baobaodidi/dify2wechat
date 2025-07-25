#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的异步回复机制
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_timeout_scenario():
    """测试超时场景的异步回复"""
    
    print("🧪 测试超时场景的异步回复机制")
    print("=" * 50)
    
    from src.wechat_official import wechat_official_handler
    from src.dify_client import dify_client
    
    # 模拟一个复杂问题的消息
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'test_timeout_user',
        'ToUserName': 'test_bot', 
        'Content': '请详细分析AI的发展历程、技术原理、应用场景和未来展望',
        'MsgId': '99999999'
    }
    
    user_id = test_message['FromUserName']
    
    print(f"📱 模拟用户发送复杂问题:")
    print(f"   用户: {user_id}")
    print(f"   内容: {test_message['Content']}")
    
    # 模拟部分回复（假设AI已经开始回复但未完成）
    print(f"\n⏱️  模拟4.5秒后的状态...")
    dify_client.partial_responses[user_id] = {
        'answer': 'AI的发展历程可以分为几个重要阶段...',
        'first_chunk_time': 2.0,
        'conversation_id': 'test_conv_timeout',
        'message_id': 'test_msg_timeout'
    }
    
    # 启动异步任务
    print(f"🚀 启动异步完整回复任务...")
    if user_id not in wechat_official_handler.async_tasks:
        wechat_official_handler.async_tasks[user_id] = asyncio.create_task(
            wechat_official_handler.async_complete_response(test_message, user_id)
        )
        print(f"✅ 异步任务已启动")
    
    # 检查任务状态
    async_task = wechat_official_handler.async_tasks.get(user_id)
    if async_task:
        print(f"📊 任务状态: {'运行中' if not async_task.done() else '已完成'}")
        
        # 等待任务完成
        print(f"⏳ 等待异步任务完成...")
        try:
            await asyncio.wait_for(async_task, timeout=10.0)
            print(f"✅ 异步任务完成")
        except asyncio.TimeoutError:
            print(f"⏰ 异步任务超时（测试限制）")
            async_task.cancel()
    
    # 检查结果
    print(f"\n📋 检查处理结果:")
    
    # 检查缓存
    cached_response = await wechat_official_handler.get_cached_response(user_id)
    if cached_response:
        print(f"✅ 找到缓存的完整回复:")
        print(f"   长度: {len(cached_response)}")
        print(f"   预览: {cached_response[:100]}...")
    else:
        print(f"❌ 未找到缓存回复")
    
    # 清理
    if user_id in wechat_official_handler.async_tasks:
        del wechat_official_handler.async_tasks[user_id]
    if user_id in dify_client.partial_responses:
        del dify_client.partial_responses[user_id]

async def test_customer_service_fallback():
    """测试客服消息降级机制"""
    
    print("\n🧪 测试客服消息降级机制")
    print("=" * 50)
    
    from src.wechat_official import wechat_official_handler
    
    test_user = "test_fallback_user"
    test_content = "这是一个测试完整回复的内容，用于验证客服消息和缓存机制的工作情况。"
    
    print(f"📤 测试客服消息发送...")
    print(f"   用户: {test_user}")
    print(f"   内容: {test_content[:50]}...")
    
    # 尝试发送客服消息
    success = await wechat_official_handler.send_customer_service_message(test_user, test_content)
    
    if success:
        print(f"✅ 客服消息发送成功")
    else:
        print(f"❌ 客服消息发送失败，手动缓存测试内容")
        
        # 手动缓存测试（模拟异步任务中的缓存逻辑）
        await wechat_official_handler.cache_complete_response(test_user, test_content)
        
        # 检查是否缓存成功
        cached = await wechat_official_handler.get_cached_response(test_user)
        if cached:
            print(f"✅ 回复已成功缓存")
            print(f"   长度: {len(cached)}")
        else:
            print(f"❌ 缓存机制异常")

def demonstrate_fixed_flow():
    """演示修复后的流程"""
    
    print("\n🎯 修复后的异步回复流程")
    print("=" * 50)
    
    print("📱 用户发送复杂问题:")
    print('   "请详细分析AI的发展历程、技术原理、应用场景和未来展望"')
    print()
    
    print("⏰ 处理时间线:")
    print("   0.0s - 收到用户消息")
    print("   0.1s - 开始调用Dify API")
    print("   2.0s - 收到首字节，开始流式回复")
    print("   4.5s - ⏰ 触发超时！")
    print("   4.5s - 返回: 'AI的发展历程可以分为...'")
    print("        + '⏳ 正在为您生成更完整的回复，请耐心等待...'")
    print("   4.6s - 🚀 启动异步任务")
    print("   15s  - 📋 异步任务完成")
    print("        - 尝试客服消息发送")
    print("        - 如失败则缓存回复")
    print()
    
    print("💬 用户体验:")
    print("   [4.5s] 立即收到: 部分回复 + 等待提示")
    print("   [15s]  收到完整回复（客服消息）或")
    print("   [下次] 发送任何消息时收到缓存的完整回复")
    print()
    
    print("🔧 关键修复:")
    print("   ✅ 异步任务只在超时时启动")
    print("   ✅ 清除部分回复缓存，获取完整内容")
    print("   ✅ 客服消息失败时自动缓存")
    print("   ✅ 用户下次交互时自动推送缓存回复")

def main():
    """主函数"""
    print("🔧 异步回复机制修复测试")
    print("请选择测试类型:")
    print("1. 测试超时异步回复")
    print("2. 测试客服消息降级")
    print("3. 查看修复流程说明")
    print("4. 运行所有测试")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(test_timeout_scenario())
    elif choice == "2":
        asyncio.run(test_customer_service_fallback())
    elif choice == "3":
        demonstrate_fixed_flow()
    elif choice == "4":
        demonstrate_fixed_flow()
        print("\n" + "="*50 + "\n")
        asyncio.run(test_timeout_scenario())
        print("\n" + "="*50 + "\n")
        asyncio.run(test_customer_service_fallback())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 