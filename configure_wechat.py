#!/usr/bin/env python3
"""
微信公众号配置助手
帮助用户快速配置微信公众号信息
"""

import yaml
import os
from pathlib import Path

def load_config():
    """加载当前配置"""
    config_file = Path("config.yaml")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def save_config(config):
    """保存配置到文件"""
    with open("config.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

def main():
    print("🔧 微信公众号配置助手")
    print("=" * 50)
    
    # 加载当前配置
    config = load_config()
    
    print("\n📋 请提供你的微信公众号信息：")
    print("（可以从微信公众平台 -> 开发 -> 基本配置 中获取）")
    
    # 获取用户输入
    app_id = input(f"\n🔑 AppID (当前: {config.get('wechat_official', {}).get('app_id', '未设置')}): ").strip()
    if not app_id:
        app_id = config.get('wechat_official', {}).get('app_id', '')
    
    app_secret = input(f"🔑 AppSecret (当前: {'已设置' if config.get('wechat_official', {}).get('app_secret') else '未设置'}): ").strip()
    if not app_secret:
        app_secret = config.get('wechat_official', {}).get('app_secret', '')
    
    token = input(f"🔑 Token (当前: {config.get('wechat_official', {}).get('token', 'wechat_dify_token_2024')}): ").strip()
    if not token:
        token = config.get('wechat_official', {}).get('token', 'wechat_dify_token_2024')
    
    encoding_aeskey = input(f"🔐 EncodingAESKey (可选，当前: {'已设置' if config.get('wechat_official', {}).get('encoding_aeskey') else '未设置'}): ").strip()
    if not encoding_aeskey:
        encoding_aeskey = config.get('wechat_official', {}).get('encoding_aeskey', '')
    
    # 更新配置
    if 'wechat_official' not in config:
        config['wechat_official'] = {}
    
    config['wechat_official'].update({
        'enabled': True,
        'app_id': app_id,
        'app_secret': app_secret,
        'token': token,
        'encoding_aeskey': encoding_aeskey
    })
    
    # 保存配置
    save_config(config)
    
    print("\n✅ 配置已保存到 config.yaml")
    print("\n📋 下一步操作：")
    print("1. 在微信公众平台设置服务器配置：")
    print(f"   - 服务器地址(URL): http://你的域名:8000/wechat/official")
    print(f"   - 令牌(Token): {token}")
    print("   - 消息加解密方式: 明文模式")
    
    print("\n2. 如果是本地开发，需要内网穿透：")
    print("   brew install ngrok")
    print("   ngrok http 8000")
    
    print("\n3. 重启服务使配置生效：")
    print("   pkill -f 'python main.py'")
    print("   source venv/bin/activate && nohup python main.py > server.log 2>&1 &")
    
    print("\n📖 详细配置指南请查看: docs/wechat_official_setup.md")

if __name__ == "__main__":
    main() 