# Dify微信生态接入配置指南

## 概述

本指南将详细介绍如何配置Dify与微信生态的集成，实现微信群@bot功能。

## 前期准备

### 1. Dify平台配置

1. 登录 [Dify云端平台](https://cloud.dify.ai) 或部署自己的Dify实例
2. 创建一个应用（推荐使用聊天助手类型）
3. 获取API密钥：
   - 进入应用设置 → API访问
   - 复制API密钥，格式类似：`app-xxxxxxxxxxxxxx`

### 2. 服务器准备

- 具有公网IP的服务器（腾讯云、阿里云等）
- 域名并配置SSL证书（微信要求HTTPS）
- Docker和Docker Compose环境

## 微信公众号接入

### 1. 注册微信公众号

1. 前往 [微信公众平台](https://mp.weixin.qq.com/)
2. 注册订阅号或服务号（服务号功能更丰富）
3. 完成认证（企业认证推荐）

### 2. 配置开发者设置

1. 登录微信公众平台
2. 进入 **开发** → **基本配置**
3. 获取以下信息：
   - AppID：应用ID
   - AppSecret：应用密钥（需要管理员扫码获取）
   - Token：自定义令牌（建议使用随机字符串）

4. 配置服务器地址：
   ```
   URL: https://你的域名/wechat/official
   Token: 你设置的Token
   EncodingAESKey: 可选，用于消息加密
   ```

### 3. 群聊@bot配置

微信公众号本身不直接支持群聊，但可以通过以下方式实现：

1. **客服接口模式**：用户需要先关注公众号
2. **小程序集成**：通过小程序在群里分享
3. **企业微信**：推荐方案，直接支持群聊

## 企业微信接入

### 1. 注册企业微信

1. 前往 [企业微信官网](https://work.weixin.qq.com/) 注册
2. 完成企业认证
3. 创建应用

### 2. 获取配置信息

1. 进入 **管理工具** → **应用管理**
2. 选择自建应用，获取：
   - AgentId：应用ID
   - Secret：应用密钥
   - CorpId：企业ID（在我的企业中查看）

### 3. 配置接收消息

1. 在应用设置中，配置**接收消息**：
   ```
   URL: https://你的域名/wechat/work
   Token: 自定义令牌
   EncodingAESKey: 消息加密密钥
   ```

2. 设置可见范围：选择需要使用机器人的用户或部门

### 4. 群聊@bot配置

1. 将应用添加到群聊：
   - 在群聊中点击右上角 → 群机器人 → 添加机器人
   - 选择你创建的应用

2. 群聊中@bot：
   - 发送消息时使用 `@bot 你的问题`
   - 配置文件中设置触发词：`group_trigger: "@bot"`

## 配置文件设置

复制 `config.example.yaml` 为 `config.yaml` 并编辑：

```yaml
# Dify配置
dify:
  api_base: "https://api.dify.ai/v1"  # 或你的私有部署地址
  api_key: "app-xxxxxxxxxxxxxx"       # 你的Dify API密钥

# 微信公众号配置
wechat_official:
  enabled: true
  app_id: "wxxxxxxxxxxxxxxx"          # 微信公众号AppID
  app_secret: "xxxxxxxxxxxxxxxx"      # 微信公众号AppSecret
  token: "your_token_here"            # 自定义Token

# 企业微信配置  
work_wechat:
  enabled: true
  corp_id: "wwxxxxxxxxxxxxxx"         # 企业ID
  corp_secret: "xxxxxxxxxxxxxxxx"     # 应用Secret
  agent_id: "1000001"                 # 应用AgentId

# 消息处理配置
message:
  enable_group: true                  # 启用群聊功能
  group_trigger: "@bot"               # 群聊触发关键词
  max_length: 2000                    # 最大消息长度
```

## 部署方式

### 方式一：Docker Compose部署（推荐）

1. 克隆项目：
```bash
git clone <项目地址>
cd dify2wechat
```

2. 配置环境变量：
```bash
# 设置Dify API密钥
export DIFY_API_KEY="app-xxxxxxxxxxxxxx"
```

3. 编辑配置文件：
```bash
cp config.example.yaml config.yaml
# 编辑config.yaml，填入你的配置信息
```

4. 启动服务：
```bash
docker-compose up -d
```

### 方式二：直接运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置文件：
```bash
cp config.example.yaml config.yaml
# 编辑配置
```

3. 启动服务：
```bash
python main.py
```

## SSL证书配置

微信要求Webhook地址必须使用HTTPS，配置SSL证书：

### 使用Let's Encrypt（免费）

```bash
# 安装certbot
sudo apt install certbot

# 获取证书
sudo certbot certonly --standalone -d 你的域名

# 证书位置
# /etc/letsencrypt/live/你的域名/fullchain.pem
# /etc/letsencrypt/live/你的域名/privkey.pem
```

### Nginx配置示例

```nginx
server {
    listen 443 ssl http2;
    server_name 你的域名;
    
    ssl_certificate /etc/letsencrypt/live/你的域名/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/你的域名/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 测试和验证

### 1. 服务健康检查

访问：`https://你的域名/health`
应该返回：`{"status": "healthy"}`

### 2. 微信服务器验证

在微信公众平台或企业微信管理后台，点击**验证**按钮，确保服务器配置正确。

### 3. 消息测试

- **公众号**：关注后发送消息测试
- **企业微信**：在群聊中@bot发送消息测试

## 常见问题

### 1. 服务器验证失败

- 检查URL是否可访问
- 确认Token配置正确
- 查看服务器日志排查错误

### 2. SSL证书问题

- 确保证书有效且未过期
- 检查证书链是否完整
- 使用在线SSL检测工具验证

### 3. 群聊@bot无响应

- 确认机器人已添加到群聊
- 检查触发关键词配置
- 查看应用可见范围设置

### 4. Dify API调用失败

- 验证API密钥是否正确
- 检查网络连接
- 确认Dify服务状态

## 监控和维护

### 1. 日志查看

```bash
# Docker部署
docker-compose logs -f dify2wechat

# 直接运行
tail -f logs/app.log
```

### 2. 性能监控

- 使用Prometheus + Grafana监控
- 关注API响应时间
- 监控错误率和成功率

### 3. 定期维护

- 更新SSL证书
- 备份配置文件
- 监控服务器资源使用

## 进阶功能

### 1. 多租户支持

可以为不同的企业微信或公众号配置不同的Dify应用。

### 2. 消息队列

对于高并发场景，可以集成消息队列（如Redis、RabbitMQ）进行异步处理。

### 3. 用户权限管理

实现基于用户身份的权限控制和功能限制。

### 4. 智能路由

根据用户问题类型，路由到不同的Dify应用或处理逻辑。

## 技术支持

如有问题，请查阅：
- 项目GitHub Issues
- 微信开发者文档
- Dify官方文档


ollama serve
curl http://localhost:11434/api/tags

cd /opt/homebrew/bin/ && ./natapp

cd /Users/kamirui/Documents/9_AI/Cursor/dify2wechat && source venv/bin/activate && NO_PROXY=localhost python main.py
