#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试微信超时处理的调试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def debug_no_reply_issue():
    """调试没有收到回复的问题"""
    
    print("🔍 调试：为什么没有收到回复内容")
    print("=" * 50)
    
    from src.wechat_official import wechat_official_handler
    from src.dify_client import dify_client
    
    # 检查1: 服务状态
    print("1️⃣  检查服务组件状态")
    print("─" * 30)
    
    # 检查微信处理器
    print(f"✅ 微信处理器: {'已初始化' if wechat_official_handler else '未初始化'}")
    print(f"✅ Dify客户端: {'已初始化' if dify_client else '未初始化'}")
    
    # 检查配置
    from src.config import config
    print(f"✅ 微信配置: {'启用' if config.wechat_official.enabled else '禁用'}")
    print(f"✅ Dify API: {config.dify.api_base}")
    
    # 检查2: 实际消息处理
    print(f"\n2️⃣  测试实际消息处理")
    print("─" * 30)
    
    test_message = {
        'MsgType': 'text',
        'FromUserName': 'debug_user_001',
        'ToUserName': 'gh_debug_bot',
        'Content': '为什么我没有收到回复？',
        'MsgId': '999999999'
    }
    
    print(f"📱 测试消息: {test_message['Content']}")
    
    try:
        response = await wechat_official_handler.handle_message(test_message)
        if response:
            print(f"✅ 消息处理成功")
            # 简单解析XML
            if '<Content><![CDATA[' in response:
                start = response.find('<Content><![CDATA[') + 18
                end = response.find(']]></Content>')
                if end > start:
                    reply_text = response[start:end]
                    print(f"📤 回复内容: {reply_text}")
                else:
                    print(f"⚠️  XML格式异常")
            else:
                print(f"⚠️  非标准回复格式")
                print(f"   原始回复: {response[:100]}...")
        else:
            print(f"❌ 没有收到回复")
    except Exception as e:
        print(f"❌ 处理异常: {e}")
    
    # 检查3: 可能的问题原因
    print(f"\n3️⃣  可能的问题原因分析")
    print("─" * 30)
    
    print("🔍 检查点:")
    print("   □ 微信消息是否正确到达服务器？")
    print("   □ 服务器是否正确解析微信XML？")
    print("   □ Dify API是否正常响应？")
    print("   □ 回复是否正确发送给微信？")
    print("   □ 微信是否正确显示回复？")
    
    print(f"\n💡 排查建议:")
    print("   1. 检查微信后台日志")
    print("   2. 检查natapp连接状态")
    print("   3. 检查服务器日志")
    print("   4. 测试简单消息（如'你好'）")
    print("   5. 检查用户是否已关注公众号")

def check_natapp_connection():
    """检查natapp连接状态"""
    
    print("\n🌐 检查natapp连接状态")
    print("=" * 50)
    
    import requests
    
    try:
        # 测试外网访问
        response = requests.get("https://kamirui.natapp4.cc/health", timeout=10)
        if response.status_code == 200:
            print("✅ natapp隧道连接正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ natapp响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ natapp连接失败: {e}")
        print("💡 请检查:")
        print("   1. natapp是否正在运行")
        print("   2. 隧道配置是否正确")
        print("   3. 本地服务是否在8000端口运行")

async def test_webhook_endpoint():
    """测试webhook端点"""
    
    print("\n🔗 测试webhook端点")
    print("=" * 50)
    
    import requests
    
    try:
        # 测试GET请求（微信验证）
        test_params = {
            'signature': 'test_signature',
            'timestamp': '1703123456',
            'nonce': 'test_nonce',
            'echostr': 'test_echo'
        }
        
        response = requests.get(
            "https://kamirui.natapp4.cc/wechat/official", 
            params=test_params,
            timeout=10
        )
        
        print(f"GET请求测试: {response.status_code}")
        if response.status_code == 403:
            print("✅ 正常 - 签名验证失败（预期行为）")
        else:
            print(f"   响应: {response.text[:100]}...")
            
    except Exception as e:
        print(f"❌ webhook测试失败: {e}")

def main():
    """主函数"""
    print("🔧 没有收到回复的问题调试")
    print("请选择调试选项:")
    print("1. 运行完整调试")
    print("2. 检查natapp连接")
    print("3. 测试webhook端点")
    print("4. 运行所有检查")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(debug_no_reply_issue())
    elif choice == "2":
        check_natapp_connection()
    elif choice == "3":
        asyncio.run(test_webhook_endpoint())
    elif choice == "4":
        asyncio.run(debug_no_reply_issue())
        check_natapp_connection()
        asyncio.run(test_webhook_endpoint())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 