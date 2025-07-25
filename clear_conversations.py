#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理脚本 - 清空和查看会话ID
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.session_manager import session_manager

async def list_all_conversations():
    """查看所有用户的会话"""
    try:
        print("👥 查看所有用户会话...")
        print("=" * 60)
        
        conversations = []
        
        if session_manager.redis_client:
            # 从Redis获取所有conversation:*的key
            keys = session_manager.redis_client.keys("conversation:*")
            print(f"📊 在Redis中找到 {len(keys)} 个会话")
            
            for key in keys:
                try:
                    data = session_manager.redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        user_id = key.replace("conversation:", "")
                        conversation_id = session_data.get('conversation_id', '')
                        updated_at = session_data.get('updated_at', 0)
                        
                        # 转换时间戳为可读格式
                        if updated_at:
                            update_time = datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            update_time = "未知"
                        
                        conversations.append({
                            'user_id': user_id,
                            'conversation_id': conversation_id,
                            'updated_at': update_time,
                            'timestamp': updated_at
                        })
                except Exception as e:
                    print(f"⚠️  解析会话数据失败 {key}: {e}")
        else:
            # 从内存获取
            conversation_keys = [k for k in session_manager.memory_store.keys() if k.startswith("conversation:")]
            print(f"📊 在内存中找到 {len(conversation_keys)} 个会话")
            
            for key in conversation_keys:
                try:
                    session_data = session_manager.memory_store[key]
                    user_id = key.replace("conversation:", "")
                    conversation_id = session_data.get('conversation_id', '')
                    updated_at = session_data.get('updated_at', 0)
                    
                    # 转换时间戳为可读格式
                    if updated_at:
                        update_time = datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        update_time = "未知"
                    
                    conversations.append({
                        'user_id': user_id,
                        'conversation_id': conversation_id,
                        'updated_at': update_time,
                        'timestamp': updated_at
                    })
                except Exception as e:
                    print(f"⚠️  解析会话数据失败 {key}: {e}")
        
        if conversations:
            # 按更新时间倒序排列
            conversations.sort(key=lambda x: x['timestamp'], reverse=True)
            
            print("\n📝 会话详情:")
            print("-" * 80)
            print(f"{'序号':<4} {'用户ID':<30} {'会话ID':<30} {'最后更新时间'}")
            print("-" * 80)
            
            for i, conv in enumerate(conversations, 1):
                user_id = conv['user_id'][:28] + ".." if len(conv['user_id']) > 30 else conv['user_id']
                conv_id = conv['conversation_id'][:28] + ".." if len(conv['conversation_id']) > 30 else conv['conversation_id']
                print(f"{i:<4} {user_id:<30} {conv_id:<30} {conv['updated_at']}")
            
            print("-" * 80)
            print(f"总计: {len(conversations)} 个活跃会话")
            
            # 显示完整信息
            print("\n🔍 完整信息:")
            for i, conv in enumerate(conversations, 1):
                print(f"  {i}. 用户ID: {conv['user_id']}")
                print(f"     会话ID: {conv['conversation_id']}")
                print(f"     更新时间: {conv['updated_at']}")
                print()
        else:
            print("📭 没有找到任何会话数据")
        
    except Exception as e:
        print(f"❌ 查看会话时出错: {e}")

async def clear_all_conversations():
    """清空所有会话"""
    try:
        print("🧹 开始清空所有会话...")
        
        if session_manager.redis_client:
            # 如果使用Redis，清空所有conversation:*的key
            keys = session_manager.redis_client.keys("conversation:*")
            if keys:
                session_manager.redis_client.delete(*keys)
                print(f"✅ 已从Redis清空 {len(keys)} 个会话")
            else:
                print("ℹ️  Redis中没有找到会话数据")
        else:
            # 如果使用内存存储，清空内存
            conversation_keys = [k for k in session_manager.memory_store.keys() if k.startswith("conversation:")]
            for key in conversation_keys:
                del session_manager.memory_store[key]
            print(f"✅ 已从内存清空 {len(conversation_keys)} 个会话")
        
        print("🎉 所有会话已清空完成！")
        
    except Exception as e:
        print(f"❌ 清空会话时出错: {e}")

async def clear_specific_user(user_id: str):
    """清空指定用户的会话"""
    try:
        print(f"🧹 清空用户 {user_id} 的会话...")
        
        # 先检查用户是否存在会话
        conversation_id = await session_manager.get_conversation_id(user_id)
        if conversation_id:
            print(f"📋 找到用户会话ID: {conversation_id}")
            await session_manager.clear_conversation(user_id)
            print(f"✅ 用户 {user_id} 的会话已清空")
        else:
            print(f"ℹ️  用户 {user_id} 没有活跃的会话")
            
    except Exception as e:
        print(f"❌ 清空用户会话时出错: {e}")

async def show_user_info(user_id: str):
    """显示指定用户的会话信息"""
    try:
        print(f"🔍 查看用户 {user_id} 的会话信息...")
        print("-" * 40)
        
        conversation_id = await session_manager.get_conversation_id(user_id)
        
        if conversation_id:
            print(f"👤 用户ID: {user_id}")
            print(f"💬 会话ID: {conversation_id}")
            
            # 尝试获取更详细的信息
            key = f"conversation:{user_id}"
            if session_manager.redis_client:
                data = session_manager.redis_client.get(key)
                if data:
                    session_data = json.loads(data)
                    updated_at = session_data.get('updated_at', 0)
                    if updated_at:
                        update_time = datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"🕒 最后更新: {update_time}")
            else:
                session_data = session_manager.memory_store.get(key)
                if session_data:
                    updated_at = session_data.get('updated_at', 0)
                    if updated_at:
                        update_time = datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"🕒 最后更新: {update_time}")
            
            print("✅ 用户有活跃的会话")
        else:
            print(f"👤 用户ID: {user_id}")
            print("📭 该用户没有活跃的会话")
            
    except Exception as e:
        print(f"❌ 查看用户信息时出错: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="会话管理工具")
    parser.add_argument("--list", action="store_true", help="查看所有用户的会话")
    parser.add_argument("--user", help="指定要操作的用户ID")
    parser.add_argument("--clear", action="store_true", help="清空会话")
    parser.add_argument("--all", action="store_true", help="操作所有用户")
    parser.add_argument("--info", action="store_true", help="查看用户信息")
    
    args = parser.parse_args()
    
    if args.list:
        asyncio.run(list_all_conversations())
    elif args.user and args.clear:
        asyncio.run(clear_specific_user(args.user))
    elif args.user and args.info:
        asyncio.run(show_user_info(args.user))
    elif args.all and args.clear:
        asyncio.run(clear_all_conversations())
    else:
        print("🛠️  会话管理工具使用方法:")
        print("-" * 40)
        print("  查看所有会话:     python clear_conversations.py --list")
        print("  查看用户信息:     python clear_conversations.py --user USER_ID --info")
        print("  清空指定用户:     python clear_conversations.py --user USER_ID --clear")
        print("  清空所有会话:     python clear_conversations.py --all --clear")
        print()
        print("💡 示例:")
        print("  python clear_conversations.py --list")
        print("  python clear_conversations.py --user test_user_123 --info")
        print("  python clear_conversations.py --user test_user_123 --clear")
        print("  python clear_conversations.py --all --clear") 