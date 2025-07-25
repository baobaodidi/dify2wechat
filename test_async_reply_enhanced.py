#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版异步回复功能测试脚本
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.wechat_official import wechat_official_handler
from src.dify_client import dify_client

async def test_async_reply_mechanism():
    """测试异步回复机制"""
    
    print("🔄 异步回复机制测试")
    print("=" * 50)
    
    # 模拟微信消息
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'test_user_async',
        'ToUserName': 'test_bot',
        'Content': '请帮我写一篇关于人工智能发展的详细文章，包括历史、现状和未来展望',
        'MsgId': '12345678'
    }
    
    print("📝 模拟测试消息:")
    print(f"   用户: {test_message['FromUserName']}")
    print(f"   内容: {test_message['Content']}")
    print()
    
    # 测试1: 正常超时处理流程
    print("🧪 测试1: 模拟4.5秒超时情况")
    print("-" * 30)
    
    try:
        # 模拟超时处理
        start_time = time.time()
        
        # 这里我们不实际调用handle_message，而是模拟超时场景
        user_id = test_message['FromUserName']
        
        # 模拟部分回复数据
        dify_client.partial_responses[user_id] = {
            'answer': '人工智能的发展可以追溯到20世纪50年代...',
            'first_chunk_time': 2.0,
            'conversation_id': 'test_conv_123',
            'message_id': 'test_msg_456'
        }
        
        # 模拟异步任务启动
        if user_id not in wechat_official_handler.async_tasks:
            print(f"🚀 启动异步任务...")
            wechat_official_handler.async_tasks[user_id] = asyncio.create_task(
                wechat_official_handler.async_complete_response(test_message, user_id)
            )
            
        # 检查异步任务状态
        async_task = wechat_official_handler.async_tasks.get(user_id)
        if async_task:
            print(f"✅ 异步任务已启动")
            print(f"   任务状态: {'运行中' if not async_task.done() else '已完成'}")
            
            # 等待任务完成（模拟）
            print(f"⏳ 等待异步任务完成...")
            try:
                await asyncio.wait_for(async_task, timeout=5.0)
                print(f"✅ 异步任务完成")
            except asyncio.TimeoutError:
                print(f"⚠️  异步任务超时（这是正常的测试行为）")
                async_task.cancel()
        
        elapsed = time.time() - start_time
        print(f"⏱️  总用时: {elapsed:.2f}秒")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
    
    print()
    
    # 测试2: 检查异步任务管理
    print("🧪 测试2: 异步任务管理")
    print("-" * 30)
    
    # 显示当前活跃任务
    active_tasks = len(wechat_official_handler.async_tasks)
    print(f"📊 当前活跃异步任务数: {active_tasks}")
    
    for user, task in wechat_official_handler.async_tasks.items():
        status = "运行中" if not task.done() else "已完成"
        print(f"   用户: {user}, 状态: {status}")
    
    print()
    
    # 测试3: 部分回复智能判断
    print("🧪 测试3: 部分回复智能判断")
    print("-" * 30)
    
    test_scenarios = [
        {
            'name': '有部分回复，差异显著',
            'partial': '人工智能的发展...',
            'full': '人工智能的发展可以追溯到20世纪50年代，经历了符号主义、连接主义等多个阶段，如今深度学习技术正在推动AI进入新的时代...',
            'expected': '发送完整回复'
        },
        {
            'name': '无部分回复',
            'partial': '',
            'full': '这是一个完整的AI回复内容',
            'expected': '发送延迟回复'
        },
        {
            'name': '内容差异不大',
            'partial': '人工智能的发展历史',
            'full': '人工智能的发展历史很长',
            'expected': '跳过发送'
        }
    ]
    
    for scenario in test_scenarios:
        print(f"   场景: {scenario['name']}")
        partial_len = len(scenario['partial'])
        full_len = len(scenario['full'])
        
        if scenario['partial'] and full_len > partial_len * 1.5:
            result = "发送完整回复"
        elif scenario['partial'] and scenario['full'] != scenario['partial']:
            result = "发送补充回复"
        elif not scenario['partial']:
            result = "发送延迟回复"
        else:
            result = "跳过发送"
            
        print(f"   预期: {scenario['expected']}, 实际: {result}")
        print(f"   ✅" if result == scenario['expected'] else "❌")
        print()

def demonstrate_async_flow():
    """演示异步回复流程"""
    
    print("🎯 异步回复流程演示")
    print("=" * 50)
    
    print("📱 用户发送消息:")
    print("   '请帮我写一篇详细的AI文章'")
    print()
    
    print("⏰ 时间线:")
    print("   0.0s - 收到用户消息")
    print("   0.1s - 开始调用Dify API")
    print("   2.0s - 收到首字节，开始流式回复")
    print("   4.5s - 触发超时截断")
    print("   4.5s - 返回部分内容 + '完整回复将稍后发送...'")
    print("   4.6s - 启动异步任务继续处理")
    print("   15.0s - 异步任务完成，发送完整回复")
    print()
    
    print("💬 用户看到的消息流:")
    print("   [4.5s后] 机器人: '人工智能的发展可以追溯到...")
    print("            💭 我正在继续思考，完整回复将稍后发送...'")
    print()
    print("   [15s后]  机器人: '✨ 完整回复：")
    print("            人工智能的发展可以追溯到20世纪50年代...")
    print("            [完整的详细文章内容]'")
    print()
    
    print("🎉 优势:")
    print("   ✅ 用户不会看到'服务不可用'")
    print("   ✅ 4.5秒内必有回复，体验流畅")
    print("   ✅ 异步获取完整内容，信息完整")
    print("   ✅ 智能去重，避免重复发送")
    print("   ✅ 错误处理完善，系统稳定")

def main():
    """主函数"""
    print("🤖 异步回复功能测试")
    print("请选择测试类型:")
    print("1. 运行完整测试")
    print("2. 查看流程演示")
    print("3. 运行所有测试")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_async_reply_mechanism())
    elif choice == "2":
        demonstrate_async_flow()
    elif choice == "3":
        demonstrate_async_flow()
        print("\n" + "="*50 + "\n")
        asyncio.run(test_async_reply_mechanism())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 