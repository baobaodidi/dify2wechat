#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号菜单管理测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.menu_manager import menu_manager

async def test_menu_management():
    """测试菜单管理功能"""
    
    print("🔧 微信公众号菜单管理测试")
    print("=" * 40)
    
    # 1. 获取当前菜单
    print("\n1️⃣  获取当前菜单配置...")
    current_menu = await menu_manager.get_menu()
    if current_menu:
        print("✅ 当前菜单配置:")
        import json
        print(json.dumps(current_menu, indent=2, ensure_ascii=False))
    else:
        print("❌ 当前没有菜单或获取失败")
    
    # 2. 创建默认菜单
    print("\n2️⃣  创建默认菜单...")
    success = await menu_manager.create_menu()
    if success:
        print("✅ 菜单创建成功！")
        
        # 验证菜单创建结果
        print("\n3️⃣  验证菜单创建结果...")
        new_menu = await menu_manager.get_menu()
        if new_menu and new_menu.get('menu'):
            print("✅ 菜单验证成功，当前菜单:")
            print(json.dumps(new_menu, indent=2, ensure_ascii=False))
        else:
            print("⚠️  菜单创建后验证失败")
    else:
        print("❌ 菜单创建失败")
    
    print("\n🎉 测试完成！")
    print("\n📋 接下来你可以:")
    print("• 关注你的微信公众号")
    print("• 查看是否出现了自定义菜单")
    print("• 点击菜单测试各种功能")

async def test_custom_menu():
    """测试自定义菜单配置"""
    
    print("\n🎨 测试自定义菜单配置")
    print("=" * 40)
    
    # 自定义菜单结构
    custom_menu = {
        "button": [
            {
                "type": "click",
                "name": "🚀 开始聊天",
                "key": "START_CHAT"
            },
            {
                "name": "🛠️ 功能中心",
                "sub_button": [
                    {
                        "type": "click",
                        "name": "💡 智能问答",
                        "key": "AI_CHAT"
                    },
                    {
                        "type": "click",
                        "name": "🗑️ 清空记录",
                        "key": "CLEAR_HISTORY"
                    },
                    {
                        "type": "view",
                        "name": "📚 使用文档",
                        "url": "https://github.com/dify2wechat"
                    }
                ]
            },
            {
                "type": "click",
                "name": "ℹ️ 帮助信息",
                "key": "HELP_INFO"
            }
        ]
    }
    
    print("📋 自定义菜单配置:")
    import json
    print(json.dumps(custom_menu, indent=2, ensure_ascii=False))
    
    # 创建自定义菜单
    print("\n🎯 创建自定义菜单...")
    success = await menu_manager.create_menu(custom_menu)
    
    if success:
        print("✅ 自定义菜单创建成功！")
    else:
        print("❌ 自定义菜单创建失败")

def main():
    """主函数"""
    print("🤖 选择测试类型:")
    print("1. 测试默认菜单")
    print("2. 测试自定义菜单")
    print("3. 删除当前菜单")
    print("4. 查看当前菜单")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(test_menu_management())
    elif choice == "2":
        asyncio.run(test_custom_menu())
    elif choice == "3":
        async def delete_menu():
            print("🗑️  删除当前菜单...")
            success = await menu_manager.delete_menu()
            if success:
                print("✅ 菜单删除成功！")
            else:
                print("❌ 菜单删除失败")
        asyncio.run(delete_menu())
    elif choice == "4":
        async def show_menu():
            print("📋 当前菜单配置:")
            menu = await menu_manager.get_menu()
            if menu:
                import json
                print(json.dumps(menu, indent=2, ensure_ascii=False))
            else:
                print("❌ 获取菜单失败或菜单不存在")
        asyncio.run(show_menu())
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 