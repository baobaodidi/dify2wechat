#!/bin/bash

# 本地Dify + 微信公众号快速配置脚本

set -e

echo "🚀 本地Dify微信公众号配置脚本"
echo "================================="

# 检查本地Dify是否运行
echo "📡 检查本地Dify服务状态..."

if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "✅ 本地Dify API服务正常运行"
elif curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "⚠️  检测到Dify前端，但API可能在其他端口"
    echo "请确认Dify API的实际地址（通常是3001端口）"
else
    echo "❌ 未检测到本地Dify服务"
    echo "请确保Dify已正确启动，通常使用:"
    echo "   docker-compose up -d"
    exit 1
fi

# 复制配置文件
echo "📋 配置文件设置..."
if [ ! -f "config.yaml" ]; then
    cp config.local-dify.yaml config.yaml
    echo "✅ 已复制本地Dify配置模板"
else
    echo "⚠️  config.yaml已存在，如需重新配置请手动删除"
fi

# 提示用户配置
echo ""
echo "📝 请完成以下配置步骤："
echo ""
echo "1️⃣  获取Dify API密钥："
echo "   访问: http://localhost:3000"
echo "   进入应用 → 设置 → API访问"
echo "   复制API密钥（格式: app-xxxxxxxxxxxxxx）"
echo ""

echo "2️⃣  配置微信公众号："
echo "   访问: https://mp.weixin.qq.com/"
echo "   获取 AppID、AppSecret 和自定义Token"
echo ""

echo "3️⃣  编辑配置文件："
echo "   nano config.yaml  # 或使用你喜欢的编辑器"
echo "   填入实际的API密钥和微信配置"
echo ""

# 提示内网穿透
echo "4️⃣  设置内网穿透（开发环境必需）："
echo ""
echo "   方案一 - 使用ngrok:"
if command -v ngrok &> /dev/null; then
    echo "   ✅ ngrok已安装"
    echo "   运行: ngrok http 8000"
else
    echo "   安装ngrok: brew install ngrok  # macOS"
    echo "   运行: ngrok http 8000"
fi
echo ""

echo "   方案二 - 使用其他工具:"
echo "   - frp (需要公网服务器)"
echo "   - 花生壳"
echo "   - cloudflare tunnel"
echo ""

# 检查依赖
echo "5️⃣  安装Python依赖："
if [ ! -d "venv" ]; then
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
else
    echo "   ✅ 虚拟环境已存在"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
fi
echo ""

echo "6️⃣  启动服务："
echo "   ./start.sh"
echo "   或直接运行: python main.py"
echo ""

echo "7️⃣  配置微信服务器："
echo "   在微信公众平台设置:"
echo "   URL: https://你的ngrok地址/wechat/official"
echo "   Token: 配置文件中的token"
echo ""

echo "🎯 完成以上步骤后，就可以通过微信公众号与本地Dify对话了！"
echo ""
echo "📚 详细说明请查看: docs/wechat_official_setup.md"

# 提供配置文件编辑选项
echo ""
read -p "是否现在编辑配置文件? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v nano &> /dev/null; then
        nano config.yaml
    elif command -v vim &> /dev/null; then
        vim config.yaml
    else
        echo "请手动编辑 config.yaml 文件"
    fi
fi 