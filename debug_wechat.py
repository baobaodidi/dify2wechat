#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号调试工具
"""

import requests
import time
import hashlib
from urllib.parse import quote

def verify_signature(token, timestamp, nonce):
    """生成微信签名"""
    tmp_list = [token, timestamp, nonce]
    tmp_list.sort()
    tmp_str = ''.join(tmp_list)
    return hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()

def test_wechat_verification():
    """测试微信验证"""
    print("🧪 测试微信公众号验证")
    print("=" * 50)
    
    # 配置参数
    token = "wechat_dify_token_2024"
    timestamp = str(int(time.time()))
    nonce = "test123"
    echostr = "hello_world"
    
    # 生成签名
    signature = verify_signature(token, timestamp, nonce)
    
    # 测试本地服务
    local_url = "http://localhost:8000/wechat/official"
    params = {
        'signature': signature,
        'timestamp': timestamp,
        'nonce': nonce,
        'echostr': echostr
    }
    
    print(f"📍 测试URL: {local_url}")
    print(f"🔑 Token: {token}")
    print(f"⏰ Timestamp: {timestamp}")
    print(f"🎲 Nonce: {nonce}")
    print(f"🔐 Signature: {signature}")
    print(f"📢 EchoStr: {echostr}")
    
    try:
        response = requests.get(local_url, params=params, timeout=10)
        print(f"\n✅ 响应状态: {response.status_code}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200 and response.text == echostr:
            print("🎉 微信验证成功！")
            return True
        else:
            print("❌ 微信验证失败！")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 微信公众号调试工具")
    print("🔗 检查本地服务: http://localhost:8000")
    
    # 检查服务状态
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 本地服务正常运行")
        else:
            print("❌ 本地服务异常")
            return
    except:
        print("❌ 本地服务无法连接")
        return
    
    # 测试验证
    test_wechat_verification()

if __name__ == "__main__":
    main()
