#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地Dify连接脚本
"""

import httpx
import json
import sys
import asyncio
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_dify_connection():
    """测试Dify连接"""
    
    print("🧪 测试本地Dify连接")
    print("=" * 30)
    
    # 从配置文件读取设置
    try:
        import yaml
        config_file = Path("config.yaml")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            api_base = config_data.get('dify', {}).get('api_base', 'http://localhost:3001/v1')
            api_key = config_data.get('dify', {}).get('api_key', '')
        else:
            print("⚠️  配置文件不存在，使用默认设置")
            api_base = 'http://localhost:3001/v1'
            api_key = input("请输入Dify API密钥: ")
    except ImportError:
        print("⚠️  未安装yaml，使用默认设置")
        api_base = 'http://localhost:3001/v1'
        api_key = input("请输入Dify API密钥: ")
    
    if not api_key or api_key == "your-dify-api-key":
        print("❌ 请先配置正确的Dify API密钥")
        return False
    
    print(f"📡 API地址: {api_base}")
    print(f"🔑 API密钥: {api_key[:20]}...")
    print()
    
    # 测试1: 健康检查
    print("1️⃣  测试健康检查...")
    try:
        health_url = api_base.replace('/v1', '/health')
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(health_url)
            if response.status_code == 200:
                print("✅ 健康检查通过")
            else:
                print(f"⚠️  健康检查返回状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        print("请确认Dify服务是否正常运行")
        return False
    
    # 测试2: API认证
    print("\n2️⃣  测试API认证...")
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{api_base}/parameters",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ API认证成功")
                result = response.json()
                print(f"   用户输入表单: {len(result.get('user_input_form', []))} 个字段")
            elif response.status_code == 401:
                print("❌ API密钥无效")
                return False
            else:
                print(f"⚠️  API认证返回状态码: {response.status_code}")
                print(f"   响应内容: {response.text}")
                
    except Exception as e:
        print(f"❌ API认证测试失败: {e}")
        return False
    
    # 测试3: 发送测试消息
    print("\n3️⃣  测试消息发送...")
    try:
        test_payload = {
            "inputs": {},
            "query": "你好，这是一条测试消息",
            "response_mode": "blocking",
            "user": "test_user_001"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{api_base}/chat-messages",
                headers=headers,
                json=test_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                conversation_id = result.get('conversation_id', '')
                
                print("✅ 消息发送成功")
                print(f"   回复内容: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                print(f"   会话ID: {conversation_id}")
                
                # 测试会话连续性
                if conversation_id:
                    print("\n4️⃣  测试会话连续性...")
                    follow_payload = {
                        "inputs": {},
                        "query": "请重复刚才的消息",
                        "response_mode": "blocking",
                        "user": "test_user_001",
                        "conversation_id": conversation_id
                    }
                    
                    response2 = await client.post(
                        f"{api_base}/chat-messages",
                        headers=headers,
                        json=follow_payload
                    )
                    
                    if response2.status_code == 200:
                        result2 = response2.json()
                        print("✅ 会话连续性正常")
                        print(f"   跟进回复: {result2.get('answer', '')[:100]}...")
                    else:
                        print(f"⚠️  会话连续性测试失败: {response2.status_code}")
                
            elif response.status_code == 400:
                print("❌ 消息格式错误")
                print(f"   错误信息: {response.text}")
                return False
            else:
                print(f"❌ 消息发送失败，状态码: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 消息发送测试失败: {e}")
        return False
    
    print("\n🎉 所有测试通过！Dify连接正常")
    return True

async def main():
    """主函数"""
    try:
        success = await test_dify_connection()
        if success:
            print("\n✅ 你的本地Dify已准备就绪，可以启动微信公众号服务了！")
            print("   运行: ./start.sh 或 python main.py")
        else:
            print("\n❌ 请检查Dify配置并重新测试")
            
    except KeyboardInterrupt:
        print("\n👋 测试已取消")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 