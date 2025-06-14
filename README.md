# Dify微信生态接入方案

## 项目概述

本项目提供了将Dify AI助手接入微信生态的完整解决方案，支持：
- 微信公众号集成
- 企业微信机器人
- 微信群@bot功能
- 消息转发和智能回复

## 功能特性

- 🤖 智能对话：基于Dify API的AI对话
- 👥 群聊支持：支持微信群@bot触发
- 📊 消息管理：消息记录和会话管理  
- 🔄 多渠道：支持公众号、企业微信等多种接入方式
- ⚡ 高性能：异步处理，支持高并发

## 技术架构

```
用户消息 -> 微信平台 -> Webhook -> 消息处理器 -> Dify API -> 响应返回
```

## 快速开始

### 方案一：本地Dify + 微信公众号（推荐用于开发测试）

如果你已经在本地部署了Dify，推荐使用这种方案：

```bash
# 使用专门的配置脚本
./setup_local_dify.sh

# 或手动配置
cp config.local-dify.yaml config.yaml
# 编辑config.yaml填入你的配置

# 测试Dify连接
python test_local_dify.py

# 启动服务
./start.sh
```

### 方案二：云端Dify + 企业微信

```bash
# 克隆项目
git clone <项目地址>
cd dify2wechat

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp config.example.yaml config.yaml
```

### 2. 配置说明

编辑 `config.yaml` 文件：

```yaml
# Dify配置
dify:
  api_base: "https://api.dify.ai/v1"
  api_key: "your-dify-api-key"
  
# 微信公众号配置
wechat_official:
  app_id: "your-app-id" 
  app_secret: "your-app-secret"
  token: "your-token"
  
# 企业微信配置
work_wechat:
  corp_id: "your-corp-id"
  corp_secret: "your-corp-secret"
```

### 3. 启动服务

```bash
# 快速启动（推荐）
./start.sh

# 或手动启动
python main.py
```

## 微信群@bot使用方法

### 企业微信群聊（推荐）

1. **添加机器人到群聊**：
   - 在企业微信群聊中，点击右上角菜单
   - 选择"群机器人" → "添加机器人"
   - 选择你创建的Dify应用

2. **在群聊中使用**：
   ```
   @bot 你好，请介绍一下你自己
   @bot 帮我写一份工作总结
   @bot 解释一下什么是人工智能
   ```

### 微信公众号

1. **关注公众号**后直接发送消息
2. **群聊分享**：通过小程序或链接分享到群

## 架构说明

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   微信用户      │───▶│   微信平台       │───▶│   Dify2WeChat   │
│   (@bot 消息)   │    │   (Webhook)      │    │   (消息处理)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   AI回复结果    │◀───│   Dify API       │◀────────────┘
│   (智能回复)    │    │   (AI处理)       │    
└─────────────────┘    └──────────────────┘    
```

## 部署方案

支持多种部署方式：
- Docker容器部署
- 云服务器部署
- Serverless部署

## 开发指南

详见各模块的开发文档。 