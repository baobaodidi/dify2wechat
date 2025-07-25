#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试缓存回复机制
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.wechat_official import wechat_official_handler

async def test_cache_mechanism():
    """测试缓存回复机制"""
    
    print("💾 测试缓存回复机制")
    print("=" * 50)
    
    test_user = "test_cache_user"
    test_response = "这是一个完整的AI回复内容，包含了详细的分析和建议..."
    
    # 测试1: 缓存回复
    print("🧪 测试1: 缓存回复")
    print("-" * 30)
    
    await wechat_official_handler.cache_complete_response(test_user, test_response)
    print(f"✅ 回复已缓存")
    
    # 测试2: 获取缓存
    print("\n🧪 测试2: 获取缓存回复")
    print("-" * 30)
    
    cached = await wechat_official_handler.get_cached_response(test_user)
    if cached:
        print(f"✅ 成功获取缓存回复:")
        print(f"   {cached[:50]}...")
        print(f"   长度: {len(cached)}")
    else:
        print("❌ 未找到缓存回复")
    
    # 测试3: 重复获取（应该为空）
    print("\n🧪 测试3: 重复获取缓存（应该为空）")
    print("-" * 30)
    
    cached_again = await wechat_official_handler.get_cached_response(test_user)
    if cached_again:
        print("❌ 缓存没有被正确删除")
    else:
        print("✅ 缓存已正确删除（一次性获取）")

async def test_full_workflow():
    """测试完整的异步回复工作流程"""
    
    print("\n🔄 测试完整异步回复工作流程")
    print("=" * 50)
    
    # 模拟用户消息
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'workflow_test_user',
        'ToUserName': 'test_bot',
        'Content': '请详细解释什么是机器学习',
        'MsgId': '87654321'
    }
    
    user_id = test_message['FromUserName']
    
    print(f"📱 模拟用户发送消息:")
    print(f"   用户: {user_id}")
    print(f"   内容: {test_message['Content']}")
    
    # 步骤1: 模拟部分回复（超时前的回复）
    print(f"\n⏰ 步骤1: 模拟4.5秒超时，返回部分回复")
    from src.dify_client import dify_client
    dify_client.partial_responses[user_id] = {
        'answer': '机器学习是人工智能的一个重要分支...',
        'first_chunk_time': 2.0,
        'conversation_id': 'test_conv_workflow',
        'message_id': 'test_msg_workflow'
    }
    
    # 步骤2: 启动异步任务
    print(f"\n🚀 步骤2: 启动异步完整回复任务")
    if user_id not in wechat_official_handler.async_tasks:
        # 这里我们模拟异步处理，但不实际调用Dify API
        print("   异步任务已启动（模拟）")
        
        # 模拟完整回复
        full_response = """机器学习是人工智能的一个重要分支，它使计算机系统能够通过经验自动改进性能。

主要特点：
1. 自动学习：无需明确编程即可学习
2. 数据驱动：基于大量数据进行训练
3. 模式识别：从数据中发现规律和模式

常见算法：
- 监督学习：线性回归、决策树、神经网络
- 无监督学习：聚类、降维
- 强化学习：Q学习、策略梯度

应用领域：
- 图像识别和计算机视觉
- 自然语言处理
- 推荐系统
- 自动驾驶
- 医疗诊断

未来发展：
随着算力提升和数据增长，机器学习将在更多领域发挥重要作用..."""
        
        # 直接缓存完整回复（模拟客服消息发送失败的情况）
        await wechat_official_handler.cache_complete_response(user_id, full_response)
        print("   ✅ 完整回复已缓存（模拟客服消息不可用）")
    
    # 步骤3: 模拟用户再次发送消息
    print(f"\n📱 步骤3: 用户再次发送消息")
    new_message = {
        'MsgType': 'text',
        'FromUserName': user_id,
        'ToUserName': 'test_bot',
        'Content': '继续',
        'MsgId': '87654322'
    }
    
    # 检查缓存回复
    cached_response = await wechat_official_handler.get_cached_response(user_id)
    if cached_response:
        print(f"   ✅ 检测到缓存回复，将优先返回")
        print(f"   回复长度: {len(cached_response)}")
        print(f"   回复预览: {cached_response[:100]}...")
        
        # 模拟创建回复消息
        response_xml = wechat_official_handler.create_text_response(
            new_message['FromUserName'],
            new_message['ToUserName'],
            f"📨 之前为您准备的完整回复：\n\n{cached_response}"
        )
        print(f"   ✅ 回复消息已生成")
    else:
        print(f"   ❌ 未找到缓存回复")

def demonstrate_improved_flow():
    """演示改进后的异步回复流程"""
    
    print("🎯 改进版异步回复流程")
    print("=" * 50)
    
    print("📱 用户体验流程:")
    print("1. 用户发送: '请详细解释机器学习'")
    print("2. [4.5s] Bot回复: '机器学习是AI的重要分支...'")
    print("   '💭 我正在准备更详细的回复，请稍候...'")
    print("3. [后台] 异步任务生成完整回复")
    print("4. [客服消息失败] 回复被保存到缓存")
    print("5. 用户发送任何新消息（如: '继续', '好的', '还有吗'）")
    print("6. Bot立即回复: '📨 之前为您准备的完整回复：[详细内容]'")
    print()
    
    print("🎉 优势对比:")
    print("❌ 之前: 客服消息失败 → 用户收不到完整回复")
    print("✅ 现在: 客服消息失败 → 缓存回复 → 下次交互时自动推送")
    print()
    
    print("💡 适用场景:")
    print("• 未认证的订阅号（无客服消息权限）")
    print("• 用户未关注但通过其他方式交互")
    print("• 客服消息配额用完")
    print("• 网络异常导致客服消息发送失败")

def main():
    """主函数"""
    print("🧪 缓存回复机制测试")
    print("请选择测试类型:")
    print("1. 测试基础缓存功能")
    print("2. 测试完整工作流程")
    print("3. 查看改进流程说明")
    print("4. 运行所有测试")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(test_cache_mechanism())
    elif choice == "2":
        asyncio.run(test_full_workflow())
    elif choice == "3":
        demonstrate_improved_flow()
    elif choice == "4":
        demonstrate_improved_flow()
        print("\n" + "="*50 + "\n")
        asyncio.run(test_cache_mechanism())
        print("\n" + "="*50 + "\n")
        asyncio.run(test_full_workflow())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 