#!/bin/bash

# Dify微信生态接入快速启动脚本

set -e

echo "🚀 Dify微信生态接入服务启动脚本"
echo "================================="

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "📋 复制配置文件模板..."
    cp config.example.yaml config.yaml
    echo "⚠️  请编辑 config.yaml 文件配置你的参数："
    echo "   - Dify API密钥"
    echo "   - 微信公众号配置"
    echo "   - 企业微信配置"
    echo ""
    echo "配置完成后，重新运行此脚本。"
    exit 1
fi

# 检查是否有Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 使用Docker Compose启动服务..."
    
    # 检查环境变量
    if [ -z "$DIFY_API_KEY" ]; then
        echo "⚠️  请设置环境变量 DIFY_API_KEY"
        echo "   export DIFY_API_KEY=\"your-dify-api-key\""
        exit 1
    fi
    
    # 启动服务
    docker-compose up -d
    
    echo "✅ 服务启动成功！"
    echo "📡 访问地址："
    echo "   - API文档: http://localhost:8000/docs"
    echo "   - 健康检查: http://localhost:8000/health"
    echo "   - 微信公众号: http://localhost:8000/wechat/official"
    echo "   - 企业微信: http://localhost:8000/wechat/work"
    
    echo ""
    echo "📋 查看日志："
    echo "   docker-compose logs -f"
    
else
    echo "🐍 使用Python直接启动..."
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        echo "❌ 未找到Python3，请先安装Python"
        exit 1
    fi
    
    # 安装依赖
    if [ ! -d "venv" ]; then
        echo "📦 创建虚拟环境..."
        python3 -m venv venv
    fi
    
    echo "📦 激活虚拟环境并安装依赖..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    # 启动服务
    echo "🚀 启动服务..."
    # 绕过代理访问本地服务
    NO_PROXY=localhost python main.py
fi 