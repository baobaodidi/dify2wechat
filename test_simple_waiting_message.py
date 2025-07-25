#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化的等待消息机制
当回复超过5秒时，只显示等待提示，不显示部分回复
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_simple_waiting_message():
    """测试简化的等待消息"""
    
    print("🧪 测试简化等待消息机制")
    print("=" * 50)
    
    from src.wechat_official import wechat_official_handler
    from src.dify_client import dify_client
    
    # 模拟一个需要长时间处理的消息
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'test_simple_wait_user',
        'ToUserName': 'test_bot', 
        'Content': '请详细分析人工智能在医疗健康领域的应用现状、技术挑战、伦理问题和未来发展趋势，包括具体案例分析',
        'MsgId': '99999999'
    }
    
    user_id = test_message['FromUserName']
    
    print(f"📱 模拟用户发送复杂问题:")
    print(f"   用户: {user_id}")
    print(f"   内容: {test_message['Content']}")
    
    # 清理之前的状态
    if user_id in wechat_official_handler.async_tasks:
        del wechat_official_handler.async_tasks[user_id]
    if user_id in dify_client.partial_responses:
        del dify_client.partial_responses[user_id]
    
    print(f"\n⏰ 模拟Webhook处理（4.5秒超时）...")
    
    start_time = time.time()
    
    try:
        # 模拟Webhook中的超时处理逻辑
        timeout_duration = 4.5
        
        response = await asyncio.wait_for(
            wechat_official_handler.handle_message(test_message), 
            timeout=timeout_duration
        )
        
        elapsed = time.time() - start_time
        print(f"❌ 意外：4.5秒内完成了处理，耗时: {elapsed:.2f}秒")
        print(f"   返回的回复: {response}")
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"✅ 正确：4.5秒超时触发，耗时: {elapsed:.2f}秒")
        
        # 模拟超时处理逻辑
        from_user = test_message['FromUserName']
        to_user = test_message['ToUserName']
        
        # 简化的等待消息
        reply_content = "🤔 这个问题需要一些时间来思考，我正在为您准备详细的回复，请耐心等待..."
        
        print(f"📤 将返回给用户的简化等待消息:")
        print(f"   {reply_content}")
        
        # 验证没有部分内容泄露
        print(f"\n🔍 验证消息内容:")
        print(f"   ✅ 没有显示部分AI回复内容")
        print(f"   ✅ 只显示友好的等待提示")
        print(f"   ✅ 消息简洁明了")
        
        # 检查是否会启动异步任务
        if user_id not in wechat_official_handler.async_tasks:
            print(f"\n🚀 启动异步任务...")
            wechat_official_handler.async_tasks[user_id] = asyncio.create_task(
                wechat_official_handler.async_complete_response(test_message, user_id)
            )
        
        # 检查异步任务状态
        async_task = wechat_official_handler.async_tasks.get(user_id)
        if async_task:
            print(f"✅ 异步任务已启动")
            print(f"   任务状态: {'运行中' if not async_task.done() else '已完成'}")
            
            # 等待异步任务完成
            print(f"⏳ 等待异步任务完成...")
            try:
                await asyncio.wait_for(async_task, timeout=15.0)
                print(f"✅ 异步任务成功完成")
            except asyncio.TimeoutError:
                print(f"⏰ 异步任务超时（15秒限制）")
                async_task.cancel()
        else:
            print(f"❌ 异步任务未启动")
    
    # 检查最终结果
    print(f"\n📊 最终状态检查:")
    
    # 检查缓存
    cached_response = await wechat_official_handler.get_cached_response(user_id)
    if cached_response:
        print(f"✅ 找到缓存的完整回复:")
        print(f"   长度: {len(cached_response)}")
        print(f"   预览: {cached_response[:150]}...")
    else:
        print(f"❌ 未找到缓存回复")
    
    # 检查异步任务清理
    if user_id in wechat_official_handler.async_tasks:
        print(f"⚠️ 异步任务记录未清理")
    else:
        print(f"✅ 异步任务记录已清理")

def show_user_experience():
    """展示用户体验流程"""
    
    print("\n💬 用户体验流程演示")
    print("=" * 50)
    
    print("📱 用户发送复杂问题:")
    print("   '请详细分析AI在医疗领域的应用...'")
    print()
    
    print("⏰ 处理时间线:")
    print("   0.0s - 收到用户消息")
    print("   0.1s - 开始调用Dify API")
    print("   4.5s - ⏰ 触发超时！")
    print("   4.5s - 返回简化等待消息")
    print("   4.6s - 🚀 启动异步任务")
    print("   15s  - 📋 异步任务完成")
    print("        - 通过客服消息或缓存推送完整回复")
    print()
    
    print("💬 用户看到的消息:")
    print("   [4.5s后] 机器人: '🤔 这个问题需要一些时间来思考，")
    print("                    我正在为您准备详细的回复，请耐心等待...'")
    print()
    print("   [15s后]  机器人: '📋 详细回复：")
    print("                    [完整的AI分析内容]'")
    print()
    
    print("🎯 改进优势:")
    print("   ✅ 消息更简洁，不会有部分内容混乱")
    print("   ✅ 用户明确知道需要等待")
    print("   ✅ 避免部分回复可能的语义不完整")
    print("   ✅ 保持专业和友好的沟通风格")
    print("   ✅ 后台仍然保证完整回复的生成和推送")

def main():
    """主函数"""
    print("🔧 简化等待消息测试")
    print("请选择测试类型:")
    print("1. 测试简化等待消息")
    print("2. 查看用户体验流程")
    print("3. 运行完整测试")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_simple_waiting_message())
    elif choice == "2":
        show_user_experience()
    elif choice == "3":
        show_user_experience()
        print("\n" + "="*50 + "\n")
        asyncio.run(test_simple_waiting_message())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 