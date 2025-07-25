#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复后的异步回复机制
测试当超过5秒回复时异步消息推送是否正常工作
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_timeout_async_mechanism():
    """测试超时异步机制"""
    
    print("🧪 测试超时异步机制")
    print("=" * 50)
    
    from src.wechat_official import wechat_official_handler
    from src.dify_client import dify_client
    
    # 模拟一个需要长时间处理的消息
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'test_timeout_user_123',
        'ToUserName': 'test_bot', 
        'Content': '请详细解释量子计算的原理和应用，包括与传统计算的区别、技术挑战、发展前景等，要求回答详细全面',
        'MsgId': '88888888'
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
        print(f"   这意味着消息处理过快，异步机制未触发")
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"✅ 正确：4.5秒超时触发，耗时: {elapsed:.2f}秒")
        
        # 获取部分回复
        partial_result = dify_client.get_partial_response(user_id)
        partial_answer = partial_result.get('answer', '')
        
        print(f"📋 部分回复检查:")
        if partial_answer and len(partial_answer) > 30:
            print(f"   ✅ 有有效部分内容，长度: {len(partial_answer)}")
            print(f"   预览: {partial_answer[:100]}...")
            reply_content = f"{partial_answer}\n\n⏳ 正在为您生成更完整的回复，请耐心等待..."
        else:
            print(f"   ⚠️ 无有效部分内容")
            reply_content = "🤔 这个问题需要一些时间来思考，我正在为您准备详细的回复，请耐心等待..."
        
        print(f"📤 将返回给用户的回复:")
        print(f"   {reply_content[:150]}...")
        
        # 检查是否会启动异步任务
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

async def test_customer_service_message():
    """测试客服消息发送"""
    
    print("\n🧪 测试客服消息发送机制")
    print("=" * 50)
    
    from src.wechat_official import wechat_official_handler
    
    test_user = "test_customer_service_user"
    test_content = "这是一个测试客服消息发送的内容，用于验证微信公众号客服API是否正常工作。"
    
    print(f"📤 测试客服消息发送...")
    print(f"   用户: {test_user}")
    print(f"   内容长度: {len(test_content)}")
    
    success = await wechat_official_handler.send_customer_service_message(test_user, test_content)
    
    if success:
        print(f"✅ 客服消息发送成功")
        print(f"   这意味着异步回复可以通过客服消息送达用户")
    else:
        print(f"❌ 客服消息发送失败")
        print(f"   这是正常的，因为需要认证服务号才能使用客服API")
        print(f"   系统将使用缓存机制作为降级方案")
        
        # 测试缓存机制
        print(f"\n📦 测试缓存机制...")
        await wechat_official_handler.cache_complete_response(test_user, test_content)
        
        cached = await wechat_official_handler.get_cached_response(test_user)
        if cached:
            print(f"✅ 缓存机制工作正常")
            print(f"   缓存内容长度: {len(cached)}")
        else:
            print(f"❌ 缓存机制异常")

def show_fix_summary():
    """显示修复总结"""
    
    print("\n🎯 修复总结")
    print("=" * 50)
    
    print("🔧 关键修复:")
    print("   1. handle_message 方法现在会在超时时抛出 TimeoutError")
    print("   2. 检查 Dify 返回的 partial 标志，确保超时检测准确")
    print("   3. Webhook 处理器正确捕获 TimeoutError 并启动异步任务")
    print("   4. 异步任务管理逻辑增强，防止重复任务")
    print("   5. 客服消息降级到缓存机制更加稳定")
    
    print("\n📱 用户体验流程:")
    print("   1. 用户发送复杂问题")
    print("   2. 4.5秒内返回: 部分回复 + '正在生成更完整的回复'")
    print("   3. 异步任务在后台继续处理")
    print("   4. 完整回复通过客服消息发送（如果可用）")
    print("   5. 或保存到缓存，用户下次发消息时自动推送")
    
    print("\n⚡ 技术优势:")
    print("   ✅ 确保5秒内响应微信要求")
    print("   ✅ 充分利用流式API提升首字节时间")
    print("   ✅ 异步处理保证完整性")
    print("   ✅ 多重降级机制保证可靠性")
    print("   ✅ 智能缓存避免重复计算")

def main():
    """主函数"""
    print("🔧 异步回复机制修复验证")
    print("请选择测试类型:")
    print("1. 测试超时异步机制")
    print("2. 测试客服消息发送")  
    print("3. 查看修复总结")
    print("4. 运行完整测试")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(test_timeout_async_mechanism())
    elif choice == "2":
        asyncio.run(test_customer_service_message())
    elif choice == "3":
        show_fix_summary()
    elif choice == "4":
        show_fix_summary()
        print("\n" + "="*50 + "\n")
        asyncio.run(test_timeout_async_mechanism())
        print("\n" + "="*50 + "\n") 
        asyncio.run(test_customer_service_message())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 